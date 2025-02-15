import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from enum import Enum, auto
import random
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class RewardType(Enum):
    """Types of rewards"""
    CRYSTAL = auto()
    EXON = auto()
    ITEM = auto()
    EXPERIENCE = auto()
    SKILL_POINT = auto()
    ACHIEVEMENT = auto()
    TITLE = auto()
    COSMETIC = auto()

class RewardTrigger(Enum):
    """Reward trigger types"""
    LEVEL_UP = auto()
    QUEST_COMPLETE = auto()
    ACHIEVEMENT = auto()
    DAILY_LOGIN = auto()
    GATE_CLEAR = auto()
    MILESTONE = auto()
    EVENT = auto()
    REFERRAL = auto()

@dataclass
class RewardItem:
    """Reward item data"""
    type: RewardType
    amount: float
    item_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class RewardTemplate:
    """Reward template data"""
    id: str
    name: str
    description: str
    trigger: RewardTrigger
    items: List[RewardItem]
    conditions: Optional[Dict[str, Any]] = None
    cooldown: Optional[timedelta] = None
    expiry: Optional[datetime] = None

@dataclass
class RewardInstance:
    """Reward instance data"""
    id: str
    template_id: str
    user_id: int
    status: str
    items: List[RewardItem]
    claimed_at: Optional[datetime] = None
    expires_at: Optional[datetime] = None

