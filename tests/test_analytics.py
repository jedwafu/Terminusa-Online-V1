import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import json
import pandas as pd
import numpy as np
from collections import defaultdict

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AnalyticsType(Enum):
    """Types of analytics"""
    USER_BEHAVIOR = auto()
    GAME_ECONOMY = auto()
    PLAYER_PROGRESSION = auto()
    SOCIAL_INTERACTION = auto()
    COMBAT_STATS = auto()
    SYSTEM_PERFORMANCE = auto()

@dataclass
class AnalyticsData:
    """Analytics data point"""
    type: AnalyticsType
    timestamp: datetime
    user_id: Optional[int]
    data: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None

class AnalyticsSystem:
    """System for game analytics"""
    def __init__(self, storage_dir: str = 'analytics'):
        self.storage_dir = storage_dir
        os.makedirs(storage_dir, exist_ok=True)
        self.data: Dict[AnalyticsType, List[AnalyticsData]] = defaultdict(list)
        self.cached_analysis: Dict[str, Any] = {}
        self.cache_timeout = timedelta(minutes=5)

    def track(
        self,
        type: AnalyticsType,
        data: Dict[str, Any],
        user_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Track analytics data"""
        analytics = AnalyticsData(
            type=type,
            timestamp=datetime.utcnow(),
            user_id=user_id,
            data=data,
            metadata=metadata
        )
        
        self.data[type].append(analytics)
        self._save_data(analytics)

    def analyze(
        self,
        type: AnalyticsType,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        metrics: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Analyze analytics data"""
        # Check cache
        cache_key = f"{type.name}_{start_time}_{end_time}_{metrics}"
        if cache_key in self.cached_analysis:
            cache_time, result = self.cached_analysis[cache_key]
            if datetime.utcnow() - cache_time < self.cache_timeout:
                return result
        
        # Filter data
        data = self.data[type]
        if start_time:
            data = [d for d in data if d.timestamp >= start_time]
        if end_time:
            data = [d for d in data if d.timestamp <= end_time]
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {**{'timestamp': d.timestamp, 'user_id': d.user_id}, **d.data}
            for d in data
        ])
        
        # Calculate metrics
        result = {}
        if not metrics:
            metrics = ['count', 'mean', 'median', 'min', 'max']
        
        for column in df.select_dtypes(include=[np.number]).columns:
            if 'count' in metrics:
                result[f'{column}_count'] = len(df)
            if 'mean' in metrics:
                result[f'{column}_mean'] = df[column].mean()
            if 'median' in metrics:
                result[f'{column}_median'] = df[column].median()
            if 'min' in metrics:
                result[f'{column}_min'] = df[column].min()
            if 'max' in metrics:
                result[f'{column}_max'] = df[column].max()
        
        # Cache result
        self.cached_analysis[cache_key] = (datetime.utcnow(), result)
        
        return result

    def get_user_metrics(
        self,
        user_id: int,
        type: Optional[AnalyticsType] = None
    ) -> Dict[str, Any]:
        """Get metrics for specific user"""
        metrics = {}
        
        # Filter data
        data = []
        for t, entries in self.data.items():
            if type and t != type:
                continue
            data.extend([d for d in entries if d.user_id == user_id])
        
        if not data:
            return metrics
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {**{'timestamp': d.timestamp, 'type': d.type.name}, **d.data}
            for d in data
        ])
        
        # Calculate metrics
        for column in df.select_dtypes(include=[np.number]).columns:
            metrics[f'{column}_total'] = df[column].sum()
            metrics[f'{column}_average'] = df[column].mean()
            metrics[f'{column}_max'] = df[column].max()
        
        return metrics

    def get_trends(
        self,
        type: AnalyticsType,
        metric: str,
        interval: str = 'D'
    ) -> Dict[str, float]:
        """Get trends over time"""
        data = self.data[type]
        if not data:
            return {}
        
        # Convert to DataFrame
        df = pd.DataFrame([
            {**{'timestamp': d.timestamp}, **d.data}
            for d in data if metric in d.data
        ])
        
        # Resample and calculate means
        df.set_index('timestamp', inplace=True)
        trends = df[metric].resample(interval).mean()
        
        return trends.to_dict()

    def export_data(
        self,
        type: AnalyticsType,
        format: str = 'json'
    ) -> str:
        """Export analytics data"""
        data = [
            {
                'timestamp': d.timestamp.isoformat(),
                'user_id': d.user_id,
                'data': d.data,
                'metadata': d.metadata
            }
            for d in self.data[type]
        ]
        
        if format == 'json':
            return json.dumps(data, indent=2)
        elif format == 'csv':
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _save_data(self, analytics: AnalyticsData):
        """Save analytics data to file"""
        file_path = os.path.join(
            self.storage_dir,
            f"{analytics.type.name.lower()}_{analytics.timestamp.date()}.json"
        )
        
        data = {
            'timestamp': analytics.timestamp.isoformat(),
            'user_id': analytics.user_id,
            'data': analytics.data,
            'metadata': analytics.metadata
        }
        
        mode = 'a' if os.path.exists(file_path) else 'w'
        with open(file_path, mode) as f:
            if mode == 'a':
                f.write('\n')
            json.dump(data, f)

