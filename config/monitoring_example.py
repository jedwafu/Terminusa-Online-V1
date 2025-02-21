"""
Example configuration for Terminusa Online Monitoring System.
Copy this file to monitoring_config.py and adjust settings as needed.
"""

import os
from datetime import timedelta

# Base Configuration
BASE_CONFIG = {
    'enabled': True,
    'debug': False,
    'environment': os.getenv('FLASK_ENV', 'production'),
    'admin_token': os.getenv('ADMIN_API_KEY'),
    'monitoring_url': 'https://terminusa.online/admin/monitoring'
}

# Directory Configuration
DIR_CONFIG = {
    'base_dir': '/var/www/terminusa',
    'log_dir': '/var/log/terminusa/monitoring',
    'backup_dir': '/var/www/backups/monitoring',
    'data_dir': '/var/www/terminusa/monitoring/data',
    'cache_dir': '/var/www/terminusa/monitoring/cache'
}

# Redis Configuration
REDIS_CONFIG = {
    'host': os.getenv('REDIS_HOST', 'localhost'),
    'port': int(os.getenv('REDIS_PORT', 6379)),
    'db': 0,
    'password': os.getenv('REDIS_PASSWORD'),
    'socket_timeout': 5,
    'socket_connect_timeout': 5,
    'retry_on_timeout': True
}

# Database Configuration
DB_CONFIG = {
    'engine': 'django.db.backends.postgresql',
    'name': os.getenv('DB_NAME', 'terminusa_db'),
    'user': os.getenv('DB_USER', 'terminusa_user'),
    'password': os.getenv('DB_PASSWORD'),
    'host': os.getenv('DB_HOST', 'localhost'),
    'port': os.getenv('DB_PORT', '5432'),
    'options': {
        'sslmode': 'require'
    }
}

# Metric Collection Configuration
METRIC_CONFIG = {
    'collection': {
        'enabled': True,
        'intervals': {
            'system': 60,      # seconds
            'database': 300,   # 5 minutes
            'application': 30  # 30 seconds
        },
        'batch_size': 1000
    },
    'retention': {
        'raw': timedelta(days=1),
        'hourly': timedelta(days=7),
        'daily': timedelta(days=30),
        'monthly': timedelta(days=365)
    },
    'aggregation': {
        'windows': ['5min', '1hour', '1day'],
        'functions': ['avg', 'min', 'max', 'count']
    },
    'compression': {
        'enabled': True,
        'algorithm': 'gzip',
        'level': 6,
        'min_size': 1024  # 1KB
    }
}

# Alert Configuration
ALERT_CONFIG = {
    'enabled': True,
    'channels': {
        'email': {
            'enabled': True,
            'from': 'monitoring@terminusa.online',
            'recipients': ['admin@terminusa.online'],
            'smtp_host': os.getenv('EMAIL_HOST'),
            'smtp_port': int(os.getenv('EMAIL_PORT', 587)),
            'smtp_user': os.getenv('EMAIL_USER'),
            'smtp_password': os.getenv('EMAIL_PASSWORD'),
            'use_tls': True
        },
        'slack': {
            'enabled': True,
            'webhook_url': os.getenv('SLACK_WEBHOOK_URL'),
            'channel': '#monitoring',
            'username': 'Monitoring Bot',
            'icon_emoji': ':warning:'
        },
        'websocket': {
            'enabled': True,
            'url': 'wss://terminusa.online/ws/monitoring'
        }
    },
    'thresholds': {
        'system': {
            'cpu': {
                'warning': 80,
                'critical': 90,
                'duration': 300  # 5 minutes
            },
            'memory': {
                'warning': 85,
                'critical': 95,
                'duration': 300
            },
            'disk': {
                'warning': 85,
                'critical': 95,
                'duration': 3600  # 1 hour
            }
        },
        'database': {
            'connections': {
                'warning': 800,
                'critical': 1000
            },
            'query_time': {
                'warning': 5,  # seconds
                'critical': 30
            }
        },
        'application': {
            'response_time': {
                'warning': 500,  # milliseconds
                'critical': 1000
            },
            'error_rate': {
                'warning': 5,  # percentage
                'critical': 10
            }
        }
    },
    'throttling': {
        'default': 300,  # 5 minutes
        'critical': 60,  # 1 minute
        'warning': 300,  # 5 minutes
        'info': 900     # 15 minutes
    }
}