class RewardSystem:
    """System for reward management"""
    def __init__(self):
        self.templates: Dict[str, RewardTemplate] = {}
        self.instances: Dict[str, RewardInstance] = {}
        self.user_rewards: Dict[int, List[str]] = {}
        self.claim_history: Dict[int, Dict[str, datetime]] = {}

    def register_template(self, template: RewardTemplate):
        """Register a reward template"""
        self.templates[template.id] = template

    def create_reward(
        self,
        template_id: str,
        user_id: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a reward instance"""
        template = self.templates.get(template_id)
        if not template:
            return None
        
        # Check conditions
        if template.conditions and context:
            if not all(
                context.get(k) == v
                for k, v in template.conditions.items()
            ):
                return None
        
        # Check cooldown
        if template.cooldown:
            last_claim = self.claim_history.get(user_id, {}).get(template_id)
            if last_claim and datetime.utcnow() - last_claim < template.cooldown:
                return None
        
        # Create instance
        instance_id = f"reward_{len(self.instances)}"
        instance = RewardInstance(
            id=instance_id,
            template_id=template_id,
            user_id=user_id,
            status="pending",
            items=template.items.copy(),
            expires_at=template.expiry
        )
        
        self.instances[instance_id] = instance
        if user_id not in self.user_rewards:
            self.user_rewards[user_id] = []
        self.user_rewards[user_id].append(instance_id)
        
        return instance_id

    def claim_reward(
        self,
        instance_id: str,
        user_id: int
    ) -> Optional[List[RewardItem]]:
        """Claim a reward instance"""
        instance = self.instances.get(instance_id)
        if not instance:
            return None
        
        if instance.user_id != user_id:
            return None
        
        if instance.status != "pending":
            return None
        
        if instance.expires_at and datetime.utcnow() > instance.expires_at:
            instance.status = "expired"
            return None
        
        # Update claim history
        if user_id not in self.claim_history:
            self.claim_history[user_id] = {}
        self.claim_history[user_id][instance.template_id] = datetime.utcnow()
        
        # Mark as claimed
        instance.status = "claimed"
        instance.claimed_at = datetime.utcnow()
        
        return instance.items

    def get_available_rewards(
        self,
        user_id: int
    ) -> List[RewardInstance]:
        """Get available rewards for user"""
        if user_id not in self.user_rewards:
            return []
        
        rewards = []
        for instance_id in self.user_rewards[user_id]:
            instance = self.instances[instance_id]
            if instance.status == "pending":
                if not instance.expires_at or datetime.utcnow() <= instance.expires_at:
                    rewards.append(instance)
        
        return rewards

    def get_reward_history(
        self,
        user_id: int,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[RewardInstance]:
        """Get reward history for user"""
        if user_id not in self.user_rewards:
            return []
        
        history = []
        for instance_id in self.user_rewards[user_id]:
            instance = self.instances[instance_id]
            if instance.status == "claimed":
                if start_time and instance.claimed_at < start_time:
                    continue
                if end_time and instance.claimed_at > end_time:
                    continue
                history.append(instance)
        
        return sorted(history, key=lambda x: x.claimed_at)

class TestRewards(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.rewards = RewardSystem()
        
        # Register test templates
        self.daily_login = RewardTemplate(
            id="daily_login",
            name="Daily Login Reward",
            description="Reward for daily login",
            trigger=RewardTrigger.DAILY_LOGIN,
            items=[
                RewardItem(
                    type=RewardType.CRYSTAL,
                    amount=100
                )
            ],
            cooldown=timedelta(days=1)
        )
        
        self.level_up = RewardTemplate(
            id="level_up",
            name="Level Up Reward",
            description="Reward for leveling up",
            trigger=RewardTrigger.LEVEL_UP,
            items=[
                RewardItem(
                    type=RewardType.SKILL_POINT,
                    amount=1
                ),
                RewardItem(
                    type=RewardType.ITEM,
                    amount=1,
                    item_id="potion_1"
                )
            ],
            conditions={"level": 10}
        )
        
        self.rewards.register_template(self.daily_login)
        self.rewards.register_template(self.level_up)

    def test_reward_creation(self):
        """Test reward creation"""
        # Create reward
        instance_id = self.rewards.create_reward(
            "daily_login",
            1
        )
        
        # Verify creation
        self.assertIsNotNone(instance_id)
        instance = self.rewards.instances[instance_id]
        self.assertEqual(instance.template_id, "daily_login")
        self.assertEqual(instance.status, "pending")

    def test_reward_claiming(self):
        """Test reward claiming"""
        # Create and claim reward
        instance_id = self.rewards.create_reward(
            "daily_login",
            1
        )
        
        items = self.rewards.claim_reward(instance_id, 1)
        
        # Verify claim
        self.assertIsNotNone(items)
        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].type, RewardType.CRYSTAL)
        self.assertEqual(items[0].amount, 100)
        
        # Verify instance status
        instance = self.rewards.instances[instance_id]
        self.assertEqual(instance.status, "claimed")
        self.assertIsNotNone(instance.claimed_at)

    def test_reward_conditions(self):
        """Test reward conditions"""
        # Try without meeting conditions
        instance_id = self.rewards.create_reward(
            "level_up",
            1,
            {"level": 5}
        )
        
        self.assertIsNone(instance_id)
        
        # Try with conditions met
        instance_id = self.rewards.create_reward(
            "level_up",
            1,
            {"level": 10}
        )
        
        self.assertIsNotNone(instance_id)

    def test_reward_cooldown(self):
        """Test reward cooldown"""
        # Claim first reward
        instance_id = self.rewards.create_reward(
            "daily_login",
            1
        )
        self.rewards.claim_reward(instance_id, 1)
        
        # Try to create another reward
        instance_id = self.rewards.create_reward(
            "daily_login",
            1
        )
        
        self.assertIsNone(instance_id)

    def test_reward_expiry(self):
        """Test reward expiry"""
        # Create expiring reward
        template = RewardTemplate(
            id="expiring",
            name="Expiring Reward",
            description="Reward that expires",
            trigger=RewardTrigger.EVENT,
            items=[
                RewardItem(
                    type=RewardType.CRYSTAL,
                    amount=100
                )
            ],
            expiry=datetime.utcnow() + timedelta(seconds=1)
        )
        
        self.rewards.register_template(template)
        instance_id = self.rewards.create_reward("expiring", 1)
        
        # Wait for expiry
        import time
        time.sleep(1.1)
        
        # Try to claim
        items = self.rewards.claim_reward(instance_id, 1)
        self.assertIsNone(items)
        
        # Verify status
        instance = self.rewards.instances[instance_id]
        self.assertEqual(instance.status, "expired")

    def test_reward_history(self):
        """Test reward history"""
        # Create and claim multiple rewards
        for _ in range(3):
            instance_id = self.rewards.create_reward(
                "daily_login",
                1
            )
            self.rewards.claim_reward(instance_id, 1)
            time.sleep(0.1)  # Ensure different timestamps
        
        # Get history
        history = self.rewards.get_reward_history(1)
        
        # Verify history
        self.assertEqual(len(history), 3)
        self.assertTrue(
            all(r.status == "claimed" for r in history)
        )
        self.assertEqual(
            [r.template_id for r in history],
            ["daily_login"] * 3
        )

    def test_available_rewards(self):
        """Test available rewards listing"""
        # Create multiple rewards
        self.rewards.create_reward("daily_login", 1)
        self.rewards.create_reward(
            "level_up",
            1,
            {"level": 10}
        )
        
        # Get available rewards
        available = self.rewards.get_available_rewards(1)
        
        # Verify available rewards
        self.assertEqual(len(available), 2)
        self.assertTrue(
            all(r.status == "pending" for r in available)
        )

    def test_multiple_users(self):
        """Test rewards for multiple users"""
        # Create rewards for different users
        instance1 = self.rewards.create_reward("daily_login", 1)
        instance2 = self.rewards.create_reward("daily_login", 2)
        
        # Try to claim wrong reward
        items = self.rewards.claim_reward(instance1, 2)
        self.assertIsNone(items)
        
        # Claim correct reward
        items = self.rewards.claim_reward(instance2, 2)
        self.assertIsNotNone(items)

if __name__ == '__main__':
    unittest.main()
