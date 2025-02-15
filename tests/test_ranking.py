import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import json
import math

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RankTier(Enum):
    """Rank tiers"""
    BRONZE = auto()
    SILVER = auto()
    GOLD = auto()
    PLATINUM = auto()
    DIAMOND = auto()
    MASTER = auto()
    GRANDMASTER = auto()

class RankDivision(Enum):
    """Rank divisions"""
    IV = 4
    III = 3
    II = 2
    I = 1

@dataclass
class RankInfo:
    """Rank information"""
    tier: RankTier
    division: RankDivision
    points: int
    wins: int
    losses: int
    streak: int
    peak_tier: RankTier
    peak_division: RankDivision
    season_id: str

@dataclass
class MatchResult:
    """Match result data"""
    winner_id: int
    loser_id: int
    winner_score: int
    loser_score: int
    timestamp: datetime
    match_type: str
    metadata: Optional[Dict[str, Any]] = None

class RankingSystem:
    """System for player rankings"""
    def __init__(self):
        self.rankings: Dict[str, Dict[int, RankInfo]] = {}  # season -> user -> rank
        self.match_history: List[MatchResult] = []
        self.current_season: str = None
        
        # Ranking configuration
        self.points_per_tier = 400
        self.points_per_division = 100
        self.base_points_gain = 25
        self.base_points_loss = 20
        self.streak_multiplier = 0.1
        self.max_streak = 5

    def start_season(self, season_id: str):
        """Start a new ranked season"""
        if season_id in self.rankings:
            return False
        
        self.rankings[season_id] = {}
        self.current_season = season_id
        return True

    def initialize_rank(
        self,
        user_id: int,
        season_id: Optional[str] = None
    ) -> RankInfo:
        """Initialize player rank"""
        season_id = season_id or self.current_season
        if not season_id:
            raise ValueError("No active season")
        
        if season_id not in self.rankings:
            raise ValueError("Invalid season")
        
        if user_id in self.rankings[season_id]:
            return self.rankings[season_id][user_id]
        
        # Create initial rank
        rank = RankInfo(
            tier=RankTier.BRONZE,
            division=RankDivision.IV,
            points=0,
            wins=0,
            losses=0,
            streak=0,
            peak_tier=RankTier.BRONZE,
            peak_division=RankDivision.IV,
            season_id=season_id
        )
        
        self.rankings[season_id][user_id] = rank
        return rank

    def record_match(
        self,
        winner_id: int,
        loser_id: int,
        winner_score: int,
        loser_score: int,
        match_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Tuple[RankInfo, RankInfo]:
        """Record match result and update rankings"""
        if not self.current_season:
            raise ValueError("No active season")
        
        # Initialize ranks if needed
        winner_rank = self.initialize_rank(winner_id)
        loser_rank = self.initialize_rank(loser_id)
        
        # Calculate points
        points_gained = self._calculate_points(
            winner_rank,
            loser_rank,
            winner_score,
            loser_score
        )
        
        # Update winner
        winner_rank.points += points_gained
        winner_rank.wins += 1
        winner_rank.streak = min(
            winner_rank.streak + 1,
            self.max_streak
        )
        self._update_tier_division(winner_rank)
        
        # Update loser
        loser_rank.points = max(0, loser_rank.points - points_gained)
        loser_rank.losses += 1
        loser_rank.streak = max(
            loser_rank.streak - 1,
            -self.max_streak
        )
        self._update_tier_division(loser_rank)
        
        # Record match
        self.match_history.append(
            MatchResult(
                winner_id=winner_id,
                loser_id=loser_id,
                winner_score=winner_score,
                loser_score=loser_score,
                timestamp=datetime.utcnow(),
                match_type=match_type,
                metadata=metadata
            )
        )
        
        return winner_rank, loser_rank

    def get_rank(
        self,
        user_id: int,
        season_id: Optional[str] = None
    ) -> Optional[RankInfo]:
        """Get player rank"""
        season_id = season_id or self.current_season
        if not season_id or season_id not in self.rankings:
            return None
        return self.rankings[season_id].get(user_id)

    def get_leaderboard(
        self,
        season_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Tuple[int, RankInfo]]:
        """Get season leaderboard"""
        season_id = season_id or self.current_season
        if not season_id or season_id not in self.rankings:
            return []
        
        # Sort by tier, division, and points
        rankings = [
            (user_id, rank)
            for user_id, rank in self.rankings[season_id].items()
        ]
        
        rankings.sort(
            key=lambda x: (
                x[1].tier.value,
                x[1].division.value,
                x[1].points
            ),
            reverse=True
        )
        
        return rankings[:limit]

    def get_match_history(
        self,
        user_id: Optional[int] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        match_type: Optional[str] = None
    ) -> List[MatchResult]:
        """Get match history"""
        matches = self.match_history
        
        if user_id is not None:
            matches = [
                m for m in matches
                if m.winner_id == user_id or m.loser_id == user_id
            ]
        
        if start_time:
            matches = [m for m in matches if m.timestamp >= start_time]
        
        if end_time:
            matches = [m for m in matches if m.timestamp <= end_time]
        
        if match_type:
            matches = [m for m in matches if m.match_type == match_type]
        
        return sorted(matches, key=lambda m: m.timestamp)

    def _calculate_points(
        self,
        winner_rank: RankInfo,
        loser_rank: RankInfo,
        winner_score: int,
        loser_score: int
    ) -> int:
        """Calculate points for match result"""
        # Base points
        points = self.base_points_gain
        
        # Adjust for rank difference
        rank_diff = (
            winner_rank.tier.value * 4 + winner_rank.division.value
        ) - (
            loser_rank.tier.value * 4 + loser_rank.division.value
        )
        
        if rank_diff < 0:
            # Winner is lower ranked
            points *= 1.5
        elif rank_diff > 0:
            # Winner is higher ranked
            points *= 0.75
        
        # Adjust for score difference
        score_ratio = winner_score / max(loser_score, 1)
        points *= min(1.5, score_ratio)
        
        # Adjust for streak
        if winner_rank.streak > 0:
            points *= (1 + winner_rank.streak * self.streak_multiplier)
        
        return round(points)

    def _update_tier_division(self, rank: RankInfo):
        """Update tier and division based on points"""
        total_points = rank.points
        
        # Calculate tier
        tier_index = total_points // self.points_per_tier
        tier_index = min(tier_index, len(RankTier) - 1)
        new_tier = list(RankTier)[tier_index]
        
        # Calculate division
        remaining_points = total_points % self.points_per_tier
        division_index = remaining_points // self.points_per_division
        division_index = min(division_index, len(RankDivision) - 1)
        new_division = list(RankDivision)[division_index]
        
        # Update peak rank
        if (new_tier.value > rank.peak_tier.value or
            (new_tier == rank.peak_tier and
             new_division.value < rank.peak_division.value)):
            rank.peak_tier = new_tier
            rank.peak_division = new_division
        
        rank.tier = new_tier
        rank.division = new_division

class TestRanking(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.ranking = RankingSystem()
        self.ranking.start_season("S1")

    def test_rank_initialization(self):
        """Test rank initialization"""
        # Initialize rank
        rank = self.ranking.initialize_rank(1)
        
        # Verify initial rank
        self.assertEqual(rank.tier, RankTier.BRONZE)
        self.assertEqual(rank.division, RankDivision.IV)
        self.assertEqual(rank.points, 0)
        self.assertEqual(rank.wins, 0)
        self.assertEqual(rank.losses, 0)

    def test_match_recording(self):
        """Test match recording"""
        # Record match
        winner_rank, loser_rank = self.ranking.record_match(
            1, 2, 10, 5, "ranked"
        )
        
        # Verify ranks updated
        self.assertGreater(winner_rank.points, 0)
        self.assertEqual(winner_rank.wins, 1)
        self.assertEqual(loser_rank.losses, 1)
        
        # Verify match history
        history = self.ranking.get_match_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].winner_id, 1)
        self.assertEqual(history[0].loser_id, 2)

    def test_tier_progression(self):
        """Test tier progression"""
        # Win enough matches to rank up
        user_id = 1
        points_needed = self.ranking.points_per_tier
        matches_needed = math.ceil(
            points_needed / self.ranking.base_points_gain
        )
        
        for _ in range(matches_needed):
            self.ranking.record_match(
                user_id, 2, 10, 0, "ranked"
            )
        
        # Verify rank up
        rank = self.ranking.get_rank(user_id)
        self.assertGreater(
            rank.tier.value,
            RankTier.BRONZE.value
        )

    def test_win_streak(self):
        """Test win streak mechanics"""
        # Win multiple matches
        base_points = []
        streak_points = []
        
        # Get base points
        winner_rank, _ = self.ranking.record_match(
            1, 2, 10, 5, "ranked"
        )
        base_points.append(winner_rank.points)
        
        # Get streak points
        for _ in range(3):
            winner_rank, _ = self.ranking.record_match(
                1, 2, 10, 5, "ranked"
            )
            streak_points.append(
                winner_rank.points - sum(base_points)
            )
        
        # Verify increasing points
        self.assertTrue(
            all(b < s for b, s in zip(base_points, streak_points))
        )

    def test_leaderboard(self):
        """Test leaderboard generation"""
        # Create multiple players with different ranks
        for i in range(3):
            self.ranking.initialize_rank(i)
            for _ in range(i):  # Different number of wins
                self.ranking.record_match(
                    i, (i+1)%3, 10, 5, "ranked"
                )
        
        # Get leaderboard
        leaderboard = self.ranking.get_leaderboard()
        
        # Verify order
        self.assertEqual(len(leaderboard), 3)
        self.assertEqual(leaderboard[0][0], 2)  # Most wins

    def test_match_history_filtering(self):
        """Test match history filtering"""
        # Record different types of matches
        self.ranking.record_match(1, 2, 10, 5, "ranked")
        self.ranking.record_match(1, 2, 10, 5, "casual")
        self.ranking.record_match(2, 3, 10, 5, "ranked")
        
        # Filter by user
        user_matches = self.ranking.get_match_history(user_id=1)
        self.assertEqual(len(user_matches), 2)
        
        # Filter by type
        ranked_matches = self.ranking.get_match_history(
            match_type="ranked"
        )
        self.assertEqual(len(ranked_matches), 2)

    def test_season_management(self):
        """Test season management"""
        # Start new season
        success = self.ranking.start_season("S2")
        self.assertTrue(success)
        
        # Try to start duplicate season
        success = self.ranking.start_season("S2")
        self.assertFalse(success)
        
        # Initialize rank in different seasons
        rank_s1 = self.ranking.initialize_rank(1, "S1")
        rank_s2 = self.ranking.initialize_rank(1, "S2")
        
        self.assertNotEqual(
            id(rank_s1),
            id(rank_s2)
        )

    def test_peak_rank_tracking(self):
        """Test peak rank tracking"""
        user_id = 1
        self.ranking.initialize_rank(user_id)
        
        # Achieve high rank
        for _ in range(10):
            self.ranking.record_match(
                user_id, 2, 10, 0, "ranked"
            )
        
        peak_rank = self.ranking.get_rank(user_id)
        
        # Lose some matches
        for _ in range(5):
            self.ranking.record_match(
                2, user_id, 10, 0, "ranked"
            )
        
        current_rank = self.ranking.get_rank(user_id)
        
        # Verify peak rank preserved
        self.assertGreater(
            peak_rank.peak_tier.value,
            current_rank.tier.value
        )

if __name__ == '__main__':
    unittest.main()
