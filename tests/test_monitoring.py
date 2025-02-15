import unittest
from unittest.mock import Mock, patch
import sys
import os
import logging
import json
from datetime import datetime, timedelta
import threading
import queue
from prometheus_client import CollectorRegistry, Counter, Gauge, Histogram

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from db_setup import db
from models import User, Gate, Guild
from game_manager import MainGameManager

class TestMonitoring(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        
        # Set up logging
        self.log_queue = queue.Queue()
        self.queue_handler = QueueHandler(self.log_queue)
        self.logger = logging.getLogger('test_logger')
        self.logger.addHandler(self.queue_handler)
        self.logger.setLevel(logging.DEBUG)
        
        # Set up metrics
        self.registry = CollectorRegistry()
        self.metrics = {
            'requests_total': Counter('requests_total', 'Total requests', registry=self.registry),
            'active_users': Gauge('active_users', 'Number of active users', registry=self.registry),
            'response_time': Histogram('response_time', 'Response time in seconds', registry=self.registry)
        }
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.user = User(
                username='test_user',
                password='hashed_password',
                salt='test_salt',
                role='user',
                level=10
            )
            db.session.add(self.user)
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_error_logging(self):
        """Test error logging functionality"""
        # Test different log levels
        test_messages = {
            'debug': 'Debug message',
            'info': 'Info message',
            'warning': 'Warning message',
            'error': 'Error message',
            'critical': 'Critical message'
        }
        
        for level, message in test_messages.items():
            getattr(self.logger, level)(message)
        
        # Verify logs
        logs = []
        while not self.log_queue.empty():
            logs.append(self.log_queue.get())
        
        self.assertEqual(len(logs), len(test_messages))
        for log in logs:
            self.assertIn(log.message, test_messages.values())
            self.assertIn(log.levelname.lower(), test_messages.keys())

    def test_metrics_collection(self):
        """Test metrics collection"""
        # Test counter
        self.metrics['requests_total'].inc()
        self.assertEqual(
            self.metrics['requests_total']._value.get(),
            1.0
        )
        
        # Test gauge
        self.metrics['active_users'].set(10)
        self.assertEqual(
            self.metrics['active_users']._value.get(),
            10.0
        )
        
        # Test histogram
        with self.metrics['response_time'].time():
            # Simulate work
            pass
        
        self.assertGreater(
            self.metrics['response_time']._sum.get(),
            0
        )

    def test_performance_monitoring(self):
        """Test performance monitoring"""
        with patch('time.time') as mock_time:
            start_time = 1000.0
            mock_time.side_effect = [start_time, start_time + 0.5]  # 500ms
            
            with self.metrics['response_time'].time():
                # Simulate work
                pass
            
            # Verify timing
            self.assertEqual(
                self.metrics['response_time']._sum.get(),
                0.5
            )

    def test_system_health_checks(self):
        """Test system health monitoring"""
        def check_database():
            try:
                with self.app.app_context():
                    db.session.execute('SELECT 1')
                return True
            except Exception:
                return False
        
        def check_cache():
            try:
                # Simulate cache check
                return True
            except Exception:
                return False
        
        health_checks = {
            'database': check_database,
            'cache': check_cache
        }
        
        # Run health checks
        results = {}
        for name, check in health_checks.items():
            results[name] = check()
        
        # Verify results
        self.assertTrue(all(results.values()))

    def test_audit_logging(self):
        """Test audit logging functionality"""
        audit_events = [
            {
                'user_id': self.user.id,
                'action': 'login',
                'details': {'ip': '127.0.0.1'}
            },
            {
                'user_id': self.user.id,
                'action': 'gate_enter',
                'details': {'gate_id': 1}
            }
        ]
        
        # Log audit events
        for event in audit_events:
            self.logger.info(
                'AUDIT: %s',
                json.dumps(event)
            )
        
        # Verify audit logs
        logs = []
        while not self.log_queue.empty():
            log = self.log_queue.get()
            if 'AUDIT:' in log.message:
                logs.append(json.loads(log.message.replace('AUDIT: ', '')))
        
        self.assertEqual(len(logs), len(audit_events))
        for log, event in zip(logs, audit_events):
            self.assertEqual(log['user_id'], event['user_id'])
            self.assertEqual(log['action'], event['action'])

    def test_resource_monitoring(self):
        """Test resource usage monitoring"""
        import psutil
        
        # Monitor CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.assertIsInstance(cpu_percent, float)
        self.assertGreaterEqual(cpu_percent, 0)
        self.assertLessEqual(cpu_percent, 100)
        
        # Monitor memory usage
        memory = psutil.virtual_memory()
        self.assertGreaterEqual(memory.percent, 0)
        self.assertLessEqual(memory.percent, 100)
        
        # Monitor disk usage
        disk = psutil.disk_usage('/')
        self.assertGreaterEqual(disk.percent, 0)
        self.assertLessEqual(disk.percent, 100)

    def test_event_tracking(self):
        """Test event tracking system"""
        event_tracker = EventTracker(self.logger)
        
        # Track various events
        events = [
            ('gate_enter', {'user_id': 1, 'gate_id': 1}),
            ('item_purchase', {'user_id': 1, 'item_id': 1, 'price': 100}),
            ('level_up', {'user_id': 1, 'new_level': 11})
        ]
        
        for event_type, data in events:
            event_tracker.track(event_type, data)
        
        # Verify event logs
        tracked_events = event_tracker.get_recent_events()
        self.assertEqual(len(tracked_events), len(events))
        
        for tracked, (event_type, data) in zip(tracked_events, events):
            self.assertEqual(tracked['type'], event_type)
            self.assertEqual(tracked['data'], data)

    def test_alert_system(self):
        """Test alert system functionality"""
        alert_system = AlertSystem(self.logger)
        
        # Test different alert levels
        alerts = [
            ('high_cpu_usage', 'warning', {'cpu_percent': 90}),
            ('database_error', 'error', {'error': 'Connection failed'}),
            ('raid_completion', 'info', {'raid_id': 1, 'status': 'success'})
        ]
        
        for name, level, data in alerts:
            alert_system.trigger(name, level, data)
        
        # Verify alerts
        recent_alerts = alert_system.get_recent_alerts()
        self.assertEqual(len(recent_alerts), len(alerts))
        
        for alert, (name, level, data) in zip(recent_alerts, alerts):
            self.assertEqual(alert['name'], name)
            self.assertEqual(alert['level'], level)
            self.assertEqual(alert['data'], data)

class QueueHandler(logging.Handler):
    """Custom logging handler that puts logs into a queue"""
    def __init__(self, queue):
        super().__init__()
        self.queue = queue

    def emit(self, record):
        self.queue.put(record)

class EventTracker:
    """System for tracking game events"""
    def __init__(self, logger):
        self.logger = logger
        self.events = []
        self.lock = threading.Lock()

    def track(self, event_type: str, data: dict):
        """Track a new event"""
        with self.lock:
            event = {
                'type': event_type,
                'data': data,
                'timestamp': datetime.utcnow()
            }
            self.events.append(event)
            self.logger.info('EVENT: %s', json.dumps(event))

    def get_recent_events(self, minutes: int = 5) -> list:
        """Get recent events within specified timeframe"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        with self.lock:
            return [
                event for event in self.events
                if event['timestamp'] >= cutoff
            ]

class AlertSystem:
    """System for handling alerts and notifications"""
    def __init__(self, logger):
        self.logger = logger
        self.alerts = []
        self.lock = threading.Lock()

    def trigger(self, name: str, level: str, data: dict):
        """Trigger a new alert"""
        with self.lock:
            alert = {
                'name': name,
                'level': level,
                'data': data,
                'timestamp': datetime.utcnow()
            }
            self.alerts.append(alert)
            self.logger.log(
                self._get_log_level(level),
                'ALERT: %s',
                json.dumps(alert)
            )

    def get_recent_alerts(self, minutes: int = 5) -> list:
        """Get recent alerts within specified timeframe"""
        cutoff = datetime.utcnow() - timedelta(minutes=minutes)
        with self.lock:
            return [
                alert for alert in self.alerts
                if alert['timestamp'] >= cutoff
            ]

    def _get_log_level(self, alert_level: str) -> int:
        """Convert alert level to logging level"""
        return {
            'debug': logging.DEBUG,
            'info': logging.INFO,
            'warning': logging.WARNING,
            'error': logging.ERROR,
            'critical': logging.CRITICAL
        }.get(alert_level.lower(), logging.INFO)

if __name__ == '__main__':
    unittest.main()
