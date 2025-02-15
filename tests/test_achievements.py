import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AchievementCategory(Enum):
    """Achievement categories"""
    COMBAT = auto()
    EXPLORATION = auto()
    SOCIAL = auto()
    COLLECTION = auto()
    PROGRESSION = auto()
    MASTERY = auto()
    SPECIAL = auto()
    EVENT = auto()

@dataclass
class AchievementReward:
    """Achievement reward data"""
    crystals: int = 0
    exons: int = 0
    title: Optional[str] = None
    item_id: Optional[int] = None
    stat_bonus: Optional[Dict[str, int]] = None
    cosmetic_id: Optional[int] = None

@dataclass
class Achievement:
    """Achievement data"""
    id: int
    name: str
    description: str
    category: AchievementCategory
    requirements: Dict[str, int]
    reward: AchievementReward
    hidden: bool = False
    sequential_id: Optional[int] = None  # For achievement chains
    points: int = 10

class AchievementSystem:
    """Manages game achievements"""
    def __init__(self):
        self.achievements: Dict[int, Achievement] = {}
        self.user_achievements: Dict[int, Set[int]] = {}  # user_id -> achievement_ids
        self.user_progress: Dict[int, Dict[int, Dict[str, int]]] = {}  # user_id -> achievement_id -> progress

    def register_achievement(self, achievement: Achievement):
        """Register a new achievement"""
        self.achievements[achievement.id] = achievement

    def get_user_achievements(self, user_id: int) -> Set[int]:
        """Get user's completed achievements"""
        return self.user_achievements.get(user_id, set())

    def get_user_progress(self, user_id: int, achievement_id: int) -> Dict[str, int]:
        """Get user's progress for an achievement"""
        return self.user_progress.get(user_id, {}).get(achievement_id, {})

    def update_progress(
        self,
        user_id: int,
        achievement_id: int,
        progress: Dict[str, int]
    ) -> bool:
        """Update achievement progress"""
        if achievement_id not in self.achievements:
            return False
        
        # Initialize progress tracking
        if user_id not in self.user_progress:
            self.user_progress[user_id] = {}
        if achievement_id not in self.user_progress[user_id]:
            self.user_progress[user_id][achievement_id] = {}
        
        # Update progress
        achievement = self.achievements[achievement_id]
        current_progress = self.user_progress[user_id][achievement_id]
        
        for key, value in progress.items():
            if key in achievement.requirements:
                current_progress[key] = current_progress.get(key, 0) + value
        
        # Check if achievement completed
        completed = all(
            current_progress.get(key, 0) >= value
            for key, value in achievement.requirements.items()
        )
        
        if completed:
            if user_id not in self.user_achievements:
                self.user_achievements[user_id] = set()
            self.user_achievements[user_id].add(achievement_id)
        
        return completed

    def get_available_achievements(self, user_id: int) -> List[Achievement]:
        """Get available achievements for user"""
        completed = self.get_user_achievements(user_id)
        available = []
        
        for achievement in self.achievements.values():
            if achievement.id not in completed:
                if not achievement.hidden:
                    if not achievement.sequential_id or achievement.sequential_id in completed:
                        available.append(achievement)
        
        return available

    def calculate_total_points(self, user_id: int) -> int:
        """Calculate total achievement points"""
        completed = self.get_user_achievements(user_id)
        return sum(
            self.achievements[aid].points
            for aid in completed
        )

