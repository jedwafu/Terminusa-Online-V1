# Terminusa Online Monitoring Code Style Guide

## Python Code Style

### General Guidelines

1. **Code Layout**
```python
# Correct
def calculate_metric_average(
    metrics: List[float],
    window_size: int = 60
) -> float:
    """Calculate moving average of metrics."""
    return sum(metrics[-window_size:]) / len(metrics[-window_size:])

# Incorrect
def calculate_metric_average(metrics: List[float], window_size: int = 60) -> float:
    return sum(metrics[-window_size:]) / len(metrics[-window_size:])
```

2. **Imports**
```python
# Standard library imports
import os
import sys
from typing import Dict, List, Optional

# Third-party imports
import redis
import psutil
from flask import Flask, jsonify

# Local imports
from game_systems.metric_collector import MetricCollector
from game_systems.alert_manager import AlertManager
```

3. **Naming Conventions**
```python
# Classes: CamelCase
class MetricCollector:
    pass

# Functions/Variables: snake_case
def collect_system_metrics():
    system_status = get_status()

# Constants: UPPERCASE
MAX_RETRY_COUNT = 3
DEFAULT_TIMEOUT = 30
```

### Type Hints

1. **Basic Types**
```python
def process_metrics(
    raw_metrics: Dict[str, float],
    threshold: int = 100
) -> Dict[str, float]:
    pass
```

2. **Complex Types**
```python
from typing import TypeVar, Generic

T = TypeVar('T')

class MetricQueue(Generic[T]):
    def push(self, item: T) -> None:
        pass

    def pop(self) -> Optional[T]:
        pass
```

### Documentation

1. **Docstrings**
```python
def calculate_average(values: List[float]) -> float:
    """
    Calculate the average of a list of values.

    Args:
        values: List of numerical values

    Returns:
        Average of the values

    Raises:
        ValueError: If the list is empty
    """
    if not values:
        raise ValueError("Cannot calculate average of empty list")
    return sum(values) / len(values)
```

2. **Comments**
```python
# Configuration constants
MAX_RETRIES = 3  # Maximum number of retry attempts
TIMEOUT = 30     # Request timeout in seconds

def process_data():
    # Initialize counters
    success_count = 0
    error_count = 0

    # Process each batch
    for batch in data:
        # Skip empty batches
        if not batch:
            continue
```

### Error Handling

1. **Exception Hierarchy**
```python
class MonitoringError(Exception):
    """Base class for monitoring exceptions."""
    pass

class MetricCollectionError(MonitoringError):
    """Raised when metric collection fails."""
    pass

class AlertError(MonitoringError):
    """Raised when alert processing fails."""
    pass
```

2. **Error Handling Pattern**
```python
try:
    metrics = collector.collect()
except ConnectionError as e:
    logger.error(f"Failed to connect: {e}")
    raise MetricCollectionError(f"Connection failed: {e}")
except ValueError as e:
    logger.warning(f"Invalid metric value: {e}")
    return default_metrics
finally:
    collector.cleanup()
```

### Testing

1. **Test Structure**
```python
def test_metric_collection():
    """Test basic metric collection."""
    collector = MetricCollector()
    metrics = collector.collect()
    
    assert 'cpu' in metrics
    assert isinstance(metrics['cpu'], float)
    assert 0 <= metrics['cpu'] <= 100

@pytest.mark.parametrize('input,expected', [
    ([1, 2, 3], 2),
    ([0], 0),
    ([1, 1, 1], 1),
])
def test_average_calculation(input, expected):
    """Test average calculation with various inputs."""
    assert calculate_average(input) == expected
```

### Performance

1. **Optimization**
```python
# Use list comprehension instead of map/filter
# Good
squares = [x * x for x in range(10)]

# Avoid unnecessary list creation
# Good
sum(x * x for x in range(10))  # Generator
# Bad
sum([x * x for x in range(10)])  # List
```

2. **Caching**
```python
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_system_metrics() -> Dict[str, float]:
    """Get system metrics with caching."""
    return calculate_metrics()
```

### Logging

1. **Log Levels**
```python
# Error: Something went wrong
logger.error("Failed to collect metrics", exc_info=True)

# Warning: Something might be wrong
logger.warning("High memory usage detected: %s%%", memory_usage)

# Info: Normal operation
logger.info("Metric collection completed")

# Debug: Detailed information
logger.debug("Processing metric batch: %s", batch_id)
```

2. **Structured Logging**
```python
logger.info("Metric collected", extra={
    'metric_name': 'cpu_usage',
    'value': 75.5,
    'timestamp': '2024-01-20T12:00:00Z'
})
```

