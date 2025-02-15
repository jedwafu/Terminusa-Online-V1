import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from enum import Enum, auto
from dataclasses import dataclass
import json
import redis

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class LeaderboardType(Enum):
    """Types of leaderboards"""
    LEVEL = auto()
    GATES_CLEARED = auto()
    PVP_RATING = auto()
    GUILD_RANKING = auto()
    WEALTH = auto()
    ACHIEVEMENTS = auto()
    WEEKLY_GATES = auto()
    MONTHLY_GATES = auto()
    SEASON_RANKING = auto()

@dataclass
class LeaderboardEntry:
    """Leaderboard entry data"""
    id: int
    name: str
    score: int
    rank: int = 0
    details: Optional[Dict] = None
    timestamp: datetime = None

class LeaderboardSystem:
    """Manages game leaderboards"""
    def __init__(self, redis_url: str = 'redis://localhost:6379/0'):
        self.redis = redis.from_url(redis_url)
        self.cache_duration = 300  # 5 minutes

    def update_score(self, board_type: LeaderboardType, entry: LeaderboardEntry):
        """Update score in leaderboard"""
        key = f"leaderboard:{board_type.name}"
        member = json.dumps({
            'id': entry.id,
            'name': entry.name,
            'score': entry.score,
            'details': entry.details,
            'timestamp': entry.timestamp.isoformat() if entry.timestamp else None
        })
        self.redis.zadd(key, {member: entry.score})

    def get_rankings(
        self,
        board_type: LeaderboardType,
        start: int = 0,
        end: int = -1
    ) -> List[LeaderboardEntry]:
        """Get rankings from leaderboard"""
        key = f"leaderboard:{board_type.name}"
        entries = self.redis.zrevrange(key, start, end, withscores=True)
        
        rankings = []
        for rank, (member, score) in enumerate(entries, start=start+1):
            data = json.loads(member)
            entry = LeaderboardEntry(
                id=data['id'],
                name=data['name'],
                score=int(score),
                rank=rank,
                details=data['details'],
                timestamp=datetime.fromisoformat(data['timestamp']) if data['timestamp'] else None
            )
            rankings.append(entry)
        
        return rankings

    def get_rank(self, board_type: LeaderboardType, entry_id: int) -> Optional[int]:
        """Get rank for specific entry"""
        key = f"leaderboard:{board_type.name}"
        entries = self.redis.zrevrange(key, 0, -1, withscores=True)
        
        for rank, (member, _) in enumerate(entries, start=1):
            data = json.loads(member)
            if data['id'] == entry_id:
                return rank
        
        return None

    def get_top_n(self, board_type: LeaderboardType, n: int) -> List[LeaderboardEntry]:
        """Get top N entries"""
        return self.get_rankings(board_type, 0, n-1)

    def clear_leaderboard(self, board_type: LeaderboardType):
        """Clear a leaderboard"""
        key = f"leaderboard:{board_type.name}"
        self.redis.delete(key)

