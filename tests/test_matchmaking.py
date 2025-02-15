import unittest
from unittest.mock import Mock, patch
import sys
import os
import asyncio
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class PlayerRole(Enum):
    """Player roles for matchmaking"""
    TANK = auto()
    DPS = auto()
    HEALER = auto()
    SUPPORT = auto()

@dataclass
class PlayerProfile:
    """Player profile for matchmaking"""
    id: int
    level: int
    role: PlayerRole
    rating: int
    party_id: Optional[int] = None
    preferred_roles: Set[PlayerRole] = None
    last_active: datetime = None
    region: str = 'global'

@dataclass
class MatchRequest:
    """Match request data"""
    player_id: int
    gate_id: Optional[int] = None
    roles_needed: Set[PlayerRole] = None
    min_level: int = 1
    max_level: Optional[int] = None
    region: str = 'global'
    timestamp: datetime = None

class MatchmakingSystem:
    """Handles player matchmaking"""
    def __init__(self):
        self.players: Dict[int, PlayerProfile] = {}
        self.match_requests: List[MatchRequest] = []
        self.active_matches: Dict[int, List[int]] = {}  # match_id -> player_ids
        self.next_match_id = 1

    def add_player(self, profile: PlayerProfile):
        """Add player to matchmaking pool"""
        self.players[profile.id] = profile

    def remove_player(self, player_id: int):
        """Remove player from matchmaking pool"""
        if player_id in self.players:
            del self.players[player_id]

    def request_match(self, request: MatchRequest) -> Optional[int]:
        """Request a match"""
        request.timestamp = datetime.utcnow()
        self.match_requests.append(request)
        
        # Try to find match immediately
        match = self._find_match(request)
        if match:
            match_id = self.next_match_id
            self.next_match_id += 1
            self.active_matches[match_id] = match
            return match_id
        
        return None

    def _find_match(self, request: MatchRequest) -> Optional[List[int]]:
        """Find suitable match for request"""
        candidates = []
        
        for player_id, profile in self.players.items():
            if player_id != request.player_id and self._is_suitable_match(profile, request):
                candidates.append(player_id)
        
        if candidates:
            # Include requesting player
            return [request.player_id] + candidates[:3]  # Max 4 players per match
        
        return None

    def _is_suitable_match(self, profile: PlayerProfile, request: MatchRequest) -> bool:
        """Check if player is suitable for match"""
        # Check level requirements
        if profile.level < request.min_level:
            return False
        if request.max_level and profile.level > request.max_level:
            return False
        
        # Check region
        if request.region != 'global' and profile.region != request.region:
            return False
        
        # Check role requirements
        if request.roles_needed and profile.role not in request.roles_needed:
            return False
        
        return True

    def get_active_matches(self) -> Dict[int, List[int]]:
        """Get all active matches"""
        return self.active_matches.copy()

    def cancel_match(self, match_id: int):
        """Cancel an active match"""
        if match_id in self.active_matches:
            del self.active_matches[match_id]

