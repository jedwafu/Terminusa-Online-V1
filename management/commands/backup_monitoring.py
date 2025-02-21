from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
import gzip
import shutil
import logging
import redis
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Backup monitoring data and manage retention'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            choices=['full', 'metrics', 'alerts', 'config'],
            default='full',
            help='Type of backup to perform'
        )
        parser.add_argument(
            '--retention-days',
            type=int,
            default=30,
            help='Number of days to retain backups'
        )
        parser.add_argument(
            '--compress',
            action='store_true',
            default=True,
            help='Compress backup files'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Starting monitoring backup...'))
            
            backup_type = options['type']
            retention_days = options['retention_days']
            compress = options['compress']
            
            # Create backup directory if it doesn't exist
            backup_dir = self.create_backup_directory()
            
            # Perform backup based on type
            if backup_type == 'full' or backup_type == 'metrics':
                self.backup_metrics(backup_dir, compress)
                
            if backup_type == 'full' or backup_type == 'alerts':
                self.backup_alerts(backup_dir, compress)
                
            if backup_type == 'full' or backup_type == 'config':
                self.backup_config(backup_dir, compress)
                
            # Clean up old backups
            self.cleanup_old_backups(backup_dir, retention_days)
            
            self.stdout.write(self.style.SUCCESS('Backup completed successfully'))
            
        except Exception as e:
            logger.error(f"Backup failed: {e}")
            self.stdout.write(self.style.ERROR(f'Backup failed: {str(e)}'))
            raise

    def create_backup_directory(self) -> str:
        """Create backup directory with timestamp"""
        timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.BACKUP_DIR, f'monitoring_{timestamp}')
        
        if not os.path.exists(backup_dir):
            os.makedirs(backup_dir)
            
        return backup_dir

    def backup_metrics(self, backup_dir: str, compress: bool):
        """Backup metric data from Redis"""
        self.stdout.write('Backing up metrics...')
        
        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0
            )
            
            # Get all metric keys
            metric_keys = redis_client.keys('metrics:*')
            metrics_data = {}
            
            for key in metric_keys:
                data = redis_client.get(key)
                if data:
                    metrics_data[key.decode()] = json.loads(data)
            
            # Save metrics
            metrics_file = os.path.join(backup_dir, 'metrics.json')
            if compress:
                metrics_file += '.gz'
                with gzip.open(metrics_file, 'wt') as f:
                    json.dump(metrics_data, f, indent=2)
            else:
                with open(metrics_file, 'w') as f:
                    json.dump(metrics_data, f, indent=2)
                    
            self.stdout.write(self.style.SUCCESS('Metrics backup completed'))
            
        except Exception as e:
            logger.error(f"Metrics backup failed: {e}")
            raise

    def backup_alerts(self, backup_dir: str, compress: bool):
        """Backup alert history"""
        self.stdout.write('Backing up alerts...')
        
        try:
            from models import Alert
            
            # Get all alerts
            alerts = Alert.objects.all().values()
            alerts_data = list(alerts)
            
            # Save alerts
            alerts_file = os.path.join(backup_dir, 'alerts.json')
            if compress:
                alerts_file += '.gz'
                with gzip.open(alerts_file, 'wt') as f:
                    json.dump(alerts_data, f, indent=2)
            else:
                with open(alerts_file, 'w') as f:
                    json.dump(alerts_data, f, indent=2)
                    
            self.stdout.write(self.style.SUCCESS('Alerts backup completed'))
            
        except Exception as e:
            logger.error(f"Alerts backup failed: {e}")
            raise

    def backup_config(self, backup_dir: str, compress: bool):
        """Backup monitoring configuration"""
        self.stdout.write('Backing up configuration...')
        
        try:
            config_path = os.path.join(settings.MONITORING_DIR, 'config.json')
            if os.path.exists(config_path):
                backup_path = os.path.join(backup_dir, 'config.json')
                if compress:
                    backup_path += '.gz'
                    with open(config_path, 'rb') as f_in:
                        with gzip.open(backup_path, 'wb') as f_out:
                            shutil.copyfileobj(f_in, f_out)
                else:
                    shutil.copy2(config_path, backup_path)
                    
            # Backup templates
            templates_dir = os.path.join(settings.BASE_DIR, 'templates/alerts')
            if os.path.exists(templates_dir):
                backup_templates_dir = os.path.join(backup_dir, 'templates')
                if compress:
                    shutil.make_archive(backup_templates_dir, 'gztar', templates_dir)
                else:
                    shutil.copytree(templates_dir, backup_templates_dir)
                    
            self.stdout.write(self.style.SUCCESS('Configuration backup completed'))
            
        except Exception as e:
            logger.error(f"Configuration backup failed: {e}")
            raise

    def cleanup_old_backups(self, backup_dir: str, retention_days: int):
        """Clean up old backup files"""
        self.stdout.write('Cleaning up old backups...')
        
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
            
            for root, dirs, files in os.walk(settings.BACKUP_DIR):
                for dir_name in dirs:
                    if dir_name.startswith('monitoring_'):
                        dir_path = os.path.join(root, dir_name)
                        dir_date = datetime.strptime(dir_name.split('_')[1], '%Y%m%d')
                        
                        if dir_date < cutoff_date:
                            shutil.rmtree(dir_path)
                            self.stdout.write(
                                self.style.SUCCESS(f'Removed old backup: {dir_name}')
                            )
                            
        except Exception as e:
            logger.error(f"Backup cleanup failed: {e}")
            raise

    def verify_backup(self, backup_dir: str):
        """Verify backup integrity"""
        self.stdout.write('Verifying backup...')
        
        try:
            # Check metrics backup
            metrics_file = os.path.join(backup_dir, 'metrics.json.gz')
            if os.path.exists(metrics_file):
                with gzip.open(metrics_file, 'rt') as f:
                    metrics_data = json.load(f)
                    if not isinstance(metrics_data, dict):
                        raise ValueError("Invalid metrics backup format")
                        
            # Check alerts backup
            alerts_file = os.path.join(backup_dir, 'alerts.json.gz')
            if os.path.exists(alerts_file):
                with gzip.open(alerts_file, 'rt') as f:
                    alerts_data = json.load(f)
                    if not isinstance(alerts_data, list):
                        raise ValueError("Invalid alerts backup format")
                        
            # Check config backup
            config_file = os.path.join(backup_dir, 'config.json.gz')
            if os.path.exists(config_file):
                with gzip.open(config_file, 'rt') as f:
                    config_data = json.load(f)
                    if not isinstance(config_data, dict):
                        raise ValueError("Invalid config backup format")
                        
            self.stdout.write(self.style.SUCCESS('Backup verification completed'))
            
        except Exception as e:
            logger.error(f"Backup verification failed: {e}")
            raise

    def restore_backup(self, backup_dir: str):
        """Restore from backup"""
        self.stdout.write('Restoring from backup...')
        
        try:
            # Restore metrics
            metrics_file = os.path.join(backup_dir, 'metrics.json.gz')
            if os.path.exists(metrics_file):
                redis_client = redis.Redis(
                    host=settings.REDIS_HOST,
                    port=settings.REDIS_PORT,
                    db=0
                )
                
                with gzip.open(metrics_file, 'rt') as f:
                    metrics_data = json.load(f)
                    for key, value in metrics_data.items():
                        redis_client.set(key, json.dumps(value))
                        
            # Restore alerts
            alerts_file = os.path.join(backup_dir, 'alerts.json.gz')
            if os.path.exists(alerts_file):
                from models import Alert
                with gzip.open(alerts_file, 'rt') as f:
                    alerts_data = json.load(f)
                    for alert in alerts_data:
                        Alert.objects.create(**alert)
                        
            # Restore config
            config_file = os.path.join(backup_dir, 'config.json.gz')
            if os.path.exists(config_file):
                config_path = os.path.join(settings.MONITORING_DIR, 'config.json')
                with gzip.open(config_file, 'rb') as f_in:
                    with open(config_path, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                        
            self.stdout.write(self.style.SUCCESS('Restore completed successfully'))
            
        except Exception as e:
            logger.error(f"Restore failed: {e}")
            raise
