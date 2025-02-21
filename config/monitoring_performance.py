"""
Performance configuration for Terminusa Online Monitoring System.
This file defines performance optimization settings and thresholds.
"""

from typing import Dict
import os

# Cache Configuration
CACHE_CONFIG = {
    'enabled': True,
    'backend': 'redis',
    'prefix': 'monitoring:cache:',
    'default_timeout': 3600,  # 1 hour
    'version': 1,
    'key_patterns': {
        'metrics': 'metrics:{name}:{timestamp}',
        'alerts': 'alerts:{id}',
        'config': 'config:{key}',
        'stats': 'stats:{name}:{period}'
    },
    'regions': {
        'metrics': {
            'timeout': 300,    # 5 minutes
            'max_entries': 10000
        },
        'alerts': {
            'timeout': 3600,   # 1 hour
            'max_entries': 1000
        },
        'config': {
            'timeout': 86400,  # 1 day
            'max_entries': 100
        }
    }
}

# Database Performance
DB_PERFORMANCE = {
    'pool_size': {
        'min': 5,
        'max': 20,
        'overflow': 10,
        'timeout': 30
    },
    'query_timeout': 30,  # seconds
    'statement_timeout': 60,  # seconds
    'idle_in_transaction_timeout': 60,  # seconds
    'max_connections': 100,
    'prepared_statements': True,
    'connection_recycling': {
        'enabled': True,
        'threshold': 10000,  # queries
        'timeout': 3600     # 1 hour
    },
    'query_caching': {
        'enabled': True,
        'timeout': 300,  # 5 minutes
        'max_size': 1000
    }
}

# Redis Performance
REDIS_PERFORMANCE = {
    'connection_pool': {
        'max_connections': 100,
        'timeout': 20,
        'retry_on_timeout': True,
        'max_retries': 3
    },
    'socket_keepalive': True,
    'socket_timeout': 10,
    'health_check_interval': 30,
    'retry_on_error': True,
    'max_memory': '1gb',
    'max_memory_policy': 'allkeys-lru',
    'eviction_policy': {
        'maxmemory_samples': 5,
        'maxmemory_policy': 'volatile-lru'
    }
}

# Metric Collection Performance
METRIC_PERFORMANCE = {
    'batch_processing': {
        'enabled': True,
        'size': 1000,
        'timeout': 60,  # seconds
        'retry_attempts': 3
    },
    'compression': {
        'enabled': True,
        'algorithm': 'gzip',
        'level': 6,
        'min_size': 1024  # bytes
    },
    'aggregation': {
        'batch_size': 1000,
        'timeout': 300,  # seconds
        'parallel_processing': True,
        'max_workers': 4
    },
    'storage_optimization': {
        'enabled': True,
        'compression_ratio': 0.3,
        'cleanup_interval': 86400  # 1 day
    }
}

# WebSocket Performance
WEBSOCKET_PERFORMANCE = {
    'connection_limit': 1000,
    'message_size_limit': 1048576,  # 1MB
    'compression': True,
    'ping_interval': 30,
    'ping_timeout': 10,
    'max_message_size': 1048576,  # 1MB
    'max_frame_size': 131072,    # 128KB
    'throttling': {
        'enabled': True,
        'rate': '100/second',
        'burst': 200
    }
}

# API Performance
API_PERFORMANCE = {
    'rate_limiting': {
        'enabled': True,
        'default': '1000/hour',
        'admin': '5000/hour',
        'burst': 100
    },
    'timeout': {
        'read': 30,    # seconds
        'write': 30,   # seconds
        'connect': 10  # seconds
    },
    'compression': {
        'enabled': True,
        'min_size': 1024,  # bytes
        'types': ['gzip', 'deflate']
    },
    'caching': {
        'enabled': True,
        'timeout': 300,  # 5 minutes
        'vary_by': ['Authorization']
    }
}

# System Performance
SYSTEM_PERFORMANCE = {
    'process_pool': {
        'min_workers': 2,
        'max_workers': 8,
        'thread_pool_size': 4
    },
    'memory_management': {
        'gc_interval': 300,  # 5 minutes
        'memory_limit': '2G',
        'swap_limit': '1G'
    },
    'io_optimization': {
        'buffer_size': 8192,  # bytes
        'direct_io': True,
        'async_io': True
    }
}