class TestMatchmaking(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.matchmaking = MatchmakingSystem()
        
        # Create test players
        self.players = [
            PlayerProfile(
                id=1,
                level=10,
                role=PlayerRole.TANK,
                rating=1500,
                region='NA'
            ),
            PlayerProfile(
                id=2,
                level=12,
                role=PlayerRole.DPS,
                rating=1600,
                region='NA'
            ),
            PlayerProfile(
                id=3,
                level=11,
                role=PlayerRole.HEALER,
                rating=1550,
                region='NA'
            )
        ]
        
        for player in self.players:
            self.matchmaking.add_player(player)

    def test_basic_matching(self):
        """Test basic matchmaking functionality"""
        # Create match request
        request = MatchRequest(
            player_id=1,
            min_level=10,
            region='NA'
        )
        
        # Request match
        match_id = self.matchmaking.request_match(request)
        
        # Verify match
        self.assertIsNotNone(match_id)
        match = self.matchmaking.get_active_matches()[match_id]
        self.assertIn(1, match)  # Requesting player
        self.assertTrue(len(match) > 1)  # At least one other player

    def test_role_requirements(self):
        """Test role-based matchmaking"""
        # Request match requiring specific roles
        request = MatchRequest(
            player_id=1,
            roles_needed={PlayerRole.HEALER, PlayerRole.DPS},
            region='NA'
        )
        
        match_id = self.matchmaking.request_match(request)
        
        # Verify match has required roles
        match = self.matchmaking.get_active_matches()[match_id]
        matched_roles = {
            self.matchmaking.players[pid].role
            for pid in match if pid != 1
        }
        self.assertTrue(PlayerRole.HEALER in matched_roles)
        self.assertTrue(PlayerRole.DPS in matched_roles)

    def test_level_requirements(self):
        """Test level-based matchmaking"""
        # Request match with level requirements
        request = MatchRequest(
            player_id=1,
            min_level=11,
            max_level=15,
            region='NA'
        )
        
        match_id = self.matchmaking.request_match(request)
        
        # Verify matched players meet level requirements
        match = self.matchmaking.get_active_matches()[match_id]
        for player_id in match:
            if player_id != 1:  # Skip requesting player
                player = self.matchmaking.players[player_id]
                self.assertGreaterEqual(player.level, 11)
                self.assertLessEqual(player.level, 15)

    def test_region_matching(self):
        """Test region-based matchmaking"""
        # Add player from different region
        eu_player = PlayerProfile(
            id=4,
            level=10,
            role=PlayerRole.DPS,
            rating=1500,
            region='EU'
        )
        self.matchmaking.add_player(eu_player)
        
        # Request match in NA region
        request = MatchRequest(
            player_id=1,
            region='NA'
        )
        
        match_id = self.matchmaking.request_match(request)
        
        # Verify only NA players are matched
        match = self.matchmaking.get_active_matches()[match_id]
        for player_id in match:
            if player_id != 1:
                self.assertEqual(
                    self.matchmaking.players[player_id].region,
                    'NA'
                )

    def test_match_cancellation(self):
        """Test match cancellation"""
        # Create match
        request = MatchRequest(
            player_id=1,
            region='NA'
        )
        match_id = self.matchmaking.request_match(request)
        
        # Cancel match
        self.matchmaking.cancel_match(match_id)
        
        # Verify match removed
        self.assertNotIn(match_id, self.matchmaking.get_active_matches())

    def test_player_removal(self):
        """Test player removal from matchmaking"""
        # Remove player
        self.matchmaking.remove_player(2)
        
        # Request match
        request = MatchRequest(
            player_id=1,
            region='NA'
        )
        match_id = self.matchmaking.request_match(request)
        
        # Verify removed player not in match
        match = self.matchmaking.get_active_matches()[match_id]
        self.assertNotIn(2, match)

    def test_rating_based_matching(self):
        """Test rating-based matchmaking"""
        # Add players with different ratings
        high_rated = PlayerProfile(
            id=5,
            level=10,
            role=PlayerRole.DPS,
            rating=2000,
            region='NA'
        )
        self.matchmaking.add_player(high_rated)
        
        # Request match with similar rating
        request = MatchRequest(
            player_id=1,  # Rating 1500
            region='NA'
        )
        match_id = self.matchmaking.request_match(request)
        
        # Verify matched players have closer ratings
        match = self.matchmaking.get_active_matches()[match_id]
        for player_id in match:
            if player_id != 1:
                player = self.matchmaking.players[player_id]
                rating_diff = abs(player.rating - 1500)
                self.assertLess(rating_diff, 500)

    def test_party_matching(self):
        """Test party-based matchmaking"""
        # Set players in same party
        self.players[1].party_id = 1
        self.players[2].party_id = 1
        
        # Request match for party member
        request = MatchRequest(
            player_id=1,
            region='NA'
        )
        match_id = self.matchmaking.request_match(request)
        
        # Verify party members are matched together
        match = self.matchmaking.get_active_matches()[match_id]
        self.assertIn(1, match)
        self.assertIn(2, match)

    def test_preferred_roles(self):
        """Test preferred roles matching"""
        # Set preferred roles
        self.players[1].preferred_roles = {PlayerRole.TANK, PlayerRole.DPS}
        
        # Request match with role requirements
        request = MatchRequest(
            player_id=2,
            roles_needed={PlayerRole.TANK},
            region='NA'
        )
        match_id = self.matchmaking.request_match(request)
        
        # Verify player with preferred role is matched
        match = self.matchmaking.get_active_matches()[match_id]
        self.assertIn(1, match)

if __name__ == '__main__':
    unittest.main()
