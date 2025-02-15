import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class StatCategory(Enum):
    """Statistic categories"""
    COMBAT = auto()
    ECONOMY = auto()
    SOCIAL = auto()
    PROGRESSION = auto()
    ACHIEVEMENTS = auto()
    ITEMS = auto()
    TIME = auto()
    GATES = auto()

@dataclass
class StatisticValue:
    """Statistic value with metadata"""
    value: Any
    timestamp: datetime
    increment: bool = True  # True for cumulative stats, False for current value

@dataclass
class TimeSpan:
    """Time span for statistics"""
    daily: Dict[str, Any]
    weekly: Dict[str, Any]
    monthly: Dict[str, Any]
    all_time: Dict[str, Any]

class StatisticsSystem:
    """Manages game statistics"""
    def __init__(self):
        self.stats: Dict[int, Dict[StatCategory, Dict[str, List[StatisticValue]]]] = {}
        self.global_stats: Dict[StatCategory, Dict[str, List[StatisticValue]]] = {}

    def track_stat(
        self,
        user_id: int,
        category: StatCategory,
        stat_name: str,
        value: Any,
        increment: bool = True
    ):
        """Track a statistic"""
        # Initialize structures if needed
        if user_id not in self.stats:
            self.stats[user_id] = {}
        if category not in self.stats[user_id]:
            self.stats[user_id][category] = {}
        if stat_name not in self.stats[user_id][category]:
            self.stats[user_id][category][stat_name] = []
        
        # Add stat
        stat = StatisticValue(
            value=value,
            timestamp=datetime.utcnow(),
            increment=increment
        )
        self.stats[user_id][category][stat_name].append(stat)
        
        # Update global stats
        if category not in self.global_stats:
            self.global_stats[category] = {}
        if stat_name not in self.global_stats[category]:
            self.global_stats[category][stat_name] = []
        
        self.global_stats[category][stat_name].append(stat)

    def get_stat(
        self,
        user_id: int,
        category: StatCategory,
        stat_name: str,
        timespan: Optional[timedelta] = None
    ) -> Any:
        """Get current value of a statistic"""
        if user_id not in self.stats:
            return 0
        if category not in self.stats[user_id]:
            return 0
        if stat_name not in self.stats[user_id][category]:
            return 0
        
        stats = self.stats[user_id][category][stat_name]
        if not stats:
            return 0
        
        if timespan:
            cutoff = datetime.utcnow() - timespan
            stats = [s for s in stats if s.timestamp >= cutoff]
        
        if not stats:
            return 0
        
        if stats[0].increment:
            return sum(s.value for s in stats)
        else:
            return stats[-1].value

    def get_stats_summary(
        self,
        user_id: int,
        category: StatCategory
    ) -> TimeSpan:
        """Get statistics summary for different time periods"""
        now = datetime.utcnow()
        
        return TimeSpan(
            daily=self._get_stats_for_period(
                user_id,
                category,
                now - timedelta(days=1)
            ),
            weekly=self._get_stats_for_period(
                user_id,
                category,
                now - timedelta(weeks=1)
            ),
            monthly=self._get_stats_for_period(
                user_id,
                category,
                now - timedelta(days=30)
            ),
            all_time=self._get_stats_for_period(
                user_id,
                category
            )
        )

    def get_global_stat(
        self,
        category: StatCategory,
        stat_name: str,
        timespan: Optional[timedelta] = None
    ) -> Any:
        """Get global statistic value"""
        if category not in self.global_stats:
            return 0
        if stat_name not in self.global_stats[category]:
            return 0
        
        stats = self.global_stats[category][stat_name]
        if not stats:
            return 0
        
        if timespan:
            cutoff = datetime.utcnow() - timespan
            stats = [s for s in stats if s.timestamp >= cutoff]
        
        if not stats:
            return 0
        
        if stats[0].increment:
            return sum(s.value for s in stats)
        else:
            return stats[-1].value

    def get_leaderboard(
        self,
        category: StatCategory,
        stat_name: str,
        limit: int = 10,
        timespan: Optional[timedelta] = None
    ) -> List[Dict[str, Any]]:
        """Get leaderboard for a statistic"""
        leaderboard = []
        
        for user_id in self.stats:
            value = self.get_stat(user_id, category, stat_name, timespan)
            leaderboard.append({
                'user_id': user_id,
                'value': value
            })
        
        return sorted(
            leaderboard,
            key=lambda x: x['value'],
            reverse=True
        )[:limit]

    def _get_stats_for_period(
        self,
        user_id: int,
        category: StatCategory,
        start_time: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get all stats for a category within time period"""
        if user_id not in self.stats:
            return {}
        if category not in self.stats[user_id]:
            return {}
        
        result = {}
        for stat_name, stats in self.stats[user_id][category].items():
            if start_time:
                stats = [s for s in stats if s.timestamp >= start_time]
            
            if stats:
                if stats[0].increment:
                    result[stat_name] = sum(s.value for s in stats)
                else:
                    result[stat_name] = stats[-1].value
            else:
                result[stat_name] = 0
        
        return result

class TestStatistics(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.stats_system = StatisticsSystem()
        self.test_user_id = 1

    def test_basic_stat_tracking(self):
        """Test basic statistic tracking"""
        # Track a stat
        self.stats_system.track_stat(
            self.test_user_id,
            StatCategory.COMBAT,
            'monsters_killed',
            5
        )
        
        # Get stat value
        value = self.stats_system.get_stat(
            self.test_user_id,
            StatCategory.COMBAT,
            'monsters_killed'
        )
        
        self.assertEqual(value, 5)

    def test_cumulative_stats(self):
        """Test cumulative statistics"""
        # Track multiple values
        for value in [5, 3, 7]:
            self.stats_system.track_stat(
                self.test_user_id,
                StatCategory.COMBAT,
                'damage_dealt',
                value
            )
        
        # Get total
        total = self.stats_system.get_stat(
            self.test_user_id,
            StatCategory.COMBAT,
            'damage_dealt'
        )
        
        self.assertEqual(total, 15)

    def test_current_value_stats(self):
        """Test current value statistics"""
        # Track level progression
        for level in [1, 2, 3]:
            self.stats_system.track_stat(
                self.test_user_id,
                StatCategory.PROGRESSION,
                'level',
                level,
                increment=False
            )
        
        # Get current level
        level = self.stats_system.get_stat(
            self.test_user_id,
            StatCategory.PROGRESSION,
            'level'
        )
        
        self.assertEqual(level, 3)

    def test_time_based_stats(self):
        """Test time-based statistics"""
        # Create stats at different times
        now = datetime.utcnow()
        
        with patch('datetime.datetime') as mock_datetime:
            # Yesterday's stats
            mock_datetime.utcnow.return_value = now - timedelta(days=1)
            self.stats_system.track_stat(
                self.test_user_id,
                StatCategory.COMBAT,
                'kills',
                10
            )
            
            # Today's stats
            mock_datetime.utcnow.return_value = now
            self.stats_system.track_stat(
                self.test_user_id,
                StatCategory.COMBAT,
                'kills',
                5
            )
        
        # Get daily stats
        daily_kills = self.stats_system.get_stat(
            self.test_user_id,
            StatCategory.COMBAT,
            'kills',
            timedelta(days=1)
        )
        
        self.assertEqual(daily_kills, 5)

    def test_global_stats(self):
        """Test global statistics"""
        # Track stats for multiple users
        for user_id in [1, 2, 3]:
            self.stats_system.track_stat(
                user_id,
                StatCategory.ECONOMY,
                'crystals_earned',
                100
            )
        
        # Get global total
        total = self.stats_system.get_global_stat(
            StatCategory.ECONOMY,
            'crystals_earned'
        )
        
        self.assertEqual(total, 300)

    def test_stats_summary(self):
        """Test statistics summary"""
        # Track various stats
        self.stats_system.track_stat(
            self.test_user_id,
            StatCategory.COMBAT,
            'kills',
            10
        )
        self.stats_system.track_stat(
            self.test_user_id,
            StatCategory.COMBAT,
            'deaths',
            2
        )
        
        # Get summary
        summary = self.stats_system.get_stats_summary(
            self.test_user_id,
            StatCategory.COMBAT
        )
        
        self.assertEqual(summary.all_time['kills'], 10)
        self.assertEqual(summary.all_time['deaths'], 2)

    def test_leaderboard(self):
        """Test leaderboard generation"""
        # Track stats for multiple users
        stats = {
            1: 100,
            2: 200,
            3: 150
        }
        
        for user_id, value in stats.items():
            self.stats_system.track_stat(
                user_id,
                StatCategory.GATES,
                'gates_cleared',
                value
            )
        
        # Get leaderboard
        leaderboard = self.stats_system.get_leaderboard(
            StatCategory.GATES,
            'gates_cleared',
            limit=3
        )
        
        self.assertEqual(len(leaderboard), 3)
        self.assertEqual(leaderboard[0]['user_id'], 2)  # Highest value
        self.assertEqual(leaderboard[0]['value'], 200)

    def test_multiple_categories(self):
        """Test tracking multiple categories"""
        # Track stats in different categories
        categories = {
            StatCategory.COMBAT: ('damage_dealt', 1000),
            StatCategory.ECONOMY: ('gold_earned', 500),
            StatCategory.SOCIAL: ('friends_made', 5)
        }
        
        for category, (stat_name, value) in categories.items():
            self.stats_system.track_stat(
                self.test_user_id,
                category,
                stat_name,
                value
            )
        
        # Verify each category
        for category, (stat_name, value) in categories.items():
            stat_value = self.stats_system.get_stat(
                self.test_user_id,
                category,
                stat_name
            )
            self.assertEqual(stat_value, value)

    def test_empty_stats(self):
        """Test handling of empty statistics"""
        # Get non-existent stat
        value = self.stats_system.get_stat(
            999,  # Non-existent user
            StatCategory.COMBAT,
            'non_existent_stat'
        )
        
        self.assertEqual(value, 0)
        
        # Get empty leaderboard
        leaderboard = self.stats_system.get_leaderboard(
            StatCategory.COMBAT,
            'non_existent_stat'
        )
        
        self.assertEqual(len(leaderboard), 0)

if __name__ == '__main__':
    unittest.main()
