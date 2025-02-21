import logging
import asyncio
import psutil
import redis
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from collections import defaultdict

from config.monitoring import METRIC_CONFIG
from game_systems.alert_manager import AlertManager, AlertSeverity
from game_systems.metric_collector import MetricCollector

logger = logging.getLogger(__name__)

class MonitoringImprovements:
    def __init__(self, alert_manager: AlertManager, metric_collector: MetricCollector):
        self.alert_manager = alert_manager
        self.metric_collector = metric_collector
        self.trend_analyzer = TrendAnalyzer()
        self.anomaly_detector = AnomalyDetector()
        self.predictive_alerts = PredictiveAlerts()
        self.performance_optimizer = PerformanceOptimizer()

    async def start(self):
        """Start monitoring improvements"""
        try:
            await asyncio.gather(
                self.trend_analyzer.start(),
                self.anomaly_detector.start(),
                self.predictive_alerts.start(),
                self.performance_optimizer.start()
            )
        except Exception as e:
            logger.error(f"Failed to start monitoring improvements: {e}")
            raise

class TrendAnalyzer:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0
        )
        self.window_sizes = {
            'short': timedelta(hours=1),
            'medium': timedelta(days=1),
            'long': timedelta(days=7)
        }

    async def start(self):
        """Start trend analysis"""
        try:
            while True:
                await self.analyze_trends()
                await asyncio.sleep(300)  # Every 5 minutes
        except Exception as e:
            logger.error(f"Trend analysis failed: {e}")
            raise

    async def analyze_trends(self):
        """Analyze metric trends"""
        try:
            metrics = self.get_metrics()
            trends = {}

            for metric_type, data in metrics.items():
                trends[metric_type] = {
                    'short': self.calculate_trend(data, self.window_sizes['short']),
                    'medium': self.calculate_trend(data, self.window_sizes['medium']),
                    'long': self.calculate_trend(data, self.window_sizes['long'])
                }

            self.store_trends(trends)
            await self.alert_significant_trends(trends)

        except Exception as e:
            logger.error(f"Failed to analyze trends: {e}")

    def calculate_trend(self, data: List[Dict], window: timedelta) -> Dict:
        """Calculate trend for given window"""
        try:
            window_data = [
                d for d in data
                if datetime.utcnow() - datetime.fromisoformat(d['timestamp']) <= window
            ]

            if not window_data:
                return {'slope': 0, 'correlation': 0}

            values = [d['value'] for d in window_data]
            times = range(len(values))

            # Calculate linear regression
            import numpy as np
            slope, intercept = np.polyfit(times, values, 1)
            correlation = np.corrcoef(times, values)[0, 1]

            return {
                'slope': slope,
                'correlation': correlation
            }

        except Exception as e:
            logger.error(f"Trend calculation failed: {e}")
            return {'slope': 0, 'correlation': 0}

class AnomalyDetector:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0
        )
        self.detection_config = {
            'z_score_threshold': 3.0,
            'min_samples': 30,
            'learning_rate': 0.1
        }

    async def start(self):
        """Start anomaly detection"""
        try:
            while True:
                await self.detect_anomalies()
                await asyncio.sleep(60)  # Every minute
        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")
            raise

    async def detect_anomalies(self):
        """Detect metric anomalies"""
        try:
            metrics = self.get_recent_metrics()
            baselines = self.get_baselines()

            anomalies = {}
            for metric_type, values in metrics.items():
                baseline = baselines.get(metric_type, {})
                anomalies[metric_type] = self.check_anomalies(values, baseline)

            self.update_baselines(metrics, baselines)
            await self.alert_anomalies(anomalies)

        except Exception as e:
            logger.error(f"Anomaly detection failed: {e}")

    def check_anomalies(self, values: List[float], baseline: Dict) -> List[Dict]:
        """Check for anomalies in values"""
        try:
            import numpy as np
            
            if len(values) < self.detection_config['min_samples']:
                return []

            mean = baseline.get('mean', np.mean(values))
            std = baseline.get('std', np.std(values))

            z_scores = np.abs((values - mean) / std)
            anomalies = []

            for i, z_score in enumerate(z_scores):
                if z_score > self.detection_config['z_score_threshold']:
                    anomalies.append({
                        'index': i,
                        'value': values[i],
                        'z_score': z_score
                    })

            return anomalies

        except Exception as e:
            logger.error(f"Anomaly check failed: {e}")
            return []

class PredictiveAlerts:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0
        )
        self.prediction_config = {
            'forecast_hours': 24,
            'confidence_threshold': 0.8,
            'min_samples': 100
        }

    async def start(self):
        """Start predictive alerting"""
        try:
            while True:
                await self.predict_issues()
                await asyncio.sleep(3600)  # Every hour
        except Exception as e:
            logger.error(f"Predictive alerting failed: {e}")
            raise

    async def predict_issues(self):
        """Predict potential issues"""
        try:
            metrics = self.get_historical_metrics()
            predictions = {}

            for metric_type, data in metrics.items():
                if len(data) >= self.prediction_config['min_samples']:
                    predictions[metric_type] = self.forecast_metric(data)

            await self.alert_predictions(predictions)

        except Exception as e:
            logger.error(f"Issue prediction failed: {e}")

    def forecast_metric(self, data: List[Dict]) -> Dict:
        """Forecast metric values"""
        try:
            from sklearn.ensemble import RandomForestRegressor
            import numpy as np

            X = np.array(range(len(data))).reshape(-1, 1)
            y = np.array([d['value'] for d in data])

            model = RandomForestRegressor(n_estimators=100)
            model.fit(X, y)

            future_X = np.array(range(
                len(data),
                len(data) + self.prediction_config['forecast_hours']
            )).reshape(-1, 1)

            predictions = model.predict(future_X)
            confidence = model.score(X, y)

            return {
                'predictions': predictions.tolist(),
                'confidence': confidence
            }

        except Exception as e:
            logger.error(f"Metric forecast failed: {e}")
            return {'predictions': [], 'confidence': 0}

