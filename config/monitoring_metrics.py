"""
Metric definitions for Terminusa Online Monitoring System.
This file defines all metrics that are collected and monitored.
"""

from typing import Dict, List

# System Metrics
SYSTEM_METRICS = {
    'cpu': {
        'name': 'CPU Usage',
        'unit': 'percent',
        'collection_interval': 60,  # seconds
        'thresholds': {
            'warning': 80,
            'critical': 90
        },
        'aggregations': ['avg', 'max', 'min'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'memory': {
        'name': 'Memory Usage',
        'unit': 'percent',
        'collection_interval': 60,
        'thresholds': {
            'warning': 85,
            'critical': 95
        },
        'aggregations': ['avg', 'max', 'min'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'disk': {
        'name': 'Disk Usage',
        'unit': 'percent',
        'collection_interval': 300,  # 5 minutes
        'thresholds': {
            'warning': 85,
            'critical': 95
        },
        'aggregations': ['avg', 'max'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'network': {
        'name': 'Network Traffic',
        'unit': 'bytes/sec',
        'collection_interval': 60,
        'metrics': {
            'rx_bytes': 'Received Bytes',
            'tx_bytes': 'Transmitted Bytes',
            'rx_packets': 'Received Packets',
            'tx_packets': 'Transmitted Packets'
        },
        'aggregations': ['avg', 'max', 'sum'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    }
}

# Application Metrics
APPLICATION_METRICS = {
    'response_time': {
        'name': 'Response Time',
        'unit': 'milliseconds',
        'collection_interval': 30,
        'thresholds': {
            'warning': 500,
            'critical': 1000
        },
        'aggregations': ['avg', 'p95', 'p99'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'error_rate': {
        'name': 'Error Rate',
        'unit': 'percent',
        'collection_interval': 60,
        'thresholds': {
            'warning': 5,
            'critical': 10
        },
        'aggregations': ['avg', 'sum'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'request_rate': {
        'name': 'Request Rate',
        'unit': 'requests/sec',
        'collection_interval': 60,
        'aggregations': ['avg', 'max', 'sum'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    }
}

# Database Metrics
DATABASE_METRICS = {
    'connections': {
        'name': 'Active Connections',
        'unit': 'count',
        'collection_interval': 60,
        'thresholds': {
            'warning': 800,
            'critical': 1000
        },
        'aggregations': ['avg', 'max'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'query_time': {
        'name': 'Query Time',
        'unit': 'seconds',
        'collection_interval': 60,
        'thresholds': {
            'warning': 5,
            'critical': 30
        },
        'aggregations': ['avg', 'p95', 'p99'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'cache_hit_ratio': {
        'name': 'Cache Hit Ratio',
        'unit': 'percent',
        'collection_interval': 300,
        'thresholds': {
            'warning': 80,
            'critical': 70
        },
        'aggregations': ['avg'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    }
}

# Game Metrics
GAME_METRICS = {
    'active_players': {
        'name': 'Active Players',
        'unit': 'count',
        'collection_interval': 60,
        'aggregations': ['avg', 'max', 'min'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'active_wars': {
        'name': 'Active Wars',
        'unit': 'count',
        'collection_interval': 60,
        'aggregations': ['avg', 'max'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'transactions': {
        'name': 'Transaction Rate',
        'unit': 'transactions/min',
        'collection_interval': 60,
        'thresholds': {
            'warning': 1000,
            'critical': 2000
        },
        'aggregations': ['avg', 'max', 'sum'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    }
}

# Security Metrics
SECURITY_METRICS = {
    'failed_logins': {
        'name': 'Failed Login Attempts',
        'unit': 'count',
        'collection_interval': 300,
        'thresholds': {
            'warning': 50,
            'critical': 100
        },
        'aggregations': ['sum'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'suspicious_ips': {
        'name': 'Suspicious IPs',
        'unit': 'count',
        'collection_interval': 300,
        'thresholds': {
            'warning': 10,
            'critical': 20
        },
        'aggregations': ['sum'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    }
}

# Custom Metrics
CUSTOM_METRICS = {
    'gate_clears': {
        'name': 'Gate Clears',
        'unit': 'count',
        'collection_interval': 300,
        'dimensions': ['gate_type', 'difficulty'],
        'aggregations': ['sum'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    },
    'currency_volume': {
        'name': 'Currency Volume',
        'unit': 'amount',
        'collection_interval': 300,
        'dimensions': ['currency_type', 'transaction_type'],
        'aggregations': ['sum', 'avg'],
        'retention': {
            'raw': '1d',
            'hourly': '7d',
            'daily': '30d'
        }
    }
}

# Metric Categories
METRIC_CATEGORIES = {
    'system': SYSTEM_METRICS,
    'application': APPLICATION_METRICS,
    'database': DATABASE_METRICS,
    'game': GAME_METRICS,
    'security': SECURITY_METRICS,
    'custom': CUSTOM_METRICS
}

# Metric Collection Settings
COLLECTION_SETTINGS = {
    'batch_size': 1000,
    'timeout': 30,
    'retry_attempts': 3,
    'retry_delay': 5
}

# Metric Storage Settings
STORAGE_SETTINGS = {
    'compression': True,
    'compression_algorithm': 'gzip',
    'compression_level': 6,
    'batch_size': 1000,
    'max_batch_interval': 60
}

# Metric Aggregation Settings
AGGREGATION_SETTINGS = {
    'windows': ['5min', '1hour', '1day'],
    'functions': ['avg', 'min', 'max', 'sum', 'count', 'p95', 'p99'],
    'batch_size': 1000,
    'timeout': 300
}

# Metric Retention Settings
RETENTION_SETTINGS = {
    'raw': {
        'duration': '1d',
        'resolution': '1min'
    },
    'hourly': {
        'duration': '7d',
        'resolution': '1hour'
    },
    'daily': {
        'duration': '30d',
        'resolution': '1day'
    },
    'monthly': {
        'duration': '365d',
        'resolution': '1month'
    }
}

# Alert Rules
ALERT_RULES = {
    'system': {
        'cpu_high': {
            'metric': 'cpu',
            'condition': 'gt',
            'threshold': 90,
            'duration': '5m',
            'severity': 'critical'
        },
        'memory_high': {
            'metric': 'memory',
            'condition': 'gt',
            'threshold': 95,
            'duration': '5m',
            'severity': 'critical'
        }
    },
    'application': {
        'high_error_rate': {
            'metric': 'error_rate',
            'condition': 'gt',
            'threshold': 10,
            'duration': '5m',
            'severity': 'critical'
        },
        'slow_response': {
            'metric': 'response_time',
            'condition': 'gt',
            'threshold': 1000,
            'duration': '5m',
            'severity': 'warning'
        }
    }
}

def get_metric_config(category: str, metric: str) -> Dict:
    """Get configuration for a specific metric."""
    return METRIC_CATEGORIES.get(category, {}).get(metric, {})

def get_retention_config(window: str) -> Dict:
    """Get retention configuration for a specific window."""
    return RETENTION_SETTINGS.get(window, {})

def get_alert_rules(category: str) -> Dict:
    """Get alert rules for a specific category."""
    return ALERT_RULES.get(category, {})

def get_aggregation_functions() -> List[str]:
    """Get list of supported aggregation functions."""
    return AGGREGATION_SETTINGS['functions']
