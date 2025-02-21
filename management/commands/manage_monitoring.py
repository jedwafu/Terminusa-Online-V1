from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
import json
import redis
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Manage monitoring system operations'

    def add_arguments(self, parser):
        parser.add_argument(
            'action',
            choices=[
                'status',
                'start',
                'stop',
                'restart',
                'cleanup',
                'check',
                'purge-metrics',
                'purge-alerts',
                'reset-config',
                'test-alerts'
            ],
            help='Action to perform'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force the action without confirmation'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Number of days for data retention'
        )

    def handle(self, *args, **options):
        try:
            action = options['action']
            force = options['force']
            days = options['days']

            actions = {
                'status': self.show_status,
                'start': self.start_monitoring,
                'stop': self.stop_monitoring,
                'restart': self.restart_monitoring,
                'cleanup': self.cleanup_data,
                'check': self.check_health,
                'purge-metrics': self.purge_metrics,
                'purge-alerts': self.purge_alerts,
                'reset-config': self.reset_config,
                'test-alerts': self.test_alerts
            }

            if not force and action in ['stop', 'purge-metrics', 'purge-alerts', 'reset-config']:
                confirm = input(f"Are you sure you want to {action}? [y/N] ")
                if confirm.lower() != 'y':
                    self.stdout.write(self.style.WARNING('Operation cancelled'))
                    return

            actions[action](days=days)

        except Exception as e:
            logger.error(f"Monitoring management failed: {e}")
            raise CommandError(f"Failed to {action}: {str(e)}")

    def show_status(self, **kwargs):
        """Show monitoring system status"""
        self.stdout.write('Checking monitoring system status...')

        try:
            # Check services
            services = self.check_services()
            self.stdout.write('\nServices:')
            for service, status in services.items():
                style = self.style.SUCCESS if status['running'] else self.style.ERROR
                self.stdout.write(f"  {service}: {style(status['status'])}")

            # Check metrics
            metrics = self.check_metrics()
            self.stdout.write('\nMetrics:')
            self.stdout.write(f"  Total metrics: {metrics['total']}")
            self.stdout.write(f"  Last collection: {metrics['last_collection']}")
            self.stdout.write(f"  Storage used: {metrics['storage_used']}")

            # Check alerts
            alerts = self.check_alerts()
            self.stdout.write('\nAlerts:')
            self.stdout.write(f"  Active alerts: {alerts['active']}")
            self.stdout.write(f"  Last alert: {alerts['last_alert']}")
            self.stdout.write(f"  Alert channels: {', '.join(alerts['channels'])}")

            # Check resources
            resources = self.check_resources()
            self.stdout.write('\nResources:')
            self.stdout.write(f"  CPU Usage: {resources['cpu']}%")
            self.stdout.write(f"  Memory Usage: {resources['memory']}%")
            self.stdout.write(f"  Disk Usage: {resources['disk']}%")

        except Exception as e:
            logger.error(f"Status check failed: {e}")
            raise

    def start_monitoring(self, **kwargs):
        """Start monitoring services"""
        self.stdout.write('Starting monitoring services...')

        try:
            # Start monitoring service
            os.system('systemctl start terminusa-monitoring')
            
            # Initialize components
            from game_systems.monitoring_init import monitoring
            monitoring.init_app(settings.FLASK_APP)

            self.stdout.write(self.style.SUCCESS('Monitoring services started'))

        except Exception as e:
            logger.error(f"Failed to start monitoring: {e}")
            raise

    def stop_monitoring(self, **kwargs):
        """Stop monitoring services"""
        self.stdout.write('Stopping monitoring services...')

        try:
            # Stop monitoring service
            os.system('systemctl stop terminusa-monitoring')

            # Stop components
            from game_systems.monitoring_init import monitoring
            monitoring.cleanup()

            self.stdout.write(self.style.SUCCESS('Monitoring services stopped'))

        except Exception as e:
            logger.error(f"Failed to stop monitoring: {e}")
            raise

    def restart_monitoring(self, **kwargs):
        """Restart monitoring services"""
        self.stop_monitoring()
        self.start_monitoring()

    def cleanup_data(self, **kwargs):
        """Clean up old monitoring data"""
        days = kwargs.get('days', 30)
        self.stdout.write(f'Cleaning up monitoring data older than {days} days...')

        try:
            # Clean up metrics
            self.purge_metrics(days=days)

            # Clean up alerts
            self.purge_alerts(days=days)

            # Clean up logs
            self.cleanup_logs(days=days)

            self.stdout.write(self.style.SUCCESS('Data cleanup completed'))

        except Exception as e:
            logger.error(f"Data cleanup failed: {e}")
            raise

    def check_health(self, **kwargs):
        """Perform health check of monitoring system"""
        self.stdout.write('Performing health check...')

        try:
            checks = [
                self.check_services,
                self.check_metrics,
                self.check_alerts,
                self.check_resources
            ]

            all_healthy = True
            for check in checks:
                try:
                    result = check()
                    if not self.is_healthy(result):
                        all_healthy = False
                        self.stdout.write(
                            self.style.WARNING(f'Health check warning: {check.__name__}')
                        )
                except Exception as e:
                    all_healthy = False
                    self.stdout.write(
                        self.style.ERROR(f'Health check failed: {check.__name__} - {e}')
                    )

            if all_healthy:
                self.stdout.write(self.style.SUCCESS('All systems healthy'))
            else:
                self.stdout.write(self.style.WARNING('Some systems need attention'))

        except Exception as e:
            logger.error(f"Health check failed: {e}")
            raise

    def purge_metrics(self, **kwargs):
        """Purge old metrics data"""
        days = kwargs.get('days', 30)
        self.stdout.write(f'Purging metrics older than {days} days...')

        try:
            redis_client = redis.Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0
            )

            cutoff = datetime.utcnow() - timedelta(days=days)
            pattern = 'metrics:*'
            deleted = 0

            for key in redis_client.scan_iter(pattern):
                timestamp = key.decode().split(':')[1]
                if datetime.fromisoformat(timestamp) < cutoff:
                    redis_client.delete(key)
                    deleted += 1

            self.stdout.write(
                self.style.SUCCESS(f'Purged {deleted} old metrics')
            )

        except Exception as e:
            logger.error(f"Metrics purge failed: {e}")
            raise

    def purge_alerts(self, **kwargs):
        """Purge old alerts"""
        days = kwargs.get('days', 30)
        self.stdout.write(f'Purging alerts older than {days} days...')

        try:
            from models import Alert
            cutoff = datetime.utcnow() - timedelta(days=days)
            deleted = Alert.objects.filter(created_at__lt=cutoff).delete()[0]

            self.stdout.write(
                self.style.SUCCESS(f'Purged {deleted} old alerts')
            )

        except Exception as e:
            logger.error(f"Alerts purge failed: {e}")
            raise

    def reset_config(self, **kwargs):
        """Reset monitoring configuration"""
        self.stdout.write('Resetting monitoring configuration...')

        try:
            config_path = os.path.join(settings.MONITORING_DIR, 'config.json')
            
            # Backup existing config
            if os.path.exists(config_path):
                backup_path = f"{config_path}.bak"
                os.rename(config_path, backup_path)
                self.stdout.write(f"Existing config backed up to {backup_path}")

            # Create new config
            from game_systems.monitoring_init import MonitoringSystem
            monitoring = MonitoringSystem()
            monitoring.create_initial_config()

            self.stdout.write(self.style.SUCCESS('Configuration reset completed'))

        except Exception as e:
            logger.error(f"Config reset failed: {e}")
            raise

    def test_alerts(self, **kwargs):
        """Test alert notifications"""
        self.stdout.write('Testing alert notifications...')

        try:
            from game_systems.alert_manager import AlertManager, AlertSeverity

            alert_manager = AlertManager(
                config=settings.ALERT_CONFIG,
                redis_client=settings.REDIS_CLIENT
            )

            # Test different severity levels
            for severity in AlertSeverity:
                alert_manager.create_alert(
                    title=f"Test {severity.value} Alert",
                    message=f"This is a test {severity.value} alert",
                    severity=severity,
                    component="monitoring",
                    details={"test": True}
                )

            self.stdout.write(self.style.SUCCESS('Test alerts sent'))

        except Exception as e:
            logger.error(f"Alert test failed: {e}")
            raise

    def check_services(self) -> Dict:
        """Check monitoring service status"""
        services = {
            'monitoring': {'running': False, 'status': 'stopped'},
            'redis': {'running': False, 'status': 'stopped'},
            'websocket': {'running': False, 'status': 'stopped'}
        }

        for service in services:
            result = os.system(f'systemctl is-active --quiet terminusa-{service}')
            services[service]['running'] = result == 0
            services[service]['status'] = 'running' if result == 0 else 'stopped'

        return services

    def check_metrics(self) -> Dict:
        """Check metrics status"""
        redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0
        )

        metrics = redis_client.keys('metrics:*')
        last_metric = max(metrics, key=lambda x: x.decode().split(':')[1]) if metrics else None

        return {
            'total': len(metrics),
            'last_collection': last_metric.decode().split(':')[1] if last_metric else 'Never',
            'storage_used': redis_client.info()['used_memory_human']
        }

    def check_alerts(self) -> Dict:
        """Check alerts status"""
        from models import Alert

        last_alert = Alert.objects.order_by('-created_at').first()
        active_alerts = Alert.objects.filter(status='new').count()

        return {
            'active': active_alerts,
            'last_alert': last_alert.created_at if last_alert else 'Never',
            'channels': list(settings.ALERT_CONFIG['channels'].keys())
        }

    def check_resources(self) -> Dict:
        """Check system resources"""
        return {
            'cpu': psutil.cpu_percent(),
            'memory': psutil.virtual_memory().percent,
            'disk': psutil.disk_usage('/').percent
        }

    def cleanup_logs(self, days: int):
        """Clean up old log files"""
        log_dir = os.path.join(settings.LOG_DIR, 'monitoring')
        cutoff = datetime.utcnow() - timedelta(days=days)

        for root, _, files in os.walk(log_dir):
            for file in files:
                if file.endswith('.log'):
                    file_path = os.path.join(root, file)
                    if datetime.fromtimestamp(os.path.getmtime(file_path)) < cutoff:
                        os.remove(file_path)

    def is_healthy(self, check_result: Dict) -> bool:
        """Determine if check results indicate healthy status"""
        if not check_result:
            return False

        # Check for error indicators
        if any(isinstance(v, dict) and v.get('error') for v in check_result.values()):
            return False

        # Check for alert flags
        if any(isinstance(v, dict) and v.get('alert') for v in check_result.values()):
            return False

        return True
