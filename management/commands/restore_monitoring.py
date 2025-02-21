from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import json
import gzip
import shutil
import redis
import logging
from datetime import datetime
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Restore monitoring system from backup'

    def add_arguments(self, parser):
        parser.add_argument(
            '--backup-dir',
            help='Specific backup directory to restore from'
        )
        parser.add_argument(
            '--type',
            choices=['full', 'metrics', 'alerts', 'config'],
            default='full',
            help='Type of restore to perform'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force restore without confirmation'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be restored without making changes'
        )

    def handle(self, *args, **options):
        try:
            backup_dir = options['backup_dir']
            restore_type = options['type']
            force = options['force']
            dry_run = options['dry_run']

            # Find latest backup if not specified
            if not backup_dir:
                backup_dir = self.find_latest_backup()
                if not backup_dir:
                    raise CommandError("No backup found")

            self.stdout.write(f"Using backup: {backup_dir}")

            # Verify backup
            if not self.verify_backup(backup_dir):
                raise CommandError("Backup verification failed")

            # Confirm restore
            if not force and not dry_run:
                confirm = input(f"Are you sure you want to restore from {backup_dir}? [y/N] ")
                if confirm.lower() != 'y':
                    self.stdout.write(self.style.WARNING('Restore cancelled'))
                    return

            # Stop monitoring services
            if not dry_run:
                self.stop_services()

            # Perform restore
            if restore_type == 'full' or restore_type == 'metrics':
                self.restore_metrics(backup_dir, dry_run)

            if restore_type == 'full' or restore_type == 'alerts':
                self.restore_alerts(backup_dir, dry_run)

            if restore_type == 'full' or restore_type == 'config':
                self.restore_config(backup_dir, dry_run)

            # Start services
            if not dry_run:
                self.start_services()

            if dry_run:
                self.stdout.write(self.style.SUCCESS('Dry run completed'))
            else:
                self.stdout.write(self.style.SUCCESS('Restore completed successfully'))

        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise CommandError(str(e))

    def find_latest_backup(self) -> Optional[str]:
        """Find the latest backup directory"""
        try:
            backup_root = settings.BACKUP_DIR
            backup_dirs = [
                d for d in os.listdir(backup_root)
                if d.startswith('monitoring_') and os.path.isdir(os.path.join(backup_root, d))
            ]

            if not backup_dirs:
                return None

            latest = max(backup_dirs, key=lambda x: x.split('_')[1])
            return os.path.join(backup_root, latest)

        except Exception as e:
            logger.error(f"Failed to find latest backup: {e}")
            return None

    def verify_backup(self, backup_dir: str) -> bool:
        """Verify backup integrity"""
        try:
            required_files = {
                'metrics': 'metrics.json.gz',
                'alerts': 'alerts.json.gz',
                'config': 'config.json.gz'
            }

            for component, filename in required_files.items():
                filepath = os.path.join(backup_dir, filename)
                if not os.path.exists(filepath):
                    self.stdout.write(
                        self.style.WARNING(f"Missing {component} backup: {filename}")
                    )
                    continue

                # Verify file integrity
                try:
                    with gzip.open(filepath, 'rt') as f:
                        data = json.load(f)
                        if component == 'metrics' and not isinstance(data, dict):
                            raise ValueError("Invalid metrics format")
                        elif component == 'alerts' and not isinstance(data, list):
                            raise ValueError("Invalid alerts format")
                        elif component == 'config' and not isinstance(data, dict):
                            raise ValueError("Invalid config format")
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f"Corrupt {component} backup: {e}")
                    )
                    return False

            return True

        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            return False

    def stop_services(self):
        """Stop monitoring services"""
        self.stdout.write('Stopping monitoring services...')
        os.system('systemctl stop terminusa-monitoring')

    def start_services(self):
        """Start monitoring services"""
        self.stdout.write('Starting monitoring services...')
        os.system('systemctl start terminusa-monitoring')

    def restore_metrics(self, backup_dir: str, dry_run: bool):
        """Restore metrics data"""
        self.stdout.write('Restoring metrics...')

        try:
            metrics_file = os.path.join(backup_dir, 'metrics.json.gz')
            if not os.path.exists(metrics_file):
                self.stdout.write(self.style.WARNING('No metrics backup found'))
                return

            with gzip.open(metrics_file, 'rt') as f:
                metrics_data = json.load(f)

            if dry_run:
                self.stdout.write(f"Would restore {len(metrics_data)} metrics")
                return

            # Clear existing metrics
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0
            )
            redis_client.delete(*redis_client.keys('metrics:*'))

            # Restore metrics
            for key, value in metrics_data.items():
                redis_client.set(key, json.dumps(value))

            self.stdout.write(self.style.SUCCESS('Metrics restored'))

        except Exception as e:
            logger.error(f"Metrics restore failed: {e}")
            raise

    def restore_alerts(self, backup_dir: str, dry_run: bool):
        """Restore alerts"""
        self.stdout.write('Restoring alerts...')

        try:
            alerts_file = os.path.join(backup_dir, 'alerts.json.gz')
            if not os.path.exists(alerts_file):
                self.stdout.write(self.style.WARNING('No alerts backup found'))
                return

            with gzip.open(alerts_file, 'rt') as f:
                alerts_data = json.load(f)

            if dry_run:
                self.stdout.write(f"Would restore {len(alerts_data)} alerts")
                return

            # Clear existing alerts
            from models import Alert
            Alert.objects.all().delete()

            # Restore alerts
            for alert in alerts_data:
                Alert.objects.create(**alert)

            self.stdout.write(self.style.SUCCESS('Alerts restored'))

        except Exception as e:
            logger.error(f"Alerts restore failed: {e}")
            raise

    def restore_config(self, backup_dir: str, dry_run: bool):
        """Restore configuration"""
        self.stdout.write('Restoring configuration...')

        try:
            config_file = os.path.join(backup_dir, 'config.json.gz')
            if not os.path.exists(config_file):
                self.stdout.write(self.style.WARNING('No config backup found'))
                return

            # Backup current config
            current_config = os.path.join(settings.MONITORING_DIR, 'config.json')
            if os.path.exists(current_config):
                backup_path = f"{current_config}.bak"
                if not dry_run:
                    shutil.copy2(current_config, backup_path)
                self.stdout.write(f"Current config backed up to {backup_path}")

            if dry_run:
                self.stdout.write("Would restore configuration")
                return

            # Restore config
            with gzip.open(config_file, 'rb') as f_in:
                with open(current_config, 'wb') as f_out:
                    shutil.copyfileobj(f_in, f_out)

            # Restore templates
            templates_backup = os.path.join(backup_dir, 'templates.tar.gz')
            if os.path.exists(templates_backup):
                templates_dir = os.path.join(settings.BASE_DIR, 'templates/alerts')
                shutil.rmtree(templates_dir, ignore_errors=True)
                shutil.unpack_archive(templates_backup, templates_dir)

            self.stdout.write(self.style.SUCCESS('Configuration restored'))

        except Exception as e:
            logger.error(f"Config restore failed: {e}")
            raise

    def verify_restore(self):
        """Verify restore success"""
        self.stdout.write('Verifying restore...')

        try:
            # Check metrics
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0
            )
            metrics_count = len(redis_client.keys('metrics:*'))
            self.stdout.write(f"Metrics restored: {metrics_count}")

            # Check alerts
            from models import Alert
            alerts_count = Alert.objects.count()
            self.stdout.write(f"Alerts restored: {alerts_count}")

            # Check config
            config_path = os.path.join(settings.MONITORING_DIR, 'config.json')
            if os.path.exists(config_path):
                with open(config_path) as f:
                    config = json.load(f)
                self.stdout.write("Configuration restored")

            # Check services
            result = os.system('systemctl is-active --quiet terminusa-monitoring')
            if result == 0:
                self.stdout.write("Monitoring service running")
            else:
                self.stdout.write(self.style.WARNING("Monitoring service not running"))

        except Exception as e:
            logger.error(f"Restore verification failed: {e}")
            raise
