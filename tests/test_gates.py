import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import uuid
import random

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class GateType(Enum):
    """Types of gates"""
    NORMAL = auto()
    ELITE = auto()
    BOSS = auto()
    EVENT = auto()
    CHALLENGE = auto()
    RAID = auto()

class GateState(Enum):
    """Gate instance states"""
    FORMING = auto()
    IN_PROGRESS = auto()
    COMPLETED = auto()
    FAILED = auto()
    EXPIRED = auto()

@dataclass
class GateRequirement:
    """Gate requirement data"""
    min_level: int
    max_level: Optional[int] = None
    item_requirements: Optional[Dict[str, int]] = None
    quest_requirements: Optional[List[str]] = None
    achievement_requirements: Optional[List[str]] = None

@dataclass
class GateReward:
    """Gate reward data"""
    experience: int
    items: Dict[str, float]  # item_id -> drop_rate
    currency: Dict[str, int]
    achievements: Optional[List[str]] = None

@dataclass
class GateTemplate:
    """Gate template data"""
    id: str
    name: str
    description: str
    type: GateType
    difficulty: int
    min_players: int
    max_players: int
    time_limit: timedelta
    requirements: GateRequirement
    rewards: GateReward
    cooldown: Optional[timedelta] = None

@dataclass
class GateInstance:
    """Gate instance data"""
    id: str
    template_id: str
    leader_id: int
    state: GateState
    players: Dict[int, datetime]  # user_id -> join_time
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    progress: float = 0.0
    rewards_claimed: Set[int] = None

class GateSystem:
    """System for gate management"""
    def __init__(self):
        self.templates: Dict[str, GateTemplate] = {}
        self.instances: Dict[str, GateInstance] = {}
        self.player_instances: Dict[int, str] = {}  # user_id -> instance_id
        self.cooldowns: Dict[int, Dict[str, datetime]] = {}  # user_id -> template_id -> last_clear

    def register_template(self, template: GateTemplate):
        """Register a gate template"""
        self.templates[template.id] = template

    def create_instance(
        self,
        template_id: str,
        leader_id: int
    ) -> Optional[str]:
        """Create a gate instance"""
        template = self.templates.get(template_id)
        if not template:
            return None
        
        if leader_id in self.player_instances:
            return None
        
        # Check cooldown
        if template.cooldown:
            last_clear = self.cooldowns.get(leader_id, {}).get(template_id)
            if last_clear and datetime.utcnow() - last_clear < template.cooldown:
                return None
        
        instance_id = str(uuid.uuid4())
        instance = GateInstance(
            id=instance_id,
            template_id=template_id,
            leader_id=leader_id,
            state=GateState.FORMING,
            players={leader_id: datetime.utcnow()},
            rewards_claimed=set()
        )
        
        self.instances[instance_id] = instance
        self.player_instances[leader_id] = instance_id
        
        return instance_id

    def join_instance(
        self,
        instance_id: str,
        player_id: int
    ) -> bool:
        """Join a gate instance"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        if instance.state != GateState.FORMING:
            return False
        
        template = self.templates[instance.template_id]
        if len(instance.players) >= template.max_players:
            return False
        
        if player_id in self.player_instances:
            return False
        
        instance.players[player_id] = datetime.utcnow()
        self.player_instances[player_id] = instance_id
        return True

    def leave_instance(self, player_id: int) -> bool:
        """Leave current gate instance"""
        instance_id = self.player_instances.get(player_id)
        if not instance_id:
            return False
        
        instance = self.instances[instance_id]
        if instance.state not in (GateState.FORMING, GateState.IN_PROGRESS):
            return False
        
        # Handle leader leaving
        if player_id == instance.leader_id:
            # Try to promote another player
            other_players = [
                pid for pid in instance.players.keys()
                if pid != player_id
            ]
            
            if other_players:
                instance.leader_id = other_players[0]
            else:
                # Close instance if no other players
                instance.state = GateState.EXPIRED
                for pid in list(instance.players.keys()):
                    del self.player_instances[pid]
                return True
        
        # Remove player
        del instance.players[player_id]
        del self.player_instances[player_id]
        return True

    def start_instance(self, instance_id: str) -> bool:
        """Start a gate instance"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        if instance.state != GateState.FORMING:
            return False
        
        template = self.templates[instance.template_id]
        if len(instance.players) < template.min_players:
            return False
        
        instance.state = GateState.IN_PROGRESS
        instance.started_at = datetime.utcnow()
        return True

    def update_progress(
        self,
        instance_id: str,
        progress: float
    ) -> bool:
        """Update gate progress"""
        instance = self.instances.get(instance_id)
        if not instance:
            return False
        
        if instance.state != GateState.IN_PROGRESS:
            return False
        
        instance.progress = min(1.0, max(0.0, progress))
        
        if instance.progress >= 1.0:
            instance.state = GateState.COMPLETED
            instance.completed_at = datetime.utcnow()
            
            # Update cooldowns
            template = self.templates[instance.template_id]
            if template.cooldown:
                for player_id in instance.players:
                    if player_id not in self.cooldowns:
                        self.cooldowns[player_id] = {}
                    self.cooldowns[player_id][template.id] = datetime.utcnow()
        
        return True

    def claim_rewards(
        self,
        instance_id: str,
        player_id: int
    ) -> Optional[Dict[str, Any]]:
        """Claim gate rewards"""
        instance = self.instances.get(instance_id)
        if not instance:
            return None
        
        if instance.state != GateState.COMPLETED:
            return None
        
        if player_id not in instance.players:
            return None
        
        if player_id in instance.rewards_claimed:
            return None
        
        template = self.templates[instance.template_id]
        rewards = {
            'experience': template.rewards.experience,
            'currency': template.rewards.currency.copy(),
            'items': {}
        }
        
        # Roll for item drops
        for item_id, drop_rate in template.rewards.items.items():
            if random.random() < drop_rate:
                rewards['items'][item_id] = 1
        
        instance.rewards_claimed.add(player_id)
        return rewards

    def get_instance(self, instance_id: str) -> Optional[GateInstance]:
        """Get gate instance"""
        return self.instances.get(instance_id)

    def get_player_instance(self, player_id: int) -> Optional[GateInstance]:
        """Get player's current instance"""
        instance_id = self.player_instances.get(player_id)
        if not instance_id:
            return None
        return self.instances.get(instance_id)

