# Terminusa Online Monitoring Development Guide

## Development Setup

### Prerequisites
```bash
# System requirements
Python 3.8+
Redis 6.0+
PostgreSQL 12+
Node.js 16+

# Clone repository
git clone https://github.com/terminusa/monitoring.git
cd monitoring

# Create virtual environment
python -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements-monitoring.txt
```

### Development Environment
```bash
# Environment variables
export FLASK_ENV=development
export FLASK_DEBUG=1
export MONITORING_CONFIG=config/monitoring_dev.py

# Start development server
python manage.py runserver

# Start monitoring services
python manage.py manage_monitoring start --dev
```

## Code Structure

### Project Layout
```
monitoring/
├── config/                 # Configuration files
├── docs/                  # Documentation
├── game_systems/          # Core monitoring systems
├── management/           # Management commands
├── models/              # Database models
├── routes/             # API routes
├── scripts/           # Utility scripts
├── static/           # Static assets
├── templates/       # HTML templates
└── tests/         # Test suite
```

### Core Components
```python
# Metric Collection
from game_systems.metric_collector import MetricCollector

class CustomMetricCollector(MetricCollector):
    def collect_custom_metrics(self):
        """Collect custom game metrics"""
        return {
            'active_players': self.get_active_players(),
            'active_wars': self.get_active_wars()
        }

# Alert Management
from game_systems.alert_manager import AlertManager

class CustomAlertManager(AlertManager):
    def define_custom_rules(self):
        """Define custom alert rules"""
        return {
            'high_player_count': {
                'threshold': 1000,
                'duration': 300
            }
        }
```

## Development Guidelines

### Code Style
```python
# Follow PEP 8 guidelines
def process_metrics(metrics: Dict[str, Any]) -> Dict[str, float]:
    """
    Process raw metrics into aggregated values.
    
    Args:
        metrics: Raw metric data
        
    Returns:
        Processed metrics
    """
    processed = {}
    for key, value in metrics.items():
        processed[key] = calculate_average(value)
    return processed
```

### Error Handling
```python
class MonitoringError(Exception):
    """Base class for monitoring exceptions"""
    pass

class MetricCollectionError(MonitoringError):
    """Raised when metric collection fails"""
    pass

def collect_metrics():
    try:
        metrics = collector.collect()
    except Exception as e:
        raise MetricCollectionError(f"Failed to collect metrics: {e}")
```

### Testing
```python
# Unit Tests
def test_metric_collection():
    collector = MetricCollector()
    metrics = collector.collect()
    assert 'cpu' in metrics
    assert 0 <= metrics['cpu'] <= 100

# Integration Tests
def test_alert_notification():
    alert_manager = AlertManager()
    alert = alert_manager.create_alert('test', 'critical')
    assert alert.notifications_sent > 0
```

## API Development

### Adding New Endpoints
```python
from flask import Blueprint, jsonify

monitoring_bp = Blueprint('monitoring', __name__)

@monitoring_bp.route('/api/monitoring/custom', methods=['GET'])
@require_auth
def get_custom_metrics():
    """Get custom monitoring metrics"""
    try:
        metrics = collector.get_custom_metrics()
        return jsonify({
            'success': True,
            'metrics': metrics
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

### WebSocket Development
```python
class MonitoringWebSocket:
    def __init__(self):
        self.clients = set()
        
    async def handle_connection(self, websocket):
        """Handle new WebSocket connection"""
        self.clients.add(websocket)
        try:
            await self.handle_messages(websocket)
        finally:
            self.clients.remove(websocket)
            
    async def broadcast_metrics(self, metrics):
        """Broadcast metrics to all clients"""
        message = json.dumps({
            'type': 'metrics',
            'data': metrics
        })
        await asyncio.gather(
            *[client.send(message) for client in self.clients]
        )
```

## Frontend Development

### Dashboard Components
```javascript
class MetricChart extends React.Component {
    state = {
        data: [],
        loading: true
    }
    
    componentDidMount() {
        this.startMetricCollection();
    }
    
    startMetricCollection() {
        const ws = new WebSocket('wss://terminusa.online/ws/monitoring');
        ws.onmessage = (event) => {
            const data = JSON.parse(event.data);
            this.updateChart(data);
        };
    }
    
