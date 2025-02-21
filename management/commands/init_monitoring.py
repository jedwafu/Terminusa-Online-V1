from django.core.management.base import BaseCommand
from django.conf import settings
import os
import json
import logging
from datetime import datetime

from game_systems.monitoring_init import MonitoringSystem
from game_systems.alert_manager import AlertManager
from game_systems.metric_collector import MetricCollector

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Initialize monitoring system and required components'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reinitialization of monitoring system'
        )
        parser.add_argument(
            '--skip-checks',
            action='store_true',
            help='Skip prerequisite checks'
        )

    def handle(self, *args, **options):
        try:
            self.stdout.write(self.style.SUCCESS('Starting monitoring initialization...'))

            # Check prerequisites
            if not options['skip_checks']:
                self.check_prerequisites()

            # Create required directories
            self.create_directories()

            # Initialize monitoring system
            monitoring = MonitoringSystem()
            if options['force'] or not monitoring.is_initialized():
                monitoring.init_app(settings.FLASK_APP)
                self.stdout.write(self.style.SUCCESS('Monitoring system initialized'))
            else:
                self.stdout.write(self.style.WARNING('Monitoring system already initialized'))

            # Initialize alert manager
            self.init_alert_manager()

            # Initialize metric collector
            self.init_metric_collector()

            # Create initial configuration
            self.create_initial_config()

            # Verify initialization
            self.verify_initialization()

            self.stdout.write(self.style.SUCCESS('Monitoring initialization completed successfully'))

        except Exception as e:
            logger.error(f"Monitoring initialization failed: {e}")
            self.stdout.write(self.style.ERROR(f'Initialization failed: {str(e)}'))
            raise

    def check_prerequisites(self):
        """Check required prerequisites"""
        self.stdout.write('Checking prerequisites...')

        # Check Redis connection
        try:
            from redis import Redis
            redis = Redis(
                host=settings.REDIS_HOST,
                port=settings.REDIS_PORT,
                db=0
            )
            redis.ping()
            self.stdout.write(self.style.SUCCESS('Redis connection verified'))
        except Exception as e:
            raise Exception(f"Redis connection failed: {e}")

        # Check database connection
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute('SELECT 1')
            self.stdout.write(self.style.SUCCESS('Database connection verified'))
        except Exception as e:
            raise Exception(f"Database connection failed: {e}")

        # Check required directories
        required_dirs = [
            settings.LOG_DIR,
            os.path.join(settings.LOG_DIR, 'monitoring'),
            settings.MONITORING_DIR,
            os.path.join(settings.MONITORING_DIR, 'data')
        ]
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)
            if not os.access(directory, os.W_OK):
                raise Exception(f"Directory not writable: {directory}")
        self.stdout.write(self.style.SUCCESS('Directory permissions verified'))

    def create_directories(self):
        """Create required directories"""
        self.stdout.write('Creating required directories...')
        
        directories = {
            'logs': settings.LOG_DIR,
            'monitoring': settings.MONITORING_DIR,
            'data': os.path.join(settings.MONITORING_DIR, 'data'),
            'backup': settings.BACKUP_DIR
        }

        for name, path in directories.items():
            if not os.path.exists(path):
                os.makedirs(path)
                self.stdout.write(self.style.SUCCESS(f'Created {name} directory: {path}'))

    def init_alert_manager(self):
        """Initialize alert manager"""
        self.stdout.write('Initializing alert manager...')
        
        try:
            alert_manager = AlertManager(
                config=settings.ALERT_CONFIG,
                redis_client=settings.REDIS_CLIENT
            )
            alert_manager.start()
            self.stdout.write(self.style.SUCCESS('Alert manager initialized'))
            
        except Exception as e:
            raise Exception(f"Alert manager initialization failed: {e}")

    def init_metric_collector(self):
        """Initialize metric collector"""
        self.stdout.write('Initializing metric collector...')
        
        try:
            metric_collector = MetricCollector(
                config=settings.METRIC_CONFIG,
                redis_client=settings.REDIS_CLIENT
            )
            metric_collector.start()
            self.stdout.write(self.style.SUCCESS('Metric collector initialized'))
            
        except Exception as e:
            raise Exception(f"Metric collector initialization failed: {e}")

    def create_initial_config(self):
        """Create initial monitoring configuration"""
        self.stdout.write('Creating initial configuration...')
        
        config = {
            'initialized_at': datetime.utcnow().isoformat(),
            'email': {
                'enabled': True,
                'from': 'monitoring@terminusa.online',
                'recipients': ['admin@terminusa.online']
            },
            'slack': {
                'enabled': True,
                'webhook_url': settings.SLACK_WEBHOOK_URL,
                'channel': '#monitoring'
            },
            'metrics': {
                'collection_interval': 60,
                'retention_days': {
                    'raw': 1,
                    'hourly': 7,
                    'daily': 30
                }
            },
            'alerts': {
                'throttling': {
                    'default': 300,
                    'critical': 60
                }
            }
        }

        config_path = os.path.join(settings.MONITORING_DIR, 'config.json')
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
            
        self.stdout.write(self.style.SUCCESS('Initial configuration created'))

    def verify_initialization(self):
        """Verify monitoring initialization"""
        self.stdout.write('Verifying initialization...')

        checks = [
            self.verify_alert_manager,
            self.verify_metric_collector,
            self.verify_monitoring_service,
            self.verify_log_files
        ]

        for check in checks:
            try:
                check()
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Verification warning: {str(e)}'))

    def verify_alert_manager(self):
        """Verify alert manager initialization"""
        from game_systems.alert_manager import alert_manager
        if not alert_manager or not alert_manager.is_running():
            raise Exception("Alert manager not running")
        self.stdout.write(self.style.SUCCESS('Alert manager verified'))

    def verify_metric_collector(self):
        """Verify metric collector initialization"""
        from game_systems.metric_collector import metric_collector
        if not metric_collector or not metric_collector.is_running():
            raise Exception("Metric collector not running")
        self.stdout.write(self.style.SUCCESS('Metric collector verified'))

    def verify_monitoring_service(self):
        """Verify monitoring service status"""
        import subprocess
        result = subprocess.run(['systemctl', 'is-active', 'terminusa-monitoring'],
                              capture_output=True, text=True)
        if result.stdout.strip() != 'active':
            raise Exception("Monitoring service not active")
        self.stdout.write(self.style.SUCCESS('Monitoring service verified'))

    def verify_log_files(self):
        """Verify log file creation and permissions"""
        log_files = [
            os.path.join(settings.LOG_DIR, 'monitoring.log'),
            os.path.join(settings.LOG_DIR, 'alerts.log'),
            os.path.join(settings.LOG_DIR, 'metrics.log')
        ]

        for log_file in log_files:
            if not os.path.exists(log_file):
                open(log_file, 'a').close()
            if not os.access(log_file, os.W_OK):
                raise Exception(f"Log file not writable: {log_file}")
        self.stdout.write(self.style.SUCCESS('Log files verified'))