class TestAchievements(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.achievement_system = AchievementSystem()
        
        # Create test achievements
        self.achievements = [
            Achievement(
                id=1,
                name="First Gate",
                description="Clear your first gate",
                category=AchievementCategory.COMBAT,
                requirements={'gates_cleared': 1},
                reward=AchievementReward(crystals=100)
            ),
            Achievement(
                id=2,
                name="Gate Master",
                description="Clear 100 gates",
                category=AchievementCategory.COMBAT,
                requirements={'gates_cleared': 100},
                reward=AchievementReward(
                    crystals=1000,
                    title="Gate Master"
                )
            ),
            Achievement(
                id=3,
                name="Social Butterfly",
                description="Join a guild",
                category=AchievementCategory.SOCIAL,
                requirements={'guilds_joined': 1},
                reward=AchievementReward(exons=100)
            ),
            Achievement(
                id=4,
                name="Hidden Achievement",
                description="???",
                category=AchievementCategory.SPECIAL,
                requirements={'special_action': 1},
                reward=AchievementReward(
                    cosmetic_id=1
                ),
                hidden=True
            ),
            Achievement(
                id=5,
                name="Strength Training I",
                description="Reach 50 strength",
                category=AchievementCategory.PROGRESSION,
                requirements={'strength': 50},
                reward=AchievementReward(
                    stat_bonus={'strength': 5}
                ),
                sequential_id=None
            ),
            Achievement(
                id=6,
                name="Strength Training II",
                description="Reach 100 strength",
                category=AchievementCategory.PROGRESSION,
                requirements={'strength': 100},
                reward=AchievementReward(
                    stat_bonus={'strength': 10}
                ),
                sequential_id=5
            )
        ]
        
        # Register achievements
        for achievement in self.achievements:
            self.achievement_system.register_achievement(achievement)

    def test_basic_achievement(self):
        """Test basic achievement completion"""
        user_id = 1
        
        # Update progress
        completed = self.achievement_system.update_progress(
            user_id,
            1,  # First Gate achievement
            {'gates_cleared': 1}
        )
        
        # Verify completion
        self.assertTrue(completed)
        self.assertIn(1, self.achievement_system.get_user_achievements(user_id))

    def test_progress_tracking(self):
        """Test achievement progress tracking"""
        user_id = 1
        
        # Update progress partially
        self.achievement_system.update_progress(
            user_id,
            2,  # Gate Master achievement
            {'gates_cleared': 50}
        )
        
        # Verify progress
        progress = self.achievement_system.get_user_progress(user_id, 2)
        self.assertEqual(progress['gates_cleared'], 50)
        
        # Complete achievement
        completed = self.achievement_system.update_progress(
            user_id,
            2,
            {'gates_cleared': 50}  # Total 100
        )
        
        self.assertTrue(completed)

    def test_hidden_achievements(self):
        """Test hidden achievement handling"""
        user_id = 1
        
        # Get available achievements
        available = self.achievement_system.get_available_achievements(user_id)
        
        # Hidden achievement should not be visible
        hidden_ids = [a.id for a in available if a.hidden]
        self.assertEqual(len(hidden_ids), 0)
        
        # Complete hidden achievement
        completed = self.achievement_system.update_progress(
            user_id,
            4,  # Hidden achievement
            {'special_action': 1}
        )
        
        self.assertTrue(completed)

    def test_sequential_achievements(self):
        """Test sequential achievement chains"""
        user_id = 1
        
        # Try to complete second achievement first
        available = self.achievement_system.get_available_achievements(user_id)
        self.assertNotIn(6, [a.id for a in available])  # Strength Training II
        
        # Complete first achievement
        self.achievement_system.update_progress(
            user_id,
            5,  # Strength Training I
            {'strength': 50}
        )
        
        # Now second achievement should be available
        available = self.achievement_system.get_available_achievements(user_id)
        self.assertIn(6, [a.id for a in available])

    def test_achievement_points(self):
        """Test achievement points calculation"""
        user_id = 1
        
        # Complete some achievements
        self.achievement_system.update_progress(
            user_id,
            1,
            {'gates_cleared': 1}
        )
        self.achievement_system.update_progress(
            user_id,
            3,
            {'guilds_joined': 1}
        )
        
        # Calculate points
        points = self.achievement_system.calculate_total_points(user_id)
        self.assertEqual(points, 20)  # 10 points each

    def test_achievement_rewards(self):
        """Test achievement reward structure"""
        # Test different reward types
        crystal_reward = self.achievements[0].reward
        self.assertEqual(crystal_reward.crystals, 100)
        
        title_reward = self.achievements[1].reward
        self.assertEqual(title_reward.title, "Gate Master")
        
        stat_reward = self.achievements[4].reward
        self.assertEqual(stat_reward.stat_bonus['strength'], 5)

    def test_category_filtering(self):
        """Test achievement category filtering"""
        combat_achievements = [
            a for a in self.achievements
            if a.category == AchievementCategory.COMBAT
        ]
        self.assertEqual(len(combat_achievements), 2)
        
        progression_achievements = [
            a for a in self.achievements
            if a.category == AchievementCategory.PROGRESSION
        ]
        self.assertEqual(len(progression_achievements), 2)

    def test_multiple_requirements(self):
        """Test achievements with multiple requirements"""
        # Create achievement with multiple requirements
        complex_achievement = Achievement(
            id=7,
            name="Well-Rounded",
            description="Reach multiple milestones",
            category=AchievementCategory.MASTERY,
            requirements={
                'level': 50,
                'gates_cleared': 10,
                'guilds_joined': 1
            },
            reward=AchievementReward(crystals=500)
        )
        self.achievement_system.register_achievement(complex_achievement)
        
        user_id = 1
        
        # Update progress partially
        self.achievement_system.update_progress(
            user_id,
            7,
            {'level': 50, 'gates_cleared': 10}
        )
        
        # Should not be complete yet
        self.assertNotIn(7, self.achievement_system.get_user_achievements(user_id))
        
        # Complete final requirement
        completed = self.achievement_system.update_progress(
            user_id,
            7,
            {'guilds_joined': 1}
        )
        
        self.assertTrue(completed)

    def test_achievement_updates(self):
        """Test achievement progress updates"""
        user_id = 1
        
        # Update progress multiple times
        updates = [
            {'gates_cleared': 30},
            {'gates_cleared': 40},
            {'gates_cleared': 30}
        ]
        
        for update in updates:
            self.achievement_system.update_progress(
                user_id,
                2,  # Gate Master achievement
                update
            )
        
        # Verify total progress
        progress = self.achievement_system.get_user_progress(user_id, 2)
        self.assertEqual(progress['gates_cleared'], 100)

if __name__ == '__main__':
    unittest.main()
