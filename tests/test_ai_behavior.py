import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import math
import random

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class AIState(Enum):
    """AI behavior states"""
    IDLE = auto()
    PATROL = auto()
    CHASE = auto()
    ATTACK = auto()
    FLEE = auto()
    RETURN = auto()
    INTERACT = auto()
    DEAD = auto()

class AIPersonality(Enum):
    """AI personality types"""
    AGGRESSIVE = auto()
    DEFENSIVE = auto()
    CAUTIOUS = auto()
    SOCIAL = auto()
    COWARDLY = auto()
    CURIOUS = auto()

@dataclass
class Vector2:
    """2D vector"""
    x: float
    y: float

    def distance_to(self, other: 'Vector2') -> float:
        return math.sqrt(
            (self.x - other.x) ** 2 +
            (self.y - other.y) ** 2
        )

    def direction_to(self, other: 'Vector2') -> 'Vector2':
        dx = other.x - self.x
        dy = other.y - self.y
        length = math.sqrt(dx * dx + dy * dy)
        if length == 0:
            return Vector2(0, 0)
        return Vector2(dx / length, dy / length)

@dataclass
class AITarget:
    """AI target data"""
    id: int
    position: Vector2
    type: str
    threat_level: float = 0
    is_hostile: bool = False

@dataclass
class AIMemory:
    """AI memory data"""
    target_id: int
    last_position: Vector2
    last_seen: datetime
    threat_level: float
    interaction_count: int = 0

@dataclass
class AIBehavior:
    """AI behavior configuration"""
    personality: AIPersonality
    aggression: float
    caution: float
    social: float
    curiosity: float
    memory_duration: timedelta
    vision_range: float
    attack_range: float
    chase_range: float
    flee_threshold: float
    home_position: Vector2

