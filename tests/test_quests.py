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

class QuestType(Enum):
    """Types of quests"""
    KILL = auto()
    COLLECT = auto()
    EXPLORE = auto()
    CRAFT = auto()
    TRADE = auto()
    ESCORT = auto()
    DEFEND = auto()
    GUILD = auto()
    DAILY = auto()
    WEEKLY = auto()

class QuestStatus(Enum):
    """Quest status states"""
    AVAILABLE = auto()
    ACTIVE = auto()
    COMPLETED = auto()
    FAILED = auto()
    EXPIRED = auto()

@dataclass
class QuestReward:
    """Quest reward data"""
    experience: int = 0
    crystals: int = 0
    exons: int = 0
    items: List[Dict] = None
    reputation: Dict[str, int] = None

@dataclass
class QuestRequirement:
    """Quest requirement data"""
    type: str
    target: str
    amount: int
    current: int = 0

@dataclass
class Quest:
    """Quest data"""
    id: int
    name: str
    description: str
    type: QuestType
    level: int
    requirements: List[QuestRequirement]
    reward: QuestReward
    time_limit: Optional[timedelta] = None
    repeatable: bool = False
    prerequisites: List[int] = None  # Quest IDs
    chain_id: Optional[int] = None  # For quest chains
    guild_id: Optional[int] = None  # For guild quests

class QuestSystem:
    """Manages game quests"""
    def __init__(self):
        self.quests: Dict[int, Quest] = {}
        self.active_quests: Dict[int, Dict[int, Quest]] = {}  # user_id -> quest_id -> quest
        self.completed_quests: Dict[int, Set[int]] = {}  # user_id -> quest_ids
        self.quest_progress: Dict[int, Dict[int, List[QuestRequirement]]] = {}  # user_id -> quest_id -> requirements

    def register_quest(self, quest: Quest):
        """Register a new quest"""
        self.quests[quest.id] = quest

    def get_available_quests(self, user_id: int, level: int) -> List[Quest]:
        """Get available quests for user"""
        available = []
        completed = self.completed_quests.get(user_id, set())
        active = self.active_quests.get(user_id, {}).keys()
        
        for quest in self.quests.values():
            if quest.level <= level and quest.id not in completed and quest.id not in active:
                if not quest.prerequisites or all(q in completed for q in quest.prerequisites):
                    available.append(quest)
        
        return available

    def accept_quest(self, user_id: int, quest_id: int) -> bool:
        """Accept a quest"""
        if quest_id not in self.quests:
            return False
        
        quest = self.quests[quest_id]
        
        # Initialize tracking
        if user_id not in self.active_quests:
            self.active_quests[user_id] = {}
        if user_id not in self.quest_progress:
            self.quest_progress[user_id] = {}
        
        # Start quest
        self.active_quests[user_id][quest_id] = quest
        self.quest_progress[user_id][quest_id] = [
            QuestRequirement(
                type=req.type,
                target=req.target,
                amount=req.amount,
                current=0
            )
            for req in quest.requirements
        ]
        
        return True

    def update_progress(
        self,
        user_id: int,
        quest_id: int,
        requirement_type: str,
        target: str,
        amount: int
    ) -> bool:
        """Update quest progress"""
        if user_id not in self.quest_progress or quest_id not in self.quest_progress[user_id]:
            return False
        
        requirements = self.quest_progress[user_id][quest_id]
        updated = False
        
        for req in requirements:
            if req.type == requirement_type and req.target == target:
                req.current += amount
                updated = True
        
        if updated:
            return self._check_completion(user_id, quest_id)
        
        return False

    def _check_completion(self, user_id: int, quest_id: int) -> bool:
        """Check if quest is completed"""
        requirements = self.quest_progress[user_id][quest_id]
        
        if all(req.current >= req.amount for req in requirements):
            if user_id not in self.completed_quests:
                self.completed_quests[user_id] = set()
            
            self.completed_quests[user_id].add(quest_id)
            del self.active_quests[user_id][quest_id]
            del self.quest_progress[user_id][quest_id]
            return True
        
        return False

    def abandon_quest(self, user_id: int, quest_id: int):
        """Abandon a quest"""
        if user_id in self.active_quests and quest_id in self.active_quests[user_id]:
            del self.active_quests[user_id][quest_id]
            del self.quest_progress[user_id][quest_id]