# Storage Performance
STORAGE_PERFORMANCE = {
    'compression': {
        'enabled': True,
        'algorithm': 'gzip',
        'level': 6,
        'min_size': 1024  # bytes
    },
    'batch_processing': {
        'enabled': True,
        'size': 1000,
        'timeout': 60  # seconds
    },
    'cleanup': {
        'enabled': True,
        'interval': 86400,  # 1 day
        'batch_size': 1000
    }
}

# Logging Performance
LOGGING_PERFORMANCE = {
    'async_logging': True,
    'buffer_size': 1000,
    'flush_interval': 5,  # seconds
    'compression': {
        'enabled': True,
        'algorithm': 'gzip',
        'level': 6
    },
    'rotation': {
        'max_size': '100M',
        'backup_count': 10,
        'compress_backups': True
    }
}

# Performance Monitoring
PERFORMANCE_MONITORING = {
    'enabled': True,
    'collection_interval': 60,  # seconds
    'metrics': {
        'cpu_usage': True,
        'memory_usage': True,
        'disk_io': True,
        'network_io': True,
        'cache_stats': True,
        'db_stats': True
    },
    'profiling': {
        'enabled': True,
        'sample_rate': 0.01,
        'max_depth': 30
    },
    'tracing': {
        'enabled': True,
        'sample_rate': 0.1,
        'max_events': 1000
    }
}

# Performance Optimization Settings
OPTIMIZATION_SETTINGS = {
    'auto_optimization': {
        'enabled': True,
        'interval': 3600,  # 1 hour
        'strategies': [
            'cache_optimization',
            'query_optimization',
            'connection_pooling',
            'resource_cleanup'
        ]
    },
    'thresholds': {
        'cpu_usage': 80,
        'memory_usage': 85,
        'disk_usage': 85,
        'response_time': 1000  # ms
    },
    'actions': {
        'cache_clear': {
            'enabled': True,
            'threshold': 90,  # percent
            'min_interval': 3600  # 1 hour
        },
        'connection_reset': {
            'enabled': True,
            'threshold': 90,  # percent
            'min_interval': 3600  # 1 hour
        },
        'log_rotation': {
            'enabled': True,
            'threshold': 100,  # MB
            'min_interval': 3600  # 1 hour
        }
    }
}

def get_cache_config(region: str = None) -> Dict:
    """Get cache configuration for a specific region."""
    if region:
        return CACHE_CONFIG['regions'].get(region, CACHE_CONFIG['regions']['default'])
    return CACHE_CONFIG

def get_db_pool_config() -> Dict:
    """Get database pool configuration."""
    return DB_PERFORMANCE['pool_size']

def get_redis_pool_config() -> Dict:
    """Get Redis pool configuration."""
    return REDIS_PERFORMANCE['connection_pool']

def get_metric_batch_config() -> Dict:
    """Get metric batch processing configuration."""
    return METRIC_PERFORMANCE['batch_processing']

def get_websocket_limits() -> Dict:
    """Get WebSocket limitation configuration."""
    return {
        'connection_limit': WEBSOCKET_PERFORMANCE['connection_limit'],
        'message_size_limit': WEBSOCKET_PERFORMANCE['message_size_limit']
    }

def get_api_rate_limits() -> Dict:
    """Get API rate limiting configuration."""
    return API_PERFORMANCE['rate_limiting']

def get_optimization_thresholds() -> Dict:
    """Get optimization threshold configuration."""
    return OPTIMIZATION_SETTINGS['thresholds']

def get_logging_config() -> Dict:
    """Get logging performance configuration."""
    return LOGGING_PERFORMANCE

def get_monitoring_config() -> Dict:
    """Get performance monitoring configuration."""
    return PERFORMANCE_MONITORING

def get_storage_config() -> Dict:
    """Get storage performance configuration."""
    return STORAGE_PERFORMANCE

def get_system_config() -> Dict:
    """Get system performance configuration."""
    return SYSTEM_PERFORMANCE