# Backup Configuration
BACKUP_CONFIG = {
    'enabled': True,
    'schedule': {
        'daily': {
            'time': '01:00',
            'retention': 7     # days
        },
        'weekly': {
            'day': 'sunday',
            'time': '02:00',
            'retention': 4     # weeks
        },
        'monthly': {
            'day': 1,
            'time': '03:00',
            'retention': 12    # months
        }
    },
    'compression': {
        'enabled': True,
        'algorithm': 'gzip',
        'level': 9
    },
    'storage': {
        'local': {
            'enabled': True,
            'path': '/var/www/backups/monitoring'
        },
        'remote': {
            'enabled': False,
            'type': 's3',
            'bucket': 'terminusa-backups',
            'path': 'monitoring'
        }
    }
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'caching': {
        'enabled': True,
        'backend': 'redis',
        'timeout': 3600,
        'key_prefix': 'monitoring:',
        'version': 1
    },
    'optimization': {
        'compression': True,
        'minification': True,
        'batch_processing': True,
        'connection_pooling': True
    },
    'rate_limiting': {
        'enabled': True,
        'default_limit': '1000/hour',
        'admin_limit': '5000/hour'
    }
}

# Security Configuration
SECURITY_CONFIG = {
    'authentication': {
        'required': True,
        'token_header': 'Authorization',
        'token_prefix': 'Bearer'
    },
    'authorization': {
        'enabled': True,
        'admin_required': True
    },
    'ip_whitelist': [
        '127.0.0.1',
        '46.250.228.210'
    ],
    'cors': {
        'enabled': True,
        'origins': [
            'https://terminusa.online',
            'https://play.terminusa.online'
        ],
        'methods': ['GET', 'POST'],
        'headers': ['Content-Type', 'Authorization']
    },
    'rate_limiting': {
        'enabled': True,
        'limit': '1000/hour'
    }
}

# Logging Configuration
LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
        'detailed': {
            'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
        }
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': '/var/log/terminusa/monitoring/monitoring.log',
            'maxBytes': 10485760,  # 10MB
            'backupCount': 10,
            'formatter': 'detailed'
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'standard'
        }
    },
    'loggers': {
        'monitoring': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    'enabled': True,
    'url': 'wss://terminusa.online/ws/monitoring',
    'ping_interval': 30,
    'ping_timeout': 10,
    'max_message_size': 1048576,  # 1MB
    'max_connections': 100
}

# Health Check Configuration
HEALTH_CHECK_CONFIG = {
    'enabled': True,
    'interval': 60,  # seconds
    'timeout': 5,
    'endpoints': [
        'https://terminusa.online/health',
        'https://play.terminusa.online/health'
    ],
    'services': [
        'terminusa',
        'terminusa-terminal',
        'nginx',
        'postgresql',
        'redis'
    ]
}

# Get environment-specific configuration
def get_config():
    """Get environment-specific configuration."""
    env = os.getenv('FLASK_ENV', 'production')
    
    if env == 'development':
        # Override with development settings
        METRIC_CONFIG['collection']['intervals'] = {
            'system': 30,
            'database': 60,
            'application': 15
        }
        ALERT_CONFIG['enabled'] = False
        BACKUP_CONFIG['enabled'] = False
        
    elif env == 'testing':
        # Override with testing settings
        METRIC_CONFIG['collection']['enabled'] = False
        ALERT_CONFIG['enabled'] = False
        BACKUP_CONFIG['enabled'] = False
        
    return {
        'base': BASE_CONFIG,
        'dirs': DIR_CONFIG,
        'redis': REDIS_CONFIG,
        'database': DB_CONFIG,
        'metrics': METRIC_CONFIG,
        'alerts': ALERT_CONFIG,
        'backup': BACKUP_CONFIG,
        'performance': PERFORMANCE_CONFIG,
        'security': SECURITY_CONFIG,
        'logging': LOGGING_CONFIG,
        'websocket': WEBSOCKET_CONFIG,
        'health': HEALTH_CHECK_CONFIG
    }