class AISystem:
    """System for AI behavior management"""
    def __init__(self):
        self.behaviors: Dict[int, AIBehavior] = {}
        self.states: Dict[int, AIState] = {}
        self.positions: Dict[int, Vector2] = {}
        self.memories: Dict[int, Dict[int, AIMemory]] = {}
        self.current_targets: Dict[int, Optional[AITarget]] = {}

    def register_ai(
        self,
        entity_id: int,
        behavior: AIBehavior,
        position: Vector2
    ):
        """Register an AI entity"""
        self.behaviors[entity_id] = behavior
        self.states[entity_id] = AIState.IDLE
        self.positions[entity_id] = position
        self.memories[entity_id] = {}
        self.current_targets[entity_id] = None

    def update_position(self, entity_id: int, position: Vector2):
        """Update AI entity position"""
        self.positions[entity_id] = position

    def process_perception(
        self,
        entity_id: int,
        visible_targets: List[AITarget]
    ):
        """Process AI perception of targets"""
        behavior = self.behaviors.get(entity_id)
        if not behavior:
            return
        
        position = self.positions[entity_id]
        now = datetime.utcnow()
        
        # Update memories
        for target in visible_targets:
            if target.id not in self.memories[entity_id]:
                self.memories[entity_id][target.id] = AIMemory(
                    target_id=target.id,
                    last_position=target.position,
                    last_seen=now,
                    threat_level=target.threat_level
                )
            else:
                memory = self.memories[entity_id][target.id]
                memory.last_position = target.position
                memory.last_seen = now
                memory.threat_level = max(
                    memory.threat_level,
                    target.threat_level
                )
        
        # Clean old memories
        self.memories[entity_id] = {
            tid: memory
            for tid, memory in self.memories[entity_id].items()
            if now - memory.last_seen <= behavior.memory_duration
        }
        
        # Select target based on personality
        best_target = None
        best_score = float('-inf')
        
        for target in visible_targets:
            distance = position.distance_to(target.position)
            if distance > behavior.vision_range:
                continue
            
            score = 0
            
            # Personality-based scoring
            if behavior.personality == AIPersonality.AGGRESSIVE:
                score += target.threat_level * behavior.aggression
            elif behavior.personality == AIPersonality.DEFENSIVE:
                score += (1 - target.threat_level) * behavior.caution
            elif behavior.personality == AIPersonality.SOCIAL:
                score += (not target.is_hostile) * behavior.social
            elif behavior.personality == AIPersonality.COWARDLY:
                score -= target.threat_level * behavior.caution
            elif behavior.personality == AIPersonality.CURIOUS:
                memory = self.memories[entity_id].get(target.id)
                if memory:
                    score += (1 / (memory.interaction_count + 1)) * behavior.curiosity
            
            # Distance penalty
            score -= distance / behavior.vision_range
            
            if score > best_score:
                best_score = score
                best_target = target
        
        self.current_targets[entity_id] = best_target

    def update_state(self, entity_id: int):
        """Update AI state"""
        behavior = self.behaviors.get(entity_id)
        if not behavior:
            return
        
        current_state = self.states[entity_id]
        if current_state == AIState.DEAD:
            return
        
        position = self.positions[entity_id]
        target = self.current_targets[entity_id]
        
        # State transitions
        if target:
            distance = position.distance_to(target.position)
            
            if target.threat_level >= behavior.flee_threshold:
                self.states[entity_id] = AIState.FLEE
            elif distance <= behavior.attack_range:
                self.states[entity_id] = AIState.ATTACK
            elif distance <= behavior.chase_range:
                self.states[entity_id] = AIState.CHASE
            else:
                home_distance = position.distance_to(behavior.home_position)
                if home_distance > behavior.vision_range:
                    self.states[entity_id] = AIState.RETURN
                else:
                    self.states[entity_id] = AIState.PATROL
        else:
            home_distance = position.distance_to(behavior.home_position)
            if home_distance > behavior.vision_range:
                self.states[entity_id] = AIState.RETURN
            else:
                self.states[entity_id] = AIState.PATROL

    def get_movement_direction(self, entity_id: int) -> Optional[Vector2]:
        """Get AI movement direction"""
        state = self.states.get(entity_id)
        if not state or state == AIState.DEAD:
            return None
        
        position = self.positions[entity_id]
        behavior = self.behaviors[entity_id]
        target = self.current_targets[entity_id]
        
        if state == AIState.FLEE and target:
            # Move away from target
            direction = target.position.direction_to(position)
            return direction
        elif state == AIState.CHASE and target:
            # Move toward target
            direction = position.direction_to(target.position)
            return direction
        elif state == AIState.RETURN:
            # Move toward home
            direction = position.direction_to(behavior.home_position)
            return direction
        elif state == AIState.PATROL:
            # Random patrol movement
            angle = random.uniform(0, 2 * math.pi)
            return Vector2(math.cos(angle), math.sin(angle))
        
        return None