class TestLeaderboard(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.leaderboard = LeaderboardSystem()
        
        # Clear all test leaderboards
        for board_type in LeaderboardType:
            self.leaderboard.clear_leaderboard(board_type)
        
        # Create test entries
        self.test_entries = [
            LeaderboardEntry(
                id=1,
                name="Player1",
                score=1000,
                details={'level': 10},
                timestamp=datetime.utcnow()
            ),
            LeaderboardEntry(
                id=2,
                name="Player2",
                score=2000,
                details={'level': 20},
                timestamp=datetime.utcnow()
            ),
            LeaderboardEntry(
                id=3,
                name="Player3",
                score=1500,
                details={'level': 15},
                timestamp=datetime.utcnow()
            )
        ]

    def test_basic_ranking(self):
        """Test basic ranking functionality"""
        # Add entries
        for entry in self.test_entries:
            self.leaderboard.update_score(LeaderboardType.LEVEL, entry)
        
        # Get rankings
        rankings = self.leaderboard.get_rankings(LeaderboardType.LEVEL)
        
        # Verify order
        self.assertEqual(len(rankings), 3)
        self.assertEqual(rankings[0].name, "Player2")  # Highest score
        self.assertEqual(rankings[1].name, "Player3")  # Second highest
        self.assertEqual(rankings[2].name, "Player1")  # Lowest score

    def test_score_updates(self):
        """Test score updating"""
        # Add initial entry
        entry = self.test_entries[0]
        self.leaderboard.update_score(LeaderboardType.LEVEL, entry)
        
        # Update score
        updated_entry = LeaderboardEntry(
            id=entry.id,
            name=entry.name,
            score=1500,
            details=entry.details,
            timestamp=datetime.utcnow()
        )
        self.leaderboard.update_score(LeaderboardType.LEVEL, updated_entry)
        
        # Verify update
        rankings = self.leaderboard.get_rankings(LeaderboardType.LEVEL)
        self.assertEqual(rankings[0].score, 1500)

    def test_multiple_leaderboards(self):
        """Test multiple leaderboard types"""
        # Add entries to different leaderboards
        for entry in self.test_entries:
            self.leaderboard.update_score(LeaderboardType.LEVEL, entry)
            self.leaderboard.update_score(LeaderboardType.PVP_RATING, entry)
        
        # Verify separate rankings
        level_rankings = self.leaderboard.get_rankings(LeaderboardType.LEVEL)
        pvp_rankings = self.leaderboard.get_rankings(LeaderboardType.PVP_RATING)
        
        self.assertEqual(len(level_rankings), 3)
        self.assertEqual(len(pvp_rankings), 3)

    def test_rank_retrieval(self):
        """Test rank retrieval for specific entry"""
        # Add entries
        for entry in self.test_entries:
            self.leaderboard.update_score(LeaderboardType.LEVEL, entry)
        
        # Get rank for specific player
        rank = self.leaderboard.get_rank(LeaderboardType.LEVEL, 2)  # Player2
        self.assertEqual(rank, 1)  # Should be first place

    def test_top_n_rankings(self):
        """Test retrieving top N rankings"""
        # Add entries
        for entry in self.test_entries:
            self.leaderboard.update_score(LeaderboardType.LEVEL, entry)
        
        # Get top 2
        top_2 = self.leaderboard.get_top_n(LeaderboardType.LEVEL, 2)
        
        self.assertEqual(len(top_2), 2)
        self.assertEqual(top_2[0].name, "Player2")
        self.assertEqual(top_2[1].name, "Player3")

    def test_entry_details(self):
        """Test entry details preservation"""
        # Add entry with details
        entry = self.test_entries[0]
        self.leaderboard.update_score(LeaderboardType.LEVEL, entry)
        
        # Retrieve entry
        rankings = self.leaderboard.get_rankings(LeaderboardType.LEVEL)
        retrieved = rankings[0]
        
        # Verify details
        self.assertEqual(retrieved.details['level'], entry.details['level'])

    def test_timestamp_handling(self):
        """Test timestamp handling"""
        # Add entry with timestamp
        entry = self.test_entries[0]
        self.leaderboard.update_score(LeaderboardType.LEVEL, entry)
        
        # Retrieve entry
        rankings = self.leaderboard.get_rankings(LeaderboardType.LEVEL)
        retrieved = rankings[0]
        
        # Verify timestamp
        self.assertIsNotNone(retrieved.timestamp)
        self.assertIsInstance(retrieved.timestamp, datetime)

    def test_weekly_rankings(self):
        """Test weekly leaderboard reset"""
        # Add entries to weekly leaderboard
        for entry in self.test_entries:
            self.leaderboard.update_score(LeaderboardType.WEEKLY_GATES, entry)
        
        # Simulate week passing
        old_rankings = self.leaderboard.get_rankings(LeaderboardType.WEEKLY_GATES)
        self.leaderboard.clear_leaderboard(LeaderboardType.WEEKLY_GATES)
        
        # Verify reset
        new_rankings = self.leaderboard.get_rankings(LeaderboardType.WEEKLY_GATES)
        self.assertEqual(len(new_rankings), 0)

    def test_guild_rankings(self):
        """Test guild rankings"""
        # Create guild entries
        guild_entries = [
            LeaderboardEntry(
                id=1,
                name="Guild1",
                score=5000,
                details={'members': 10, 'level': 5},
                timestamp=datetime.utcnow()
            ),
            LeaderboardEntry(
                id=2,
                name="Guild2",
                score=7500,
                details={'members': 15, 'level': 7},
                timestamp=datetime.utcnow()
            )
        ]
        
        # Add guild entries
        for entry in guild_entries:
            self.leaderboard.update_score(LeaderboardType.GUILD_RANKING, entry)
        
        # Verify guild rankings
        rankings = self.leaderboard.get_rankings(LeaderboardType.GUILD_RANKING)
        self.assertEqual(rankings[0].name, "Guild2")
        self.assertEqual(rankings[0].details['level'], 7)

    def test_seasonal_rankings(self):
        """Test seasonal rankings"""
        # Add entries to seasonal leaderboard
        for entry in self.test_entries:
            self.leaderboard.update_score(LeaderboardType.SEASON_RANKING, entry)
        
        # Get rankings with season details
        rankings = self.leaderboard.get_rankings(LeaderboardType.SEASON_RANKING)
        
        # Verify rankings
        self.assertEqual(len(rankings), 3)
        self.assertTrue(all(hasattr(r, 'timestamp') for r in rankings))

    def test_wealth_rankings(self):
        """Test wealth leaderboard"""
        # Create wealth entries
        wealth_entries = [
            LeaderboardEntry(
                id=1,
                name="Rich Player",
                score=1000000,
                details={'crystals': 1000000, 'exons': 1000},
                timestamp=datetime.utcnow()
            ),
            LeaderboardEntry(
                id=2,
                name="Richer Player",
                score=2000000,
                details={'crystals': 2000000, 'exons': 2000},
                timestamp=datetime.utcnow()
            )
        ]
        
        # Add wealth entries
        for entry in wealth_entries:
            self.leaderboard.update_score(LeaderboardType.WEALTH, entry)
        
        # Verify wealth rankings
        rankings = self.leaderboard.get_rankings(LeaderboardType.WEALTH)
        self.assertEqual(rankings[0].name, "Richer Player")
        self.assertEqual(rankings[0].details['crystals'], 2000000)

if __name__ == '__main__':
    unittest.main()
