import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum, auto
import json
import redis
import statistics

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class MetricType(Enum):
    """Types of metrics"""
    COUNTER = auto()
    GAUGE = auto()
    HISTOGRAM = auto()
    SUMMARY = auto()

class MetricCategory(Enum):
    """Metric categories"""
    PERFORMANCE = auto()
    GAMEPLAY = auto()
    ECONOMY = auto()
    SOCIAL = auto()
    SYSTEM = auto()

@dataclass
class MetricValue:
    """Metric value data"""
    value: float
    timestamp: datetime
    labels: Dict[str, str]

class MetricsSystem:
    """Game metrics and analytics system"""
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        self.redis = redis.from_url(redis_url)
        self.retention_days = 30

    def track_metric(
        self,
        name: str,
        value: float,
        metric_type: MetricType,
        category: MetricCategory,
        labels: Optional[Dict[str, str]] = None
    ):
        """Track a metric value"""
        metric = MetricValue(
            value=value,
            timestamp=datetime.utcnow(),
            labels=labels or {}
        )
        
        key = f"metric:{category.name}:{name}"
        data = {
            'value': value,
            'timestamp': metric.timestamp.isoformat(),
            'type': metric_type.name,
            'labels': metric.labels
        }
        
        # Store in time series
        self.redis.zadd(key, {json.dumps(data): metric.timestamp.timestamp()})
        
        # Cleanup old data
        cutoff = datetime.utcnow() - timedelta(days=self.retention_days)
        self.redis.zremrangebyscore(key, '-inf', cutoff.timestamp())

    def get_metric(
        self,
        name: str,
        category: MetricCategory,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        labels: Optional[Dict[str, str]] = None
    ) -> List[MetricValue]:
        """Get metric values"""
        key = f"metric:{category.name}:{name}"
        
        # Set time range
        min_score = start_time.timestamp() if start_time else '-inf'
        max_score = end_time.timestamp() if end_time else '+inf'
        
        # Get values
        data = self.redis.zrangebyscore(
            key,
            min_score,
            max_score,
            withscores=True
        )
        
        metrics = []
        for value_json, _ in data:
            value_data = json.loads(value_json)
            
            # Filter by labels
            if labels:
                if not all(
                    value_data['labels'].get(k) == v
                    for k, v in labels.items()
                ):
                    continue
            
            metric = MetricValue(
                value=value_data['value'],
                timestamp=datetime.fromisoformat(value_data['timestamp']),
                labels=value_data['labels']
            )
            metrics.append(metric)
        
        return metrics

    def get_stats(
        self,
        name: str,
        category: MetricCategory,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, float]:
        """Get statistical analysis of metric"""
        values = self.get_metric(name, category, start_time, end_time)
        if not values:
            return {
                'count': 0,
                'min': 0,
                'max': 0,
                'mean': 0,
                'median': 0,
                'stddev': 0
            }
        
        numbers = [v.value for v in values]
        return {
            'count': len(numbers),
            'min': min(numbers),
            'max': max(numbers),
            'mean': statistics.mean(numbers),
            'median': statistics.median(numbers),
            'stddev': statistics.stdev(numbers) if len(numbers) > 1 else 0
        }

    def get_histogram(
        self,
        name: str,
        category: MetricCategory,
        bins: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> Dict[str, int]:
        """Get histogram of metric values"""
        values = self.get_metric(name, category, start_time, end_time)
        if not values:
            return {}
        
        numbers = [v.value for v in values]
        min_val = min(numbers)
        max_val = max(numbers)
        bin_size = (max_val - min_val) / bins if max_val > min_val else 1
        
        histogram = {}
        for i in range(bins):
            bin_min = min_val + (i * bin_size)
            bin_max = min_val + ((i + 1) * bin_size)
            bin_name = f"{bin_min:.2f}-{bin_max:.2f}"
            histogram[bin_name] = sum(
                1 for v in numbers
                if bin_min <= v < bin_max
            )
        
        return histogram

    def get_top_values(
        self,
        name: str,
        category: MetricCategory,
        limit: int = 10,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """Get top metric values with labels"""
        values = self.get_metric(name, category, start_time, end_time)
        
        sorted_values = sorted(
            values,
            key=lambda x: x.value,
            reverse=True
        )
        
        return [
            {
                'value': v.value,
                'timestamp': v.timestamp,
                'labels': v.labels
            }
            for v in sorted_values[:limit]
        ]

class TestMetrics(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.metrics = MetricsSystem()
        
        # Clear existing data
        self.metrics.redis.flushall()

    def test_basic_tracking(self):
        """Test basic metric tracking"""
        # Track metric
        self.metrics.track_metric(
            'test_metric',
            100,
            MetricType.COUNTER,
            MetricCategory.GAMEPLAY
        )
        
        # Get metric
        values = self.metrics.get_metric(
            'test_metric',
            MetricCategory.GAMEPLAY
        )
        
        # Verify tracking
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0].value, 100)

    def test_labeled_metrics(self):
        """Test metrics with labels"""
        # Track metrics with different labels
        self.metrics.track_metric(
            'player_score',
            100,
            MetricType.GAUGE,
            MetricCategory.GAMEPLAY,
            {'player_id': '1', 'level': '10'}
        )
        
        self.metrics.track_metric(
            'player_score',
            200,
            MetricType.GAUGE,
            MetricCategory.GAMEPLAY,
            {'player_id': '2', 'level': '20'}
        )
        
        # Get metrics filtered by label
        values = self.metrics.get_metric(
            'player_score',
            MetricCategory.GAMEPLAY,
            labels={'player_id': '1'}
        )
        
        # Verify filtering
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0].value, 100)

    def test_time_range_filtering(self):
        """Test time range filtering"""
        # Track metrics at different times
        now = datetime.utcnow()
        
        with patch('datetime.datetime') as mock_datetime:
            # Yesterday's metric
            mock_datetime.utcnow.return_value = now - timedelta(days=1)
            self.metrics.track_metric(
                'daily_metric',
                100,
                MetricType.COUNTER,
                MetricCategory.GAMEPLAY
            )
            
            # Today's metric
            mock_datetime.utcnow.return_value = now
            self.metrics.track_metric(
                'daily_metric',
                200,
                MetricType.COUNTER,
                MetricCategory.GAMEPLAY
            )
        
        # Get today's metrics
        values = self.metrics.get_metric(
            'daily_metric',
            MetricCategory.GAMEPLAY,
            start_time=now - timedelta(hours=1)
        )
        
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0].value, 200)

    def test_statistical_analysis(self):
        """Test statistical analysis"""
        # Track multiple values
        values = [10, 20, 30, 40, 50]
        for value in values:
            self.metrics.track_metric(
                'stats_metric',
                value,
                MetricType.HISTOGRAM,
                MetricCategory.GAMEPLAY
            )
        
        # Get stats
        stats = self.metrics.get_stats(
            'stats_metric',
            MetricCategory.GAMEPLAY
        )
        
        # Verify stats
        self.assertEqual(stats['count'], 5)
        self.assertEqual(stats['min'], 10)
        self.assertEqual(stats['max'], 50)
        self.assertEqual(stats['mean'], 30)
        self.assertEqual(stats['median'], 30)

    def test_histogram(self):
        """Test histogram generation"""
        # Track values
        values = list(range(0, 100, 10))  # 0, 10, 20, ..., 90
        for value in values:
            self.metrics.track_metric(
                'histogram_metric',
                value,
                MetricType.HISTOGRAM,
                MetricCategory.GAMEPLAY
            )
        
        # Get histogram with 5 bins
        histogram = self.metrics.get_histogram(
            'histogram_metric',
            MetricCategory.GAMEPLAY,
            bins=5
        )
        
        # Verify bins
        self.assertEqual(len(histogram), 5)
        total_count = sum(histogram.values())
        self.assertEqual(total_count, len(values))

    def test_top_values(self):
        """Test top values retrieval"""
        # Track values with labels
        for i in range(5):
            self.metrics.track_metric(
                'top_metric',
                i * 10,
                MetricType.GAUGE,
                MetricCategory.GAMEPLAY,
                {'id': str(i)}
            )
        
        # Get top 3 values
        top_values = self.metrics.get_top_values(
            'top_metric',
            MetricCategory.GAMEPLAY,
            limit=3
        )
        
        # Verify order and count
        self.assertEqual(len(top_values), 3)
        self.assertEqual(top_values[0]['value'], 40)
        self.assertEqual(top_values[0]['labels']['id'], '4')

    def test_data_retention(self):
        """Test data retention"""
        # Set short retention
        self.metrics.retention_days = 1
        
        # Track old metric
        with patch('datetime.datetime') as mock_datetime:
            old_time = datetime.utcnow() - timedelta(days=2)
            mock_datetime.utcnow.return_value = old_time
            
            self.metrics.track_metric(
                'retention_metric',
                100,
                MetricType.COUNTER,
                MetricCategory.GAMEPLAY
            )
        
        # Track new metric
        self.metrics.track_metric(
            'retention_metric',
            200,
            MetricType.COUNTER,
            MetricCategory.GAMEPLAY
        )
        
        # Verify only new metric exists
        values = self.metrics.get_metric(
            'retention_metric',
            MetricCategory.GAMEPLAY
        )
        self.assertEqual(len(values), 1)
        self.assertEqual(values[0].value, 200)

    def test_multiple_categories(self):
        """Test metrics in different categories"""
        categories = {
            MetricCategory.GAMEPLAY: 100,
            MetricCategory.ECONOMY: 200,
            MetricCategory.SYSTEM: 300
        }
        
        # Track metrics in different categories
        for category, value in categories.items():
            self.metrics.track_metric(
                'category_metric',
                value,
                MetricType.GAUGE,
                category
            )
        
        # Verify each category
        for category, expected_value in categories.items():
            values = self.metrics.get_metric(
                'category_metric',
                category
            )
            self.assertEqual(len(values), 1)
            self.assertEqual(values[0].value, expected_value)

    def test_empty_metrics(self):
        """Test handling of empty metrics"""
        # Get non-existent metric
        values = self.metrics.get_metric(
            'nonexistent',
            MetricCategory.GAMEPLAY
        )
        self.assertEqual(len(values), 0)
        
        # Get stats for empty metric
        stats = self.metrics.get_stats(
            'nonexistent',
            MetricCategory.GAMEPLAY
        )
        self.assertEqual(stats['count'], 0)
        
        # Get histogram for empty metric
        histogram = self.metrics.get_histogram(
            'nonexistent',
            MetricCategory.GAMEPLAY
        )
        self.assertEqual(len(histogram), 0)

if __name__ == '__main__':
    unittest.main()