class TestQuests(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.quest_system = QuestSystem()
        
        # Create test quests
        self.quests = [
            Quest(
                id=1,
                name="Beginner's Trial",
                description="Defeat 5 slimes",
                type=QuestType.KILL,
                level=1,
                requirements=[
                    QuestRequirement(
                        type='kill',
                        target='slime',
                        amount=5
                    )
                ],
                reward=QuestReward(
                    experience=100,
                    crystals=50
                )
            ),
            Quest(
                id=2,
                name="Advanced Combat",
                description="Defeat a boss monster",
                type=QuestType.KILL,
                level=10,
                requirements=[
                    QuestRequirement(
                        type='kill',
                        target='boss',
                        amount=1
                    )
                ],
                reward=QuestReward(
                    experience=500,
                    crystals=200,
                    items=[{'id': 1, 'amount': 1}]
                ),
                prerequisites=[1]
            ),
            Quest(
                id=3,
                name="Daily Gathering",
                description="Collect 10 herbs",
                type=QuestType.DAILY,
                level=1,
                requirements=[
                    QuestRequirement(
                        type='collect',
                        target='herb',
                        amount=10
                    )
                ],
                reward=QuestReward(
                    crystals=100
                ),
                time_limit=timedelta(days=1),
                repeatable=True
            )
        ]
        
        # Register quests
        for quest in self.quests:
            self.quest_system.register_quest(quest)

    def test_basic_quest(self):
        """Test basic quest functionality"""
        user_id = 1
        
        # Accept quest
        accepted = self.quest_system.accept_quest(user_id, 1)
        self.assertTrue(accepted)
        
        # Update progress
        completed = self.quest_system.update_progress(
            user_id,
            1,
            'kill',
            'slime',
            5
        )
        
        # Verify completion
        self.assertTrue(completed)
        self.assertIn(1, self.quest_system.completed_quests[user_id])

    def test_quest_prerequisites(self):
        """Test quest prerequisites"""
        user_id = 1
        
        # Try to accept advanced quest first
        available = self.quest_system.get_available_quests(user_id, 10)
        self.assertNotIn(2, [q.id for q in available])
        
        # Complete prerequisite quest
        self.quest_system.accept_quest(user_id, 1)
        self.quest_system.update_progress(user_id, 1, 'kill', 'slime', 5)
        
        # Now advanced quest should be available
        available = self.quest_system.get_available_quests(user_id, 10)
        self.assertIn(2, [q.id for q in available])

    def test_daily_quest(self):
        """Test daily quest mechanics"""
        user_id = 1
        
        # Accept daily quest
        self.quest_system.accept_quest(user_id, 3)
        
        # Complete quest
        completed = self.quest_system.update_progress(
            user_id,
            3,
            'collect',
            'herb',
            10
        )
        self.assertTrue(completed)
        
        # Should be available again (repeatable)
        available = self.quest_system.get_available_quests(user_id, 1)
        self.assertIn(3, [q.id for q in available])

    def test_quest_abandonment(self):
        """Test quest abandonment"""
        user_id = 1
        
        # Accept quest
        self.quest_system.accept_quest(user_id, 1)
        
        # Abandon quest
        self.quest_system.abandon_quest(user_id, 1)
        
        # Verify quest removed
        self.assertNotIn(1, self.quest_system.active_quests[user_id])
        self.assertNotIn(1, self.quest_system.quest_progress[user_id])

    def test_multiple_requirements(self):
        """Test quests with multiple requirements"""
        # Create complex quest
        complex_quest = Quest(
            id=4,
            name="Complex Task",
            description="Multiple objectives",
            type=QuestType.COLLECT,
            level=5,
            requirements=[
                QuestRequirement(
                    type='collect',
                    target='wood',
                    amount=10
                ),
                QuestRequirement(
                    type='collect',
                    target='stone',
                    amount=5
                )
            ],
            reward=QuestReward(experience=200)
        )
        self.quest_system.register_quest(complex_quest)
        
        user_id = 1
        self.quest_system.accept_quest(user_id, 4)
        
        # Complete first requirement
        self.quest_system.update_progress(user_id, 4, 'collect', 'wood', 10)
        self.assertNotIn(4, self.quest_system.completed_quests.get(user_id, set()))
        
        # Complete second requirement
        completed = self.quest_system.update_progress(
            user_id,
            4,
            'collect',
            'stone',
            5
        )
        self.assertTrue(completed)

    def test_level_requirements(self):
        """Test quest level requirements"""
        user_id = 1
        
        # Get available quests for level 1
        available = self.quest_system.get_available_quests(user_id, 1)
        quest_ids = [q.id for q in available]
        
        # Should include level 1 quests but not level 10
        self.assertIn(1, quest_ids)
        self.assertNotIn(2, quest_ids)
        
        # Get available quests for level 10
        available = self.quest_system.get_available_quests(user_id, 10)
        quest_ids = [q.id for q in available]
        
        # Should include both quests
        self.assertIn(1, quest_ids)
        self.assertIn(2, quest_ids)

    def test_quest_progress_tracking(self):
        """Test quest progress tracking"""
        user_id = 1
        
        # Accept quest
        self.quest_system.accept_quest(user_id, 1)
        
        # Update progress partially
        self.quest_system.update_progress(user_id, 1, 'kill', 'slime', 3)
        
        # Check progress
        progress = self.quest_system.quest_progress[user_id][1]
        requirement = progress[0]
        self.assertEqual(requirement.current, 3)
        self.assertEqual(requirement.amount, 5)

    def test_quest_rewards(self):
        """Test quest reward structure"""
        # Test different reward types
        basic_reward = self.quests[0].reward
        self.assertEqual(basic_reward.experience, 100)
        self.assertEqual(basic_reward.crystals, 50)
        
        advanced_reward = self.quests[1].reward
        self.assertIsNotNone(advanced_reward.items)
        self.assertEqual(len(advanced_reward.items), 1)

    def test_quest_types(self):
        """Test different quest types"""
        kill_quests = [
            q for q in self.quests
            if q.type == QuestType.KILL
        ]
        self.assertEqual(len(kill_quests), 2)
        
        daily_quests = [
            q for q in self.quests
            if q.type == QuestType.DAILY
        ]
        self.assertEqual(len(daily_quests), 1)

if __name__ == '__main__':
    unittest.main()
