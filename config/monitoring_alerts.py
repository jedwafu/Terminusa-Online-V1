"""
Alert rules configuration for Terminusa Online Monitoring System.
This file defines alert conditions, thresholds, and responses.
"""

from typing import Dict, List
from datetime import timedelta

# Alert Severity Levels
SEVERITY_LEVELS = {
    'critical': {
        'name': 'Critical',
        'color': '#F44336',
        'priority': 1,
        'notification_channels': ['email', 'slack', 'websocket'],
        'auto_escalation': True,
        'escalation_timeout': 300,  # 5 minutes
        'retry_interval': 60  # 1 minute
    },
    'warning': {
        'name': 'Warning',
        'color': '#FFC107',
        'priority': 2,
        'notification_channels': ['email', 'slack', 'websocket'],
        'auto_escalation': False,
        'retry_interval': 300  # 5 minutes
    },
    'info': {
        'name': 'Info',
        'color': '#2196F3',
        'priority': 3,
        'notification_channels': ['websocket'],
        'auto_escalation': False,
        'retry_interval': 900  # 15 minutes
    }
}

# System Alert Rules
SYSTEM_ALERTS = {
    'high_cpu_usage': {
        'metric': 'cpu',
        'condition': 'gt',
        'warning_threshold': 80,
        'critical_threshold': 90,
        'duration': '5m',
        'description': 'High CPU usage detected',
        'resolution': 'Check system processes and resource usage'
    },
    'high_memory_usage': {
        'metric': 'memory',
        'condition': 'gt',
        'warning_threshold': 85,
        'critical_threshold': 95,
        'duration': '5m',
        'description': 'High memory usage detected',
        'resolution': 'Check memory-intensive processes and leaks'
    },
    'high_disk_usage': {
        'metric': 'disk',
        'condition': 'gt',
        'warning_threshold': 85,
        'critical_threshold': 95,
        'duration': '1h',
        'description': 'High disk usage detected',
        'resolution': 'Clean up old files and check disk space'
    }
}

# Application Alert Rules
APPLICATION_ALERTS = {
    'high_response_time': {
        'metric': 'response_time',
        'condition': 'gt',
        'warning_threshold': 500,  # ms
        'critical_threshold': 1000,  # ms
        'duration': '5m',
        'description': 'High response time detected',
        'resolution': 'Check application performance and database queries'
    },
    'high_error_rate': {
        'metric': 'error_rate',
        'condition': 'gt',
        'warning_threshold': 5,  # percent
        'critical_threshold': 10,  # percent
        'duration': '5m',
        'description': 'High error rate detected',
        'resolution': 'Check application logs and error tracking'
    },
    'low_request_rate': {
        'metric': 'request_rate',
        'condition': 'lt',
        'warning_threshold': 10,  # requests/sec
        'critical_threshold': 1,  # requests/sec
        'duration': '5m',
        'description': 'Low request rate detected',
        'resolution': 'Check application availability and network connectivity'
    }
}

# Database Alert Rules
DATABASE_ALERTS = {
    'high_connection_count': {
        'metric': 'connections',
        'condition': 'gt',
        'warning_threshold': 800,
        'critical_threshold': 1000,
        'duration': '5m',
        'description': 'High database connection count',
        'resolution': 'Check connection pooling and leaks'
    },
    'slow_queries': {
        'metric': 'query_time',
        'condition': 'gt',
        'warning_threshold': 5,  # seconds
        'critical_threshold': 30,  # seconds
        'duration': '5m',
        'description': 'Slow database queries detected',
        'resolution': 'Optimize queries and check indexes'
    },
    'low_cache_hit_ratio': {
        'metric': 'cache_hit_ratio',
        'condition': 'lt',
        'warning_threshold': 80,  # percent
        'critical_threshold': 70,  # percent
        'duration': '15m',
        'description': 'Low cache hit ratio',
        'resolution': 'Review caching strategy and warm up cache'
    }
}

# Game Alert Rules
GAME_ALERTS = {
    'high_player_count': {
        'metric': 'active_players',
        'condition': 'gt',
        'warning_threshold': 10000,
        'critical_threshold': 20000,
        'duration': '5m',
        'description': 'High player count detected',
        'resolution': 'Consider scaling resources'
    },
    'high_transaction_rate': {
        'metric': 'transactions',
        'condition': 'gt',
        'warning_threshold': 1000,  # tx/min
        'critical_threshold': 2000,  # tx/min
        'duration': '5m',
        'description': 'High transaction rate detected',
        'resolution': 'Monitor system performance and scaling'
    }
}