class TestGates(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.gate_system = GateSystem()
        
        # Register test template
        self.test_template = GateTemplate(
            id="test_gate",
            name="Test Gate",
            description="A test gate",
            type=GateType.NORMAL,
            difficulty=1,
            min_players=2,
            max_players=4,
            time_limit=timedelta(minutes=30),
            requirements=GateRequirement(min_level=1),
            rewards=GateReward(
                experience=1000,
                items={"item_1": 0.5},
                currency={"gold": 100}
            )
        )
        
        self.gate_system.register_template(self.test_template)

    def test_instance_creation(self):
        """Test gate instance creation"""
        # Create instance
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        
        # Verify creation
        self.assertIsNotNone(instance_id)
        instance = self.gate_system.get_instance(instance_id)
        self.assertEqual(instance.template_id, "test_gate")
        self.assertEqual(instance.leader_id, 1)
        self.assertEqual(instance.state, GateState.FORMING)

    def test_instance_joining(self):
        """Test gate instance joining"""
        # Create instance
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        
        # Join instance
        success = self.gate_system.join_instance(instance_id, 2)
        self.assertTrue(success)
        
        # Verify join
        instance = self.gate_system.get_instance(instance_id)
        self.assertIn(2, instance.players)

    def test_instance_leaving(self):
        """Test gate instance leaving"""
        # Create instance with players
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        self.gate_system.join_instance(instance_id, 2)
        
        # Player leaves
        success = self.gate_system.leave_instance(2)
        self.assertTrue(success)
        
        # Verify leave
        instance = self.gate_system.get_instance(instance_id)
        self.assertNotIn(2, instance.players)

    def test_instance_starting(self):
        """Test gate instance starting"""
        # Create instance with minimum players
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        self.gate_system.join_instance(instance_id, 2)
        
        # Start instance
        success = self.gate_system.start_instance(instance_id)
        self.assertTrue(success)
        
        # Verify start
        instance = self.gate_system.get_instance(instance_id)
        self.assertEqual(instance.state, GateState.IN_PROGRESS)
        self.assertIsNotNone(instance.started_at)

    def test_progress_tracking(self):
        """Test gate progress tracking"""
        # Create and start instance
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        self.gate_system.join_instance(instance_id, 2)
        self.gate_system.start_instance(instance_id)
        
        # Update progress
        success = self.gate_system.update_progress(instance_id, 0.5)
        self.assertTrue(success)
        
        # Verify progress
        instance = self.gate_system.get_instance(instance_id)
        self.assertEqual(instance.progress, 0.5)

    def test_completion_handling(self):
        """Test gate completion handling"""
        # Create and start instance
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        self.gate_system.join_instance(instance_id, 2)
        self.gate_system.start_instance(instance_id)
        
        # Complete instance
        self.gate_system.update_progress(instance_id, 1.0)
        
        # Verify completion
        instance = self.gate_system.get_instance(instance_id)
        self.assertEqual(instance.state, GateState.COMPLETED)
        self.assertIsNotNone(instance.completed_at)

    def test_reward_claiming(self):
        """Test reward claiming"""
        # Create and complete instance
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        self.gate_system.join_instance(instance_id, 2)
        self.gate_system.start_instance(instance_id)
        self.gate_system.update_progress(instance_id, 1.0)
        
        # Claim rewards
        rewards = self.gate_system.claim_rewards(instance_id, 1)
        
        # Verify rewards
        self.assertIsNotNone(rewards)
        self.assertEqual(rewards['experience'], 1000)
        self.assertEqual(rewards['currency']['gold'], 100)

    def test_cooldown_handling(self):
        """Test gate cooldown handling"""
        # Create template with cooldown
        template = GateTemplate(
            id="cooldown_gate",
            name="Cooldown Gate",
            description="A gate with cooldown",
            type=GateType.NORMAL,
            difficulty=1,
            min_players=1,
            max_players=4,
            time_limit=timedelta(minutes=30),
            requirements=GateRequirement(min_level=1),
            rewards=GateReward(
                experience=1000,
                items={},
                currency={}
            ),
            cooldown=timedelta(minutes=1)
        )
        
        self.gate_system.register_template(template)
        
        # Complete gate
        instance_id = self.gate_system.create_instance(
            "cooldown_gate",
            1
        )
        self.gate_system.start_instance(instance_id)
        self.gate_system.update_progress(instance_id, 1.0)
        
        # Try to create new instance
        instance_id = self.gate_system.create_instance(
            "cooldown_gate",
            1
        )
        self.assertIsNone(instance_id)

    def test_leader_leaving(self):
        """Test leader leaving handling"""
        # Create instance with players
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        self.gate_system.join_instance(instance_id, 2)
        
        # Leader leaves
        self.gate_system.leave_instance(1)
        
        # Verify new leader
        instance = self.gate_system.get_instance(instance_id)
        self.assertEqual(instance.leader_id, 2)

    def test_player_limits(self):
        """Test player limit handling"""
        # Create instance
        instance_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        
        # Fill to max players
        for i in range(2, 5):
            if i <= self.test_template.max_players:
                success = self.gate_system.join_instance(instance_id, i)
                self.assertTrue(success)
            else:
                success = self.gate_system.join_instance(instance_id, i)
                self.assertFalse(success)

    def test_multiple_instances(self):
        """Test multiple instance handling"""
        # Create two instances
        instance1_id = self.gate_system.create_instance(
            "test_gate",
            1
        )
        instance2_id = self.gate_system.create_instance(
            "test_gate",
            2
        )
        
        # Try to join both
        success = self.gate_system.join_instance(instance1_id, 3)
        self.assertTrue(success)
        
        success = self.gate_system.join_instance(instance2_id, 3)
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