### Configuration

1. **Configuration Structure**
```python
MONITORING_CONFIG = {
    'metrics': {
        'collection_interval': 60,
        'retention_period': 86400,
        'batch_size': 1000
    },
    'alerts': {
        'enabled': True,
        'channels': ['email', 'slack'],
        'throttling': {
            'default': 300,
            'critical': 60
        }
    }
}
```

2. **Environment Variables**
```python
import os
from typing import Dict, Any

def get_config() -> Dict[str, Any]:
    """Get configuration with environment overrides."""
    config = DEFAULT_CONFIG.copy()
    
    if os.getenv('MONITORING_INTERVAL'):
        config['metrics']['collection_interval'] = \
            int(os.getenv('MONITORING_INTERVAL'))
    
    return config
```

### Security

1. **Sensitive Data**
```python
# Good: Use environment variables
api_key = os.environ['API_KEY']

# Good: Mask sensitive data in logs
logger.info("API request", extra={
    'url': url,
    'api_key': '***'  # Masked
})
```

2. **Input Validation**
```python
def process_metric(name: str, value: float) -> None:
    """Process a metric with validation."""
    if not isinstance(name, str):
        raise ValueError("Metric name must be a string")
    
    if not isinstance(value, (int, float)):
        raise ValueError("Metric value must be numeric")
    
    if value < 0:
        raise ValueError("Metric value cannot be negative")
```

### Code Organization

1. **Class Structure**
```python
class MetricCollector:
    """Collect and process system metrics."""
    
    def __init__(self, config: Dict[str, Any]):
        """Initialize collector with configuration."""
        self.config = config
        self.metrics = {}
    
    def collect(self) -> Dict[str, float]:
        """Collect all metrics."""
        return {
            'system': self._collect_system_metrics(),
            'application': self._collect_app_metrics()
        }
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Internal method for system metrics."""
        pass
```

2. **Module Organization**
```python
# monitoring/collectors/__init__.py
from .system import SystemCollector
from .application import ApplicationCollector

# monitoring/collectors/system.py
class SystemCollector:
    pass

# monitoring/collectors/application.py
class ApplicationCollector:
    pass
```

### Best Practices

1. **SOLID Principles**
```python
# Single Responsibility
class MetricCollector:
    """Only handles metric collection."""
    pass

class MetricProcessor:
    """Only handles metric processing."""
    pass

# Open/Closed
class BaseCollector(ABC):
    @abstractmethod
    def collect(self):
        pass

class CustomCollector(BaseCollector):
    def collect(self):
        pass
```

2. **DRY (Don't Repeat Yourself)**
```python
# Good: Reusable function
def validate_metric(name: str, value: float) -> None:
    """Validate metric name and value."""
    if not isinstance(name, str):
        raise ValueError("Invalid metric name")
    if not isinstance(value, (int, float)):
        raise ValueError("Invalid metric value")

# Use the validation function
def process_metric(name: str, value: float) -> None:
    validate_metric(name, value)
    # Process metric...

def store_metric(name: str, value: float) -> None:
    validate_metric(name, value)
    # Store metric...
```

### Tools

1. **Code Formatting**
```bash
# Format code
black monitoring/

# Sort imports
isort monitoring/
```

2. **Linting**
```bash
# Run linters
flake8 monitoring/
pylint monitoring/
mypy monitoring/
```

### Version Control

1. **Commit Messages**
```
# Format
<type>(<scope>): <subject>

# Examples
feat(metrics): add new system metrics collector
fix(alerts): resolve notification delay
docs(api): update API documentation
```

2. **Branch Names**
```
# Format
<type>/<description>

# Examples
feature/new-metric-collector
bugfix/alert-delay
docs/api-updates
```

### Documentation

1. **Code Documentation**
```python
def process_metrics(
    metrics: Dict[str, float],
    threshold: float = 0.0
) -> Dict[str, float]:
    """
    Process raw metrics and apply threshold.

    Args:
        metrics: Raw metric values
        threshold: Minimum value threshold

    Returns:
        Processed metrics

    Example:
        >>> process_metrics({'cpu': 50.0}, threshold=10.0)
        {'cpu': 50.0}
    """
    return {
        k: v for k, v in metrics.items()
        if v >= threshold
    }
```

2. **API Documentation**
```python
@app.route('/api/metrics', methods=['GET'])
def get_metrics():
    """
    Get system metrics.
    ---
    tags:
      - Metrics
    parameters:
      - name: timespan
        in: query
        type: string
        enum: [1h, 24h, 7d]
        default: 1h
    responses:
        200:
            description: Metrics retrieved successfully
    """
    pass