class TestAIBehavior(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.ai_system = AISystem()
        
        # Create test behavior
        self.test_behavior = AIBehavior(
            personality=AIPersonality.AGGRESSIVE,
            aggression=0.8,
            caution=0.2,
            social=0.3,
            curiosity=0.4,
            memory_duration=timedelta(minutes=5),
            vision_range=10.0,
            attack_range=2.0,
            chase_range=5.0,
            flee_threshold=0.8,
            home_position=Vector2(0, 0)
        )

    def test_ai_registration(self):
        """Test AI registration"""
        # Register AI
        self.ai_system.register_ai(
            1,
            self.test_behavior,
            Vector2(0, 0)
        )
        
        # Verify registration
        self.assertIn(1, self.ai_system.behaviors)
        self.assertEqual(self.ai_system.states[1], AIState.IDLE)

    def test_target_perception(self):
        """Test target perception"""
        # Register AI
        self.ai_system.register_ai(
            1,
            self.test_behavior,
            Vector2(0, 0)
        )
        
        # Create visible targets
        targets = [
            AITarget(
                id=2,
                position=Vector2(3, 4),
                type="player",
                threat_level=0.5,
                is_hostile=True
            )
        ]
        
        # Process perception
        self.ai_system.process_perception(1, targets)
        
        # Verify target selection
        target = self.ai_system.current_targets[1]
        self.assertIsNotNone(target)
        self.assertEqual(target.id, 2)

    def test_state_transitions(self):
        """Test AI state transitions"""
        # Register AI
        self.ai_system.register_ai(
            1,
            self.test_behavior,
            Vector2(0, 0)
        )
        
        # Create target within attack range
        target = AITarget(
            id=2,
            position=Vector2(1, 1),
            type="player",
            threat_level=0.5
        )
        
        self.ai_system.current_targets[1] = target
        
        # Update state
        self.ai_system.update_state(1)
        
        # Verify attack state
        self.assertEqual(
            self.ai_system.states[1],
            AIState.ATTACK
        )

    def test_movement_direction(self):
        """Test movement direction calculation"""
        # Register AI
        self.ai_system.register_ai(
            1,
            self.test_behavior,
            Vector2(0, 0)
        )
        
        # Set chase state with target
        self.ai_system.states[1] = AIState.CHASE
        self.ai_system.current_targets[1] = AITarget(
            id=2,
            position=Vector2(3, 4),
            type="player"
        )
        
        # Get movement direction
        direction = self.ai_system.get_movement_direction(1)
        
        # Verify direction
        self.assertIsNotNone(direction)
        self.assertAlmostEqual(
            direction.x,
            0.6,
            places=1
        )
        self.assertAlmostEqual(
            direction.y,
            0.8,
            places=1
        )

    def test_memory_system(self):
        """Test AI memory system"""
        # Register AI
        self.ai_system.register_ai(
            1,
            self.test_behavior,
            Vector2(0, 0)
        )
        
        # Create target
        target = AITarget(
            id=2,
            position=Vector2(3, 4),
            type="player",
            threat_level=0.5
        )
        
        # Process perception
        self.ai_system.process_perception(1, [target])
        
        # Verify memory creation
        memory = self.ai_system.memories[1][2]
        self.assertEqual(memory.target_id, 2)
        self.assertEqual(
            memory.last_position.x,
            target.position.x
        )

    def test_personality_influence(self):
        """Test personality influence on behavior"""
        # Create different personalities
        personalities = {
            AIPersonality.AGGRESSIVE: Vector2(3, 4),
            AIPersonality.COWARDLY: Vector2(3, 4)
        }
        
        targets = {}
        for personality, position in personalities.items():
            # Register AI with personality
            behavior = AIBehavior(
                personality=personality,
                aggression=0.8,
                caution=0.2,
                social=0.3,
                curiosity=0.4,
                memory_duration=timedelta(minutes=5),
                vision_range=10.0,
                attack_range=2.0,
                chase_range=5.0,
                flee_threshold=0.8,
                home_position=Vector2(0, 0)
            )
            
            entity_id = len(targets) + 1
            self.ai_system.register_ai(
                entity_id,
                behavior,
                Vector2(0, 0)
            )
            
            # Create hostile target
            target = AITarget(
                id=100,
                position=position,
                type="player",
                threat_level=0.7,
                is_hostile=True
            )
            
            self.ai_system.process_perception(entity_id, [target])
            self.ai_system.update_state(entity_id)
            
            targets[personality] = self.ai_system.states[entity_id]
        
        # Verify different reactions
        self.assertNotEqual(
            targets[AIPersonality.AGGRESSIVE],
            targets[AIPersonality.COWARDLY]
        )

    def test_range_limits(self):
        """Test vision and range limits"""
        # Register AI
        self.ai_system.register_ai(
            1,
            self.test_behavior,
            Vector2(0, 0)
        )
        
        # Create target beyond vision range
        target = AITarget(
            id=2,
            position=Vector2(20, 20),  # Beyond vision_range
            type="player",
            threat_level=0.5
        )
        
        # Process perception
        self.ai_system.process_perception(1, [target])
        
        # Verify target not selected
        self.assertIsNone(self.ai_system.current_targets[1])

if __name__ == '__main__':
    unittest.main()
