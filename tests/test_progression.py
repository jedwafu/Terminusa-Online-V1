import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum, auto
import math
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ProgressionType(Enum):
    """Types of progression"""
    CHARACTER_LEVEL = auto()
    SKILL_LEVEL = auto()
    REPUTATION = auto()
    MASTERY = auto()
    PROFESSION = auto()
    ACHIEVEMENT = auto()
    COLLECTION = auto()

@dataclass
class ProgressionLevel:
    """Level configuration"""
    level: int
    experience_required: int
    rewards: Optional[Dict[str, Any]] = None
    unlocks: Optional[List[str]] = None

@dataclass
class ProgressionTrack:
    """Progression track data"""
    id: str
    type: ProgressionType
    name: str
    description: str
    levels: Dict[int, ProgressionLevel]
    max_level: int
    experience_multiplier: float = 1.0

@dataclass
class ProgressionState:
    """Progression state data"""
    track_id: str
    current_level: int
    current_experience: int
    total_experience: int
    unlocked_features: Set[str]
    last_updated: datetime

class ProgressionSystem:
    """System for progression management"""
    def __init__(self):
        self.tracks: Dict[str, ProgressionTrack] = {}
        self.states: Dict[int, Dict[str, ProgressionState]] = {}
        self.experience_modifiers: Dict[str, float] = {}

    def register_track(self, track: ProgressionTrack):
        """Register a progression track"""
        self.tracks[track.id] = track

    def initialize_state(
        self,
        user_id: int,
        track_id: str
    ) -> Optional[ProgressionState]:
        """Initialize progression state"""
        track = self.tracks.get(track_id)
        if not track:
            return None
        
        if user_id not in self.states:
            self.states[user_id] = {}
        
        if track_id not in self.states[user_id]:
            self.states[user_id][track_id] = ProgressionState(
                track_id=track_id,
                current_level=1,
                current_experience=0,
                total_experience=0,
                unlocked_features=set(),
                last_updated=datetime.utcnow()
            )
        
        return self.states[user_id][track_id]

    def add_experience(
        self,
        user_id: int,
        track_id: str,
        amount: int,
        source: str
    ) -> Optional[List[int]]:
        """Add experience to progression track"""
        track = self.tracks.get(track_id)
        if not track:
            return None
        
        state = self.initialize_state(user_id, track_id)
        if not state:
            return None
        
        # Apply modifiers
        modified_amount = amount * track.experience_multiplier
        for modifier in self.experience_modifiers.values():
            modified_amount *= modifier
        
        # Add experience
        state.current_experience += int(modified_amount)
        state.total_experience += int(modified_amount)
        state.last_updated = datetime.utcnow()
        
        # Check for level ups
        levels_gained = []
        while True:
            next_level = state.current_level + 1
            if next_level > track.max_level:
                break
            
            level_config = track.levels.get(next_level)
            if not level_config:
                break
            
            if state.current_experience >= level_config.experience_required:
                state.current_level = next_level
                state.current_experience -= level_config.experience_required
                levels_gained.append(next_level)
                
                # Unlock features
                if level_config.unlocks:
                    state.unlocked_features.update(level_config.unlocks)
            else:
                break
        
        return levels_gained if levels_gained else None

    def get_state(
        self,
        user_id: int,
        track_id: str
    ) -> Optional[ProgressionState]:
        """Get progression state"""
        if user_id not in self.states:
            return None
        return self.states[user_id].get(track_id)

    def get_level_progress(
        self,
        user_id: int,
        track_id: str
    ) -> Optional[float]:
        """Get level progress percentage"""
        track = self.tracks.get(track_id)
        state = self.get_state(user_id, track_id)
        if not track or not state:
            return None
        
        level_config = track.levels.get(state.current_level + 1)
        if not level_config:
            return 100.0
        
        return (state.current_experience / level_config.experience_required) * 100

    def add_experience_modifier(
        self,
        modifier_id: str,
        multiplier: float,
        duration: Optional[timedelta] = None
    ):
        """Add experience modifier"""
        self.experience_modifiers[modifier_id] = multiplier
        
        if duration:
            async def remove_modifier():
                await asyncio.sleep(duration.total_seconds())
                if modifier_id in self.experience_modifiers:
                    del self.experience_modifiers[modifier_id]
            
            asyncio.create_task(remove_modifier())

    def get_unlocked_features(
        self,
        user_id: int,
        track_id: str
    ) -> Set[str]:
        """Get unlocked features"""
        state = self.get_state(user_id, track_id)
        if not state:
            return set()
        return state.unlocked_features.copy()

