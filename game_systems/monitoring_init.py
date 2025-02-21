import logging
import os
import redis
import psycopg2
from datetime import datetime
from typing import Dict, Optional

from config.monitoring import get_monitoring_config
from game_systems.monitoring_websocket import MonitoringWebSocket
from models import db, Alert

logger = logging.getLogger(__name__)

class MonitoringSystem:
    def __init__(self, app=None):
        self.app = app
        self.config = get_monitoring_config()
        self.websocket = None
        self.redis = None
        self.alert_manager = None
        self.metric_collector = None
        
        # Initialize logging
        self.setup_logging()
        
        if app is not None:
            self.init_app(app)

    def init_app(self, app):
        """Initialize monitoring with Flask app"""
        self.app = app
        
        # Initialize components
        self.init_connections()
        self.init_websocket()
        self.init_alert_manager()
        self.init_metric_collector()
        
        # Register monitoring routes
        self.register_routes()
        
        # Start monitoring tasks
        self.start_monitoring()

    def setup_logging(self):
        """Setup monitoring system logging"""
        log_config = self.config['logs']['file']
        
        # Create log directory if it doesn't exist
        os.makedirs(os.path.dirname(log_config['path']), exist_ok=True)
        
        # Configure logging
        logging.basicConfig(
            filename=log_config['path'],
            level=getattr(logging, log_config['level']),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            maxBytes=log_config['max_size'],
            backupCount=log_config['backup_count']
        )

    def init_connections(self):
        """Initialize database and cache connections"""
        try:
            # Initialize Redis connection
            self.redis = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                db=0
            )
            
            # Test Redis connection
            self.redis.ping()
            logger.info("Redis connection established")
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis connection: {e}")
            raise

    def init_websocket(self):
        """Initialize WebSocket monitoring"""
        try:
            self.websocket = MonitoringWebSocket(self.app.websocket_manager)
            logger.info("WebSocket monitoring initialized")
        except Exception as e:
            logger.error(f"Failed to initialize WebSocket monitoring: {e}")
            raise

    def init_alert_manager(self):
        """Initialize alert management system"""
        from game_systems.alert_manager import AlertManager
        
        try:
            self.alert_manager = AlertManager(
                config=self.config['alerts'],
                redis_client=self.redis
            )
            logger.info("Alert manager initialized")
        except Exception as e:
            logger.error(f"Failed to initialize alert manager: {e}")
            raise

    def init_metric_collector(self):
        """Initialize metric collection system"""
        from game_systems.metric_collector import MetricCollector
        
        try:
            self.metric_collector = MetricCollector(
                config=self.config['metrics'],
                redis_client=self.redis
            )
            logger.info("Metric collector initialized")
        except Exception as e:
            logger.error(f"Failed to initialize metric collector: {e}")
            raise

    def register_routes(self):
        """Register monitoring routes with Flask app"""
        try:
            from routes.monitoring import monitoring_bp
            self.app.register_blueprint(monitoring_bp)
            logger.info("Monitoring routes registered")
        except Exception as e:
            logger.error(f"Failed to register monitoring routes: {e}")
            raise

    def start_monitoring(self):
        """Start all monitoring tasks"""
        try:
            # Start metric collection
            self.metric_collector.start()
            
            # Start alert checking
            self.alert_manager.start()
            
            # Start health checks
            self.start_health_checks()
            
            logger.info("Monitoring tasks started")
            
        except Exception as e:
            logger.error(f"Failed to start monitoring tasks: {e}")
            raise

    def start_health_checks(self):
        """Start system health checks"""
        try:
            from game_systems.health_checker import HealthChecker
            
            health_checker = HealthChecker(
                config=self.config['health'],
                alert_manager=self.alert_manager
            )
            health_checker.start()
            
            logger.info("Health checks started")
            
        except Exception as e:
            logger.error(f"Failed to start health checks: {e}")
            raise

    def check_monitoring_status(self) -> Dict:
        """Check monitoring system status"""
        try:
            return {
                'websocket': self.check_websocket(),
                'alert_manager': self.check_alert_manager(),
                'metric_collector': self.check_metric_collector(),
                'connections': self.check_connections()
            }
        except Exception as e:
            logger.error(f"Failed to check monitoring status: {e}")
            return {
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def check_websocket(self) -> Dict:
        """Check WebSocket status"""
        return {
            'active': bool(self.websocket),
            'clients': len(self.websocket.clients) if self.websocket else 0,
            'timestamp': datetime.utcnow().isoformat()
        }

    def check_alert_manager(self) -> Dict:
        """Check alert manager status"""
        if not self.alert_manager:
            return {'active': False}
            
        return {
            'active': True,
            'pending_alerts': self.alert_manager.get_pending_count(),
            'timestamp': datetime.utcnow().isoformat()
        }

    def check_metric_collector(self) -> Dict:
        """Check metric collector status"""
        if not self.metric_collector:
            return {'active': False}
            
        return {
            'active': True,
            'last_collection': self.metric_collector.last_collection,
            'timestamp': datetime.utcnow().isoformat()
        }

    def check_connections(self) -> Dict:
        """Check connection status"""
        return {
            'redis': self.check_redis(),
            'database': self.check_database(),
            'timestamp': datetime.utcnow().isoformat()
        }

    def check_redis(self) -> Dict:
        """Check Redis connection"""
        try:
            self.redis.ping()
            return {
                'connected': True,
                'error': None
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

    def check_database(self) -> Dict:
        """Check database connection"""
        try:
            db.session.execute('SELECT 1')
            return {
                'connected': True,
                'error': None
            }
        except Exception as e:
            return {
                'connected': False,
                'error': str(e)
            }

    def cleanup(self):
        """Cleanup monitoring resources"""
        try:
            # Stop metric collection
            if self.metric_collector:
                self.metric_collector.stop()
            
            # Stop alert manager
            if self.alert_manager:
                self.alert_manager.stop()
            
            # Close Redis connection
            if self.redis:
                self.redis.close()
            
            logger.info("Monitoring cleanup completed")
            
        except Exception as e:
            logger.error(f"Failed to cleanup monitoring resources: {e}")
            raise

# Initialize monitoring system
monitoring = MonitoringSystem()

def init_monitoring(app):
    """Initialize monitoring for the application"""
    monitoring.init_app(app)
    return monitoring
