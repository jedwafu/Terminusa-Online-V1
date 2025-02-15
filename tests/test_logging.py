import unittest
from unittest.mock import Mock, patch
import sys
import os
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum, auto
import tempfile
import shutil

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LogLevel(Enum):
    """Log level types"""
    DEBUG = logging.DEBUG
    INFO = logging.INFO
    WARNING = logging.WARNING
    ERROR = logging.ERROR
    CRITICAL = logging.CRITICAL

class LogCategory(Enum):
    """Log categories"""
    SYSTEM = auto()
    SECURITY = auto()
    GAME = auto()
    COMBAT = auto()
    ECONOMY = auto()
    NETWORK = auto()
    DATABASE = auto()
    PERFORMANCE = auto()

class GameLogger:
    """Game logging system"""
    def __init__(self, log_dir: str = 'logs'):
        self.log_dir = log_dir
        self.loggers: Dict[LogCategory, logging.Logger] = {}
        self.setup_logging()

    def setup_logging(self):
        """Set up logging system"""
        os.makedirs(self.log_dir, exist_ok=True)
        
        # Create loggers for each category
        for category in LogCategory:
            logger = logging.getLogger(category.name)
            logger.setLevel(logging.DEBUG)
            
            # File handler
            file_handler = logging.FileHandler(
                os.path.join(self.log_dir, f'{category.name.lower()}.log')
            )
            file_handler.setLevel(logging.DEBUG)
            
            # Format
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s'
            )
            file_handler.setFormatter(formatter)
            
            logger.addHandler(file_handler)
            self.loggers[category] = logger

    def log(
        self,
        category: LogCategory,
        level: LogLevel,
        message: str,
        extra: Optional[Dict] = None
    ):
        """Log a message"""
        logger = self.loggers.get(category)
        if not logger:
            return
        
        # Format message with extra data
        if extra:
            message = f"{message} - {json.dumps(extra)}"
        
        logger.log(level.value, message)

    def get_logs(
        self,
        category: LogCategory,
        level: Optional[LogLevel] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        limit: int = 100
    ) -> List[Dict]:
        """Get logs with filtering"""
        log_file = os.path.join(
            self.log_dir,
            f'{category.name.lower()}.log'
        )
        
        if not os.path.exists(log_file):
            return []
        
        logs = []
        with open(log_file, 'r') as f:
            for line in f:
                try:
                    # Parse log entry
                    timestamp_str = line[:19]
                    log_time = datetime.strptime(
                        timestamp_str,
                        '%Y-%m-%d %H:%M:%S'
                    )
                    
                    # Apply time filter
                    if start_time and log_time < start_time:
                        continue
                    if end_time and log_time > end_time:
                        continue
                    
                    # Parse level
                    level_start = line.find(' - ') + 3
                    level_end = line.find(' - ', level_start)
                    log_level = LogLevel[line[level_start:level_end]]
                    
                    # Apply level filter
                    if level and log_level != level:
                        continue
                    
                    # Get message
                    message = line[level_end + 3:].strip()
                    
                    logs.append({
                        'timestamp': log_time,
                        'level': log_level,
                        'message': message
                    })
                    
                    if len(logs) >= limit:
                        break
                except Exception:
                    continue
        
        return logs

    def clear_logs(self, category: Optional[LogCategory] = None):
        """Clear log files"""
        if category:
            log_file = os.path.join(
                self.log_dir,
                f'{category.name.lower()}.log'
            )
            if os.path.exists(log_file):
                os.remove(log_file)
        else:
            for category in LogCategory:
                log_file = os.path.join(
                    self.log_dir,
                    f'{category.name.lower()}.log'
                )
                if os.path.exists(log_file):
                    os.remove(log_file)