    render() {
        return (
            <div className="metric-chart">
                <Chart data={this.state.data} />
            </div>
        );
    }
}
```

### Alert Components
```javascript
class AlertList extends React.Component {
    state = {
        alerts: [],
        filter: 'all'
    }
    
    async acknowledgeAlert(alertId) {
        await fetch(`/api/monitoring/alerts/${alertId}/acknowledge`, {
            method: 'POST',
            headers: {
                'Authorization': `Bearer ${this.props.token}`
            }
        });
    }
    
    render() {
        return (
            <div className="alert-list">
                {this.state.alerts.map(alert => (
                    <AlertItem
                        key={alert.id}
                        alert={alert}
                        onAcknowledge={this.acknowledgeAlert}
                    />
                ))}
            </div>
        );
    }
}
```

## Database Development

### Models
```python
from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.dialects.postgresql import JSONB

class Metric(Base):
    __tablename__ = 'metrics'
    
    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    timestamp = Column(DateTime, nullable=False)
    metadata = Column(JSONB)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'value': self.value,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
```

### Migrations
```python
"""Add metric metadata

Revision ID: abc123
"""

def upgrade():
    op.add_column('metrics',
        sa.Column('metadata', postgresql.JSONB(), nullable=True)
    )

def downgrade():
    op.drop_column('metrics', 'metadata')
```

## Extension Development

### Custom Collectors
```python
from game_systems.metric_collector import BaseCollector

class GameMetricCollector(BaseCollector):
    def collect(self):
        return {
            'players': self.collect_player_metrics(),
            'wars': self.collect_war_metrics(),
            'economy': self.collect_economy_metrics()
        }
        
    def collect_player_metrics(self):
        # Implementation
        pass
```

### Custom Alert Rules
```python
from game_systems.alert_rules import BaseRule

class PlayerCountRule(BaseRule):
    def evaluate(self, metrics):
        player_count = metrics.get('players.active', 0)
        if player_count > self.threshold:
            return self.create_alert(
                'High Player Count',
                f'Active players: {player_count}'
            )
```

## Performance Optimization

### Caching
```python
from functools import lru_cache
from datetime import timedelta

@lru_cache(maxsize=1000)
def get_aggregated_metrics(timespan: str) -> Dict:
    """Get aggregated metrics with caching"""
    return calculate_aggregates(
        get_raw_metrics(timespan)
    )

def invalidate_cache():
    """Invalidate metric cache"""
    get_aggregated_metrics.cache_clear()
```

### Batch Processing
```python
class MetricBatchProcessor:
    def __init__(self, batch_size=1000):
        self.batch_size = batch_size
        self.batch = []
        
    def add(self, metric):
        self.batch.append(metric)
        if len(self.batch) >= self.batch_size:
            self.process_batch()
            
    def process_batch(self):
        with db.session.begin():
            db.session.bulk_save_objects(self.batch)
        self.batch = []
```

## Documentation

### API Documentation
```python
@monitoring_bp.route('/api/monitoring/metrics', methods=['GET'])
def get_metrics():
    """
    Get system metrics.
    ---
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
```

### Code Documentation
```python
class MetricAggregator:
    """
    Aggregates raw metrics into statistical summaries.
    
    Attributes:
        window_size (int): Aggregation window in seconds
        functions (List[str]): Aggregation functions to apply
        
    Methods:
        aggregate(metrics: List[Dict]) -> Dict:
            Aggregate raw metrics into summary statistics
    """
    pass
```

## Deployment

### Development
```bash
# Start development services
./scripts/start_dev.sh

# Run development checks
./scripts/check_dev.sh
```

### Production
```bash
# Build production assets
./scripts/build_prod.sh

# Deploy monitoring system
./scripts/deploy_monitoring.sh
```

## Support

### Resources
- Documentation: /docs/
- API Reference: /docs/api.md
- Architecture: /docs/architecture.md
- Examples: /examples/

### Contact
- GitHub Issues: github.com/terminusa/monitoring/issues
- Email: dev@terminusa.online
- Discord: #monitoring-dev