class TestProgression(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.progression = ProgressionSystem()
        
        # Create test track
        levels = {
            i: ProgressionLevel(
                level=i,
                experience_required=100 * i,
                rewards={'gold': 100 * i},
                unlocks=[f'feature_{i}'] if i % 2 == 0 else None
            )
            for i in range(1, 11)
        }
        
        self.character_track = ProgressionTrack(
            id="character",
            type=ProgressionType.CHARACTER_LEVEL,
            name="Character Level",
            description="Main character progression",
            levels=levels,
            max_level=10
        )
        
        self.progression.register_track(self.character_track)

    def test_state_initialization(self):
        """Test progression state initialization"""
        # Initialize state
        state = self.progression.initialize_state(1, "character")
        
        # Verify initial state
        self.assertIsNotNone(state)
        self.assertEqual(state.current_level, 1)
        self.assertEqual(state.current_experience, 0)
        self.assertEqual(state.total_experience, 0)

    def test_experience_gain(self):
        """Test experience gain"""
        # Add experience
        levels_gained = self.progression.add_experience(
            1,
            "character",
            150,
            "quest"
        )
        
        # Verify level up
        self.assertEqual(len(levels_gained), 1)
        
        state = self.progression.get_state(1, "character")
        self.assertEqual(state.current_level, 2)
        self.assertEqual(state.current_experience, 50)  # 150 - 100

    def test_multiple_level_ups(self):
        """Test multiple level ups"""
        # Add enough experience for multiple levels
        levels_gained = self.progression.add_experience(
            1,
            "character",
            500,
            "quest"
        )
        
        # Verify multiple level ups
        self.assertEqual(len(levels_gained), 3)  # Should reach level 4
        
        state = self.progression.get_state(1, "character")
        self.assertEqual(state.current_level, 4)

    def test_experience_modifiers(self):
        """Test experience modifiers"""
        # Add modifier
        self.progression.add_experience_modifier(
            "double_exp",
            2.0
        )
        
        # Add experience
        self.progression.add_experience(
            1,
            "character",
            100,
            "quest"
        )
        
        # Verify modified experience
        state = self.progression.get_state(1, "character")
        self.assertEqual(state.total_experience, 200)

    def test_level_progress(self):
        """Test level progress calculation"""
        # Add partial level experience
        self.progression.add_experience(
            1,
            "character",
            50,
            "quest"
        )
        
        # Check progress
        progress = self.progression.get_level_progress(
            1,
            "character"
        )
        
        self.assertEqual(progress, 50.0)  # 50%

    def test_feature_unlocks(self):
        """Test feature unlocking"""
        # Level up to unlock features
        self.progression.add_experience(
            1,
            "character",
            200,
            "quest"
        )
        
        # Check unlocked features
        features = self.progression.get_unlocked_features(
            1,
            "character"
        )
        
        self.assertIn('feature_2', features)

    def test_max_level(self):
        """Test max level handling"""
        # Add experience beyond max level
        self.progression.add_experience(
            1,
            "character",
            10000,
            "quest"
        )
        
        # Verify max level
        state = self.progression.get_state(1, "character")
        self.assertEqual(
            state.current_level,
            self.character_track.max_level
        )

    def test_temporary_modifier(self):
        """Test temporary experience modifier"""
        # Add temporary modifier
        self.progression.add_experience_modifier(
            "temp_boost",
            2.0,
            timedelta(seconds=1)
        )
        
        # Add experience with modifier
        self.progression.add_experience(
            1,
            "character",
            100,
            "quest"
        )
        
        # Wait for modifier to expire
        import time
        time.sleep(1.1)
        
        # Add experience without modifier
        self.progression.add_experience(
            1,
            "character",
            100,
            "quest"
        )
        
        # Verify total experience
        state = self.progression.get_state(1, "character")
        self.assertEqual(state.total_experience, 300)  # 200 + 100

    def test_multiple_tracks(self):
        """Test multiple progression tracks"""
        # Create second track
        skill_track = ProgressionTrack(
            id="skill",
            type=ProgressionType.SKILL_LEVEL,
            name="Skill Level",
            description="Skill progression",
            levels={
                i: ProgressionLevel(
                    level=i,
                    experience_required=50 * i
                )
                for i in range(1, 6)
            },
            max_level=5
        )
        
        self.progression.register_track(skill_track)
        
        # Add experience to both tracks
        self.progression.add_experience(1, "character", 100, "quest")
        self.progression.add_experience(1, "skill", 100, "training")
        
        # Verify separate progression
        char_state = self.progression.get_state(1, "character")
        skill_state = self.progression.get_state(1, "skill")
        
        self.assertEqual(char_state.current_level, 2)
        self.assertEqual(skill_state.current_level, 3)

    def test_experience_sources(self):
        """Test different experience sources"""
        sources = ['quest', 'combat', 'crafting']
        
        # Add experience from different sources
        for source in sources:
            self.progression.add_experience(
                1,
                "character",
                50,
                source
            )
        
        # Verify total experience
        state = self.progression.get_state(1, "character")
        self.assertEqual(state.total_experience, 150)

if __name__ == '__main__':
    unittest.main()