class TestAnalytics(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.analytics = AnalyticsSystem('test_analytics')

    def tearDown(self):
        """Clean up after each test"""
        import shutil
        if os.path.exists('test_analytics'):
            shutil.rmtree('test_analytics')

    def test_basic_tracking(self):
        """Test basic analytics tracking"""
        # Track data
        self.analytics.track(
            AnalyticsType.USER_BEHAVIOR,
            {'action': 'login', 'duration': 60},
            user_id=1
        )
        
        # Verify tracking
        data = self.analytics.data[AnalyticsType.USER_BEHAVIOR]
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0].user_id, 1)
        self.assertEqual(data[0].data['duration'], 60)

    def test_data_analysis(self):
        """Test data analysis"""
        # Track multiple data points
        for i in range(5):
            self.analytics.track(
                AnalyticsType.GAME_ECONOMY,
                {'crystals': i * 100},
                user_id=1
            )
        
        # Analyze data
        analysis = self.analytics.analyze(
            AnalyticsType.GAME_ECONOMY,
            metrics=['mean', 'max']
        )
        
        # Verify analysis
        self.assertEqual(analysis['crystals_mean'], 200)
        self.assertEqual(analysis['crystals_max'], 400)

    def test_user_metrics(self):
        """Test user-specific metrics"""
        # Track data for different users
        for user_id in [1, 2]:
            self.analytics.track(
                AnalyticsType.PLAYER_PROGRESSION,
                {'experience': 100},
                user_id=user_id
            )
        
        # Get metrics for user
        metrics = self.analytics.get_user_metrics(1)
        
        # Verify metrics
        self.assertEqual(metrics['experience_total'], 100)
        self.assertEqual(metrics['experience_average'], 100)

    def test_trend_analysis(self):
        """Test trend analysis"""
        # Track data over time
        now = datetime.utcnow()
        for i in range(3):
            with patch('datetime.datetime') as mock_datetime:
                mock_datetime.utcnow.return_value = now + timedelta(days=i)
                self.analytics.track(
                    AnalyticsType.COMBAT_STATS,
                    {'damage': 100 * (i + 1)}
                )
        
        # Get trends
        trends = self.analytics.get_trends(
            AnalyticsType.COMBAT_STATS,
            'damage',
            'D'
        )
        
        # Verify trends
        self.assertEqual(len(trends), 3)
        self.assertTrue(all(v > 0 for v in trends.values()))

    def test_data_export(self):
        """Test data export"""
        # Track some data
        self.analytics.track(
            AnalyticsType.SYSTEM_PERFORMANCE,
            {'cpu_usage': 50, 'memory_usage': 1024}
        )
        
        # Export as JSON
        json_data = self.analytics.export_data(
            AnalyticsType.SYSTEM_PERFORMANCE,
            'json'
        )
        
        # Export as CSV
        csv_data = self.analytics.export_data(
            AnalyticsType.SYSTEM_PERFORMANCE,
            'csv'
        )
        
        # Verify exports
        self.assertIn('cpu_usage', json_data)
        self.assertIn('cpu_usage', csv_data)

    def test_analysis_caching(self):
        """Test analysis result caching"""
        # Track data
        self.analytics.track(
            AnalyticsType.SOCIAL_INTERACTION,
            {'messages': 10},
            user_id=1
        )
        
        # Perform analysis
        first_analysis = self.analytics.analyze(
            AnalyticsType.SOCIAL_INTERACTION
        )
        
        # Add more data
        self.analytics.track(
            AnalyticsType.SOCIAL_INTERACTION,
            {'messages': 20},
            user_id=1
        )
        
        # Get cached analysis
        cached_analysis = self.analytics.analyze(
            AnalyticsType.SOCIAL_INTERACTION
        )
        
        # Should be same as first analysis
        self.assertEqual(first_analysis, cached_analysis)

    def test_time_filtering(self):
        """Test time-based filtering"""
        now = datetime.utcnow()
        
        # Track data at different times
        with patch('datetime.datetime') as mock_datetime:
            # Yesterday's data
            mock_datetime.utcnow.return_value = now - timedelta(days=1)
            self.analytics.track(
                AnalyticsType.USER_BEHAVIOR,
                {'action': 'old'}
            )
            
            # Today's data
            mock_datetime.utcnow.return_value = now
            self.analytics.track(
                AnalyticsType.USER_BEHAVIOR,
                {'action': 'new'}
            )
        
        # Analyze recent data
        analysis = self.analytics.analyze(
            AnalyticsType.USER_BEHAVIOR,
            start_time=now - timedelta(hours=1)
        )
        
        self.assertEqual(analysis['count'], 1)

    def test_metadata_handling(self):
        """Test metadata handling"""
        metadata = {
            'client_version': '1.0.0',
            'platform': 'desktop'
        }
        
        # Track with metadata
        self.analytics.track(
            AnalyticsType.SYSTEM_PERFORMANCE,
            {'cpu_usage': 50},
            metadata=metadata
        )
        
        # Verify metadata in export
        export = json.loads(self.analytics.export_data(
            AnalyticsType.SYSTEM_PERFORMANCE
        ))
        
        self.assertEqual(
            export[0]['metadata']['client_version'],
            '1.0.0'
        )

if __name__ == '__main__':
    unittest.main()
