"""
Monitoring configuration for Terminusa Online
"""

# System Monitoring Thresholds
SYSTEM_THRESHOLDS = {
    'cpu': {
        'warning': 70,  # Percentage
        'critical': 85,
        'duration': 300  # 5 minutes
    },
    'memory': {
        'warning': 75,  # Percentage
        'critical': 90,
        'duration': 300
    },
    'disk': {
        'warning': 80,  # Percentage
        'critical': 90,
        'duration': 3600  # 1 hour
    },
    'network': {
        'bandwidth_warning': 80,  # Percentage of max bandwidth
        'bandwidth_critical': 90,
        'latency_warning': 100,  # milliseconds
        'latency_critical': 200
    }
}

# Database Monitoring Thresholds
DATABASE_THRESHOLDS = {
    'connections': {
        'warning': 800,
        'critical': 1000
    },
    'query_time': {
        'warning': 5,  # seconds
        'critical': 30
    },
    'deadlocks': {
        'warning': 5,  # per hour
        'critical': 10
    },
    'cache_hit_ratio': {
        'warning': 0.95,
        'critical': 0.90
    }
}

# Cache Monitoring Thresholds
CACHE_THRESHOLDS = {
    'memory_usage': {
        'warning': 80,  # Percentage
        'critical': 90
    },
    'eviction_rate': {
        'warning': 100,  # per minute
        'critical': 1000
    },
    'hit_rate': {
        'warning': 0.90,
        'critical': 0.80
    }
}

# Game System Thresholds
GAME_THRESHOLDS = {
    'active_players': {
        'warning': 8000,
        'critical': 10000
    },
    'active_wars': {
        'warning': 80,
        'critical': 100
    },
    'transaction_rate': {
        'warning': 1000,  # per minute
        'critical': 2000
    },
    'response_time': {
        'warning': 500,  # milliseconds
        'critical': 1000
    }
}

# Service Health Check Configuration
SERVICE_CHECKS = {
    'terminusa': {
        'check_interval': 60,  # seconds
        'timeout': 5,
        'retry_count': 3,
        'retry_delay': 5
    },
    'terminusa-terminal': {
        'check_interval': 60,
        'timeout': 5,
        'retry_count': 3,
        'retry_delay': 5
    },
    'nginx': {
        'check_interval': 30,
        'timeout': 3,
        'retry_count': 3,
        'retry_delay': 3
    },
    'postgresql': {
        'check_interval': 60,
        'timeout': 5,
        'retry_count': 3,
        'retry_delay': 5
    },
    'redis': {
        'check_interval': 30,
        'timeout': 3,
        'retry_count': 3,
        'retry_delay': 3
    }
}

# Alert Configuration
ALERT_CONFIG = {
    'channels': {
        'email': {
            'enabled': True,
            'recipients': ['admin@terminusa.online'],
            'min_severity': 'warning'
        },
        'slack': {
            'enabled': True,
            'webhook_url': 'SLACK_WEBHOOK_URL',
            'channel': '#monitoring',
            'min_severity': 'warning'
        },
        'websocket': {
            'enabled': True,
            'min_severity': 'info'
        }
    },
    'throttling': {
        'default': 300,  # seconds
        'critical': 60,
        'warning': 300,
        'info': 900
    },
    'grouping': {
        'window': 300,  # seconds
        'max_group_size': 10
    }
}

# Metric Collection Configuration
METRIC_CONFIG = {
    'collection_interval': 60,  # seconds
    'retention_periods': {
        'raw': 86400,      # 1 day
        '1min': 604800,    # 7 days
        '5min': 2592000,   # 30 days
        '1hour': 31536000  # 1 year
    },
    'aggregation_windows': {
        '1min': 60,
        '5min': 300,
        '1hour': 3600
    }
}

# Log Configuration
LOG_CONFIG = {
    'file': {
        'path': '/var/log/terminusa/monitoring.log',
        'max_size': 10485760,  # 10MB
        'backup_count': 10,
        'level': 'INFO'
    },
    'syslog': {
        'enabled': True,
        'facility': 'local0',
        'level': 'WARNING'
    }
}

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    'ping_interval': 30,
    'ping_timeout': 10,
    'max_message_size': 1048576,  # 1MB
    'max_connections': 100
}

# Backup Monitoring Configuration
BACKUP_CONFIG = {
    'check_interval': 3600,  # 1 hour
    'max_age': 86400,       # 1 day
    'min_size': 1048576,    # 1MB
    'compression_ratio': {
        'warning': 0.8,
        'critical': 0.9
    }
}

# Performance Monitoring Configuration
PERFORMANCE_CONFIG = {
    'slow_query_threshold': 5,  # seconds
    'long_transaction_threshold': 30,  # seconds
    'high_cpu_threshold': 80,  # percentage
    'high_memory_threshold': 85,  # percentage
    'sampling_rate': 0.1  # 10% of requests
}

# Security Monitoring Configuration
SECURITY_CONFIG = {
    'failed_login_threshold': {
        'count': 5,
        'window': 300  # 5 minutes
    },
    'suspicious_ip_threshold': {
        'count': 100,
        'window': 3600  # 1 hour
    },
    'rate_limit_threshold': {
        'count': 1000,
        'window': 3600  # 1 hour
    }
}

# Resource Usage Limits
RESOURCE_LIMITS = {
    'max_memory_per_process': 1073741824,  # 1GB
    'max_cpu_per_process': 80,  # percentage
    'max_file_descriptors': 1024,
    'max_threads': 100
}

# Monitoring Dashboard Configuration
DASHBOARD_CONFIG = {
    'refresh_interval': 30,  # seconds
    'chart_points': 100,
    'default_timespan': '1h',
    'available_timespans': ['1h', '6h', '24h', '7d', '30d']
}

# Health Check Configuration
HEALTH_CHECK_CONFIG = {
    'endpoints': {
        '/': {
            'timeout': 5,
            'expected_status': 200
        },
        '/api/status': {
            'timeout': 5,
            'expected_status': 200
        },
        '/health': {
            'timeout': 2,
            'expected_status': 200
        }
    },
    'check_interval': 60,
    'failure_threshold': 3
}

# Notification Templates
NOTIFICATION_TEMPLATES = {
    'alert': {
        'email': {
            'subject': '[{severity}] Terminusa Alert: {title}',
            'body': '''
                Alert: {title}
                Severity: {severity}
                Time: {timestamp}
                Details: {details}
                
                System: {system}
                Component: {component}
                
                Actions Required: {actions}
            '''
        },
        'slack': {
            'title': '[{severity}] {title}',
            'fields': [
                'Severity',
                'Time',
                'System',
                'Component',
                'Details',
                'Actions'
            ]
        }
    }
}

# Export Configuration
def get_monitoring_config():
    """Get complete monitoring configuration"""
    return {
        'system': SYSTEM_THRESHOLDS,
        'database': DATABASE_THRESHOLDS,
        'cache': CACHE_THRESHOLDS,
        'game': GAME_THRESHOLDS,
        'services': SERVICE_CHECKS,
        'alerts': ALERT_CONFIG,
        'metrics': METRIC_CONFIG,
        'logs': LOG_CONFIG,
        'websocket': WEBSOCKET_CONFIG,
        'backup': BACKUP_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'security': SECURITY_CONFIG,
        'resources': RESOURCE_LIMITS,
        'dashboard': DASHBOARD_CONFIG,
        'health': HEALTH_CHECK_CONFIG,
        'notifications': NOTIFICATION_TEMPLATES
    }