# Security Alert Rules
SECURITY_ALERTS = {
    'high_failed_logins': {
        'metric': 'failed_logins',
        'condition': 'gt',
        'warning_threshold': 50,
        'critical_threshold': 100,
        'duration': '5m',
        'description': 'High number of failed login attempts',
        'resolution': 'Check for potential security threats'
    },
    'suspicious_ips': {
        'metric': 'suspicious_ips',
        'condition': 'gt',
        'warning_threshold': 10,
        'critical_threshold': 20,
        'duration': '5m',
        'description': 'High number of suspicious IPs detected',
        'resolution': 'Review security logs and consider IP blocking'
    }
}

# Custom Alert Rules
CUSTOM_ALERTS = {
    'high_gate_failure_rate': {
        'metric': 'gate_failure_rate',
        'condition': 'gt',
        'warning_threshold': 30,  # percent
        'critical_threshold': 50,  # percent
        'duration': '15m',
        'description': 'High gate failure rate detected',
        'resolution': 'Review gate difficulty and player stats'
    },
    'low_currency_volume': {
        'metric': 'currency_volume',
        'condition': 'lt',
        'warning_threshold': 1000,
        'critical_threshold': 100,
        'duration': '1h',
        'description': 'Low currency transaction volume',
        'resolution': 'Check economy system and player engagement'
    }
}

# Alert Categories
ALERT_CATEGORIES = {
    'system': SYSTEM_ALERTS,
    'application': APPLICATION_ALERTS,
    'database': DATABASE_ALERTS,
    'game': GAME_ALERTS,
    'security': SECURITY_ALERTS,
    'custom': CUSTOM_ALERTS
}

# Alert Notification Templates
NOTIFICATION_TEMPLATES = {
    'email': {
        'critical': 'templates/alerts/email_critical.html',
        'warning': 'templates/alerts/email_warning.html',
        'info': 'templates/alerts/email_info.html'
    },
    'slack': {
        'critical': 'templates/alerts/slack_critical.json',
        'warning': 'templates/alerts/slack_warning.json',
        'info': 'templates/alerts/slack_info.json'
    }
}

# Alert Throttling
THROTTLING_CONFIG = {
    'default': {
        'window': 300,  # 5 minutes
        'max_alerts': 3
    },
    'critical': {
        'window': 60,   # 1 minute
        'max_alerts': 5
    },
    'warning': {
        'window': 300,  # 5 minutes
        'max_alerts': 3
    },
    'info': {
        'window': 900,  # 15 minutes
        'max_alerts': 1
    }
}

# Alert Escalation
ESCALATION_CONFIG = {
    'levels': [
        {
            'timeout': 300,  # 5 minutes
            'channels': ['email', 'slack']
        },
        {
            'timeout': 900,  # 15 minutes
            'channels': ['email', 'slack', 'phone']
        },
        {
            'timeout': 1800,  # 30 minutes
            'channels': ['email', 'slack', 'phone', 'pager']
        }
    ],
    'contacts': {
        'primary': ['admin@terminusa.online'],
        'secondary': ['support@terminusa.online'],
        'emergency': ['oncall@terminusa.online']
    }
}

# Alert Aggregation
AGGREGATION_CONFIG = {
    'windows': ['5m', '1h', '1d'],
    'group_by': ['severity', 'category', 'metric'],
    'max_alerts': 1000
}

# Alert Storage
STORAGE_CONFIG = {
    'retention': {
        'active': '7d',
        'resolved': '30d',
        'archived': '365d'
    },
    'cleanup': {
        'interval': '1d',
        'batch_size': 1000
    }
}

def get_alert_config(category: str, alert: str) -> Dict:
    """Get configuration for a specific alert."""
    return ALERT_CATEGORIES.get(category, {}).get(alert, {})

def get_severity_config(severity: str) -> Dict:
    """Get configuration for a severity level."""
    return SEVERITY_LEVELS.get(severity, {})

def get_throttling_config(severity: str) -> Dict:
    """Get throttling configuration for a severity level."""
    return THROTTLING_CONFIG.get(severity, THROTTLING_CONFIG['default'])

def get_notification_template(channel: str, severity: str) -> str:
    """Get notification template for a channel and severity."""
    return NOTIFICATION_TEMPLATES.get(channel, {}).get(severity, '')

def get_escalation_level(timeout: int) -> Dict:
    """Get escalation configuration for a timeout period."""
    for level in ESCALATION_CONFIG['levels']:
        if timeout >= level['timeout']:
            return level
    return ESCALATION_CONFIG['levels'][-1]

def get_storage_retention(status: str) -> timedelta:
    """Get storage retention period for alert status."""
    days = STORAGE_CONFIG['retention'].get(status, '7d').rstrip('d')
    return timedelta(days=int(days))