class PerformanceOptimizer:
    def __init__(self):
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=0
        )
        self.optimization_config = {
            'metric_retention': {
                'raw': 86400,      # 1 day
                'hourly': 604800,  # 7 days
                'daily': 2592000   # 30 days
            },
            'compression_threshold': 1000000,  # 1MB
            'batch_size': 1000
        }

    async def start(self):
        """Start performance optimization"""
        try:
            while True:
                await self.optimize_storage()
                await self.optimize_queries()
                await asyncio.sleep(3600)  # Every hour
        except Exception as e:
            logger.error(f"Performance optimization failed: {e}")
            raise

    async def optimize_storage(self):
        """Optimize metric storage"""
        try:
            # Aggregate old metrics
            await self.aggregate_metrics()

            # Compress large metrics
            await self.compress_metrics()

            # Clean up old metrics
            await self.cleanup_metrics()

        except Exception as e:
            logger.error(f"Storage optimization failed: {e}")

    async def optimize_queries(self):
        """Optimize metric queries"""
        try:
            # Cache frequently accessed metrics
            await self.cache_hot_metrics()

            # Optimize query patterns
            await self.optimize_query_patterns()

        except Exception as e:
            logger.error(f"Query optimization failed: {e}")

    async def aggregate_metrics(self):
        """Aggregate old metrics into summaries"""
        try:
            for retention_type, ttl in self.optimization_config['metric_retention'].items():
                pattern = f"metrics:{retention_type}:*"
                keys = self.redis_client.keys(pattern)

                for i in range(0, len(keys), self.optimization_config['batch_size']):
                    batch = keys[i:i + self.optimization_config['batch_size']]
                    values = [
                        json.loads(v) for v in self.redis_client.mget(batch)
                        if v is not None
                    ]

                    if values:
                        summary = self.create_summary(values)
                        summary_key = f"metrics:summary:{retention_type}:{datetime.utcnow().isoformat()}"
                        self.redis_client.setex(
                            summary_key,
                            ttl,
                            json.dumps(summary)
                        )

                        # Delete original metrics
                        self.redis_client.delete(*batch)

        except Exception as e:
            logger.error(f"Metric aggregation failed: {e}")

    def create_summary(self, values: List[Dict]) -> Dict:
        """Create metric summary"""
        try:
            import numpy as np

            summary = defaultdict(dict)
            for value in values:
                for metric, data in value.items():
                    if isinstance(data, (int, float)):
                        if metric not in summary:
                            summary[metric] = []
                        summary[metric].append(data)

            # Calculate statistics
            for metric, data in summary.items():
                summary[metric] = {
                    'mean': float(np.mean(data)),
                    'min': float(np.min(data)),
                    'max': float(np.max(data)),
                    'std': float(np.std(data)),
                    'count': len(data)
                }

            return dict(summary)

        except Exception as e:
            logger.error(f"Summary creation failed: {e}")
            return {}

    async def compress_metrics(self):
        """Compress large metric values"""
        try:
            import zlib

            pattern = "metrics:*"
            keys = self.redis_client.keys(pattern)

            for key in keys:
                value = self.redis_client.get(key)
                if value and len(value) > self.optimization_config['compression_threshold']:
                    compressed = zlib.compress(value)
                    self.redis_client.set(f"{key}:compressed", compressed)
                    self.redis_client.delete(key)

        except Exception as e:
            logger.error(f"Metric compression failed: {e}")

    async def cache_hot_metrics(self):
        """Cache frequently accessed metrics"""
        try:
            # Identify hot metrics
            hot_metrics = self.identify_hot_metrics()

            # Pre-calculate common aggregations
            for metric in hot_metrics:
                self.precalculate_aggregations(metric)

        except Exception as e:
            logger.error(f"Metric caching failed: {e}")

    def identify_hot_metrics(self) -> List[str]:
        """Identify frequently accessed metrics"""
        try:
            # Analyze access patterns
            access_logs = self.get_access_logs()
            
            # Count metric access frequency
            frequency = defaultdict(int)
            for log in access_logs:
                frequency[log['metric']] += 1

            # Return top accessed metrics
            return sorted(
                frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]

        except Exception as e:
            logger.error(f"Hot metric identification failed: {e}")
            return []

    def precalculate_aggregations(self, metric: str):
        """Pre-calculate common metric aggregations"""
        try:
            # Get metric values
            values = self.get_metric_values(metric)

            # Calculate common aggregations
            aggregations = {
                'hourly': self.aggregate_by_hour(values),
                'daily': self.aggregate_by_day(values),
                'weekly': self.aggregate_by_week(values)
            }

            # Cache aggregations
            for agg_type, agg_values in aggregations.items():
                cache_key = f"cache:aggregation:{metric}:{agg_type}"
                self.redis_client.setex(
                    cache_key,
                    3600,  # 1 hour
                    json.dumps(agg_values)
                )

        except Exception as e:
            logger.error(f"Aggregation pre-calculation failed: {e}")