class TestLogging(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.logger = GameLogger(self.temp_dir)

    def tearDown(self):
        """Clean up after each test"""
        shutil.rmtree(self.temp_dir)

    def test_basic_logging(self):
        """Test basic logging functionality"""
        # Log a message
        self.logger.log(
            LogCategory.SYSTEM,
            LogLevel.INFO,
            "Test message"
        )
        
        # Get logs
        logs = self.logger.get_logs(LogCategory.SYSTEM)
        
        # Verify log
        self.assertEqual(len(logs), 1)
        self.assertEqual(logs[0]['level'], LogLevel.INFO)
        self.assertIn("Test message", logs[0]['message'])

    def test_log_levels(self):
        """Test different log levels"""
        # Log messages at different levels
        messages = {
            LogLevel.DEBUG: "Debug message",
            LogLevel.INFO: "Info message",
            LogLevel.WARNING: "Warning message",
            LogLevel.ERROR: "Error message",
            LogLevel.CRITICAL: "Critical message"
        }
        
        for level, message in messages.items():
            self.logger.log(LogCategory.SYSTEM, level, message)
        
        # Get logs for each level
        for level, message in messages.items():
            logs = self.logger.get_logs(
                LogCategory.SYSTEM,
                level=level
            )
            self.assertEqual(len(logs), 1)
            self.assertEqual(logs[0]['level'], level)
            self.assertIn(message, logs[0]['message'])

    def test_log_categories(self):
        """Test logging to different categories"""
        # Log to different categories
        categories = {
            LogCategory.GAME: "Game event",
            LogCategory.COMBAT: "Combat event",
            LogCategory.ECONOMY: "Economy event"
        }
        
        for category, message in categories.items():
            self.logger.log(category, LogLevel.INFO, message)
        
        # Verify each category
        for category, message in categories.items():
            logs = self.logger.get_logs(category)
            self.assertEqual(len(logs), 1)
            self.assertIn(message, logs[0]['message'])

    def test_extra_data(self):
        """Test logging with extra data"""
        # Log with extra data
        extra_data = {
            'user_id': 123,
            'action': 'login',
            'ip': '127.0.0.1'
        }
        
        self.logger.log(
            LogCategory.SECURITY,
            LogLevel.INFO,
            "User login",
            extra=extra_data
        )
        
        # Get logs
        logs = self.logger.get_logs(LogCategory.SECURITY)
        
        # Verify extra data
        self.assertEqual(len(logs), 1)
        log_message = logs[0]['message']
        self.assertIn(str(extra_data['user_id']), log_message)
        self.assertIn(extra_data['action'], log_message)

    def test_time_filtering(self):
        """Test log filtering by time"""
        # Create logs at different times
        now = datetime.now()
        
        with patch('datetime.datetime') as mock_datetime:
            # Yesterday's log
            mock_datetime.now.return_value = now - timedelta(days=1)
            self.logger.log(
                LogCategory.SYSTEM,
                LogLevel.INFO,
                "Old message"
            )
            
            # Today's log
            mock_datetime.now.return_value = now
            self.logger.log(
                LogCategory.SYSTEM,
                LogLevel.INFO,
                "New message"
            )
        
        # Get recent logs
        logs = self.logger.get_logs(
            LogCategory.SYSTEM,
            start_time=now - timedelta(hours=1)
        )
        
        self.assertEqual(len(logs), 1)
        self.assertIn("New message", logs[0]['message'])

    def test_log_clearing(self):
        """Test log clearing"""
        # Create some logs
        self.logger.log(
            LogCategory.SYSTEM,
            LogLevel.INFO,
            "Test message"
        )
        
        # Clear logs
        self.logger.clear_logs(LogCategory.SYSTEM)
        
        # Verify logs cleared
        logs = self.logger.get_logs(LogCategory.SYSTEM)
        self.assertEqual(len(logs), 0)

    def test_log_limit(self):
        """Test log retrieval limit"""
        # Create many logs
        for i in range(200):
            self.logger.log(
                LogCategory.SYSTEM,
                LogLevel.INFO,
                f"Message {i}"
            )
        
        # Get logs with limit
        logs = self.logger.get_logs(
            LogCategory.SYSTEM,
            limit=50
        )
        
        self.assertEqual(len(logs), 50)

    def test_error_logging(self):
        """Test error logging"""
        # Log an error with stack trace
        try:
            raise ValueError("Test error")
        except Exception as e:
            self.logger.log(
                LogCategory.SYSTEM,
                LogLevel.ERROR,
                str(e),
                extra={'traceback': str(e.__traceback__)}
            )
        
        # Get error logs
        logs = self.logger.get_logs(
            LogCategory.SYSTEM,
            level=LogLevel.ERROR
        )
        
        self.assertEqual(len(logs), 1)
        self.assertIn("Test error", logs[0]['message'])

    def test_performance_logging(self):
        """Test performance logging"""
        # Log performance metrics
        metrics = {
            'cpu_usage': 45.2,
            'memory_usage': 1024.5,
            'response_time': 0.15
        }
        
        self.logger.log(
            LogCategory.PERFORMANCE,
            LogLevel.INFO,
            "Performance metrics",
            extra=metrics
        )
        
        # Get performance logs
        logs = self.logger.get_logs(LogCategory.PERFORMANCE)
        
        self.assertEqual(len(logs), 1)
        log_message = logs[0]['message']
        self.assertIn(str(metrics['cpu_usage']), log_message)
        self.assertIn(str(metrics['memory_usage']), log_message)

    def test_security_logging(self):
        """Test security event logging"""
        # Log security events
        events = [
            {
                'event': 'failed_login',
                'username': 'test_user',
                'ip': '192.168.1.1',
                'reason': 'invalid_password'
            },
            {
                'event': 'suspicious_activity',
                'user_id': 123,
                'activity': 'rapid_requests',
                'count': 1000
            }
        ]
        
        for event in events:
            self.logger.log(
                LogCategory.SECURITY,
                LogLevel.WARNING,
                f"Security event: {event['event']}",
                extra=event
            )
        
        # Get security logs
        logs = self.logger.get_logs(
            LogCategory.SECURITY,
            level=LogLevel.WARNING
        )
        
        self.assertEqual(len(logs), 2)
        for log, event in zip(logs, events):
            self.assertIn(event['event'], log['message'])

if __name__ == '__main__':
    unittest.main()
