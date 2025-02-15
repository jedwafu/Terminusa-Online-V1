import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import random
import math

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class DamageType(Enum):
    """Types of damage"""
    PHYSICAL = auto()
    MAGICAL = auto()
    TRUE = auto()
    FIRE = auto()
    ICE = auto()
    LIGHTNING = auto()
    POISON = auto()

class StatusEffect(Enum):
    """Combat status effects"""
    STUN = auto()
    BURN = auto()
    FREEZE = auto()
    SHOCK = auto()
    POISON = auto()
    BLEED = auto()
    WEAKEN = auto()
    STRENGTHEN = auto()
    HASTE = auto()
    SLOW = auto()

@dataclass
class Stats:
    """Combat stats"""
    health: float
    mana: float
    attack: float
    defense: float
    magic_attack: float
    magic_defense: float
    speed: float
    critical_rate: float
    critical_damage: float
    dodge_rate: float
    accuracy: float
    resistances: Dict[DamageType, float]

@dataclass
class StatusEffectInstance:
    """Status effect instance"""
    type: StatusEffect
    duration: int
    strength: float
    source_id: int

@dataclass
class CombatEntity:
    """Combat entity data"""
    id: int
    name: str
    level: int
    base_stats: Stats
    current_stats: Stats
    status_effects: List[StatusEffectInstance]
    is_alive: bool = True

@dataclass
class CombatAction:
    """Combat action data"""
    source_id: int
    target_id: int
    damage_type: DamageType
    base_damage: float
    status_effects: List[StatusEffectInstance] = None
    accuracy_modifier: float = 1.0
    critical_modifier: float = 1.0

@dataclass
class CombatResult:
    """Combat result data"""
    damage_dealt: float
    damage_type: DamageType
    is_critical: bool
    is_dodged: bool
    status_effects: List[StatusEffectInstance]

class CombatSystem:
    """System for combat management"""
    def __init__(self):
        self.entities: Dict[int, CombatEntity] = {}
        self.next_entity_id = 1

    def register_entity(
        self,
        name: str,
        level: int,
        stats: Stats
    ) -> int:
        """Register a combat entity"""
        entity_id = self.next_entity_id
        self.next_entity_id += 1
        
        entity = CombatEntity(
            id=entity_id,
            name=name,
            level=level,
            base_stats=stats,
            current_stats=Stats(**stats.__dict__),
            status_effects=[]
        )
        
        self.entities[entity_id] = entity
        return entity_id

    def process_action(
        self,
        action: CombatAction
    ) -> Optional[CombatResult]:
        """Process a combat action"""
        source = self.entities.get(action.source_id)
        target = self.entities.get(action.target_id)
        if not source or not target:
            return None
        
        if not source.is_alive or not target.is_alive:
            return None
        
        # Calculate hit chance
        hit_chance = (
            source.current_stats.accuracy *
            action.accuracy_modifier /
            target.current_stats.dodge_rate
        )
        
        if random.random() > hit_chance:
            return CombatResult(
                damage_dealt=0,
                damage_type=action.damage_type,
                is_critical=False,
                is_dodged=True,
                status_effects=[]
            )
        
        # Calculate critical hit
        is_critical = random.random() < source.current_stats.critical_rate
        critical_multiplier = (
            source.current_stats.critical_damage if is_critical
            else 1.0
        )
        
        # Calculate damage
        if action.damage_type in (DamageType.PHYSICAL, DamageType.BLEED):
            defense = target.current_stats.defense
            attack = source.current_stats.attack
        elif action.damage_type == DamageType.TRUE:
            defense = 0
            attack = source.current_stats.attack
        else:
            defense = target.current_stats.magic_defense
            attack = source.current_stats.magic_attack
        
        damage = (
            action.base_damage *
            (attack / (attack + defense)) *
            critical_multiplier *
            action.critical_modifier *
            (1.0 - target.current_stats.resistances.get(action.damage_type, 0))
        )
        
        # Apply damage
        target.current_stats.health = max(
            0,
            target.current_stats.health - damage
        )
        
        if target.current_stats.health <= 0:
            target.is_alive = False
        
        # Apply status effects
        applied_effects = []
        if action.status_effects:
            for effect in action.status_effects:
                if random.random() < 0.5:  # 50% base chance
                    target.status_effects.append(effect)
                    applied_effects.append(effect)
        
        return CombatResult(
            damage_dealt=damage,
            damage_type=action.damage_type,
            is_critical=is_critical,
            is_dodged=False,
            status_effects=applied_effects
        )

    def process_status_effects(self, entity_id: int):
        """Process entity status effects"""
        entity = self.entities.get(entity_id)
        if not entity or not entity.is_alive:
            return
        
        # Process each effect
        remaining_effects = []
        for effect in entity.status_effects:
            # Apply effect
            if effect.type == StatusEffect.BURN:
                damage = entity.base_stats.health * 0.05 * effect.strength
                entity.current_stats.health = max(
                    0,
                    entity.current_stats.health - damage
                )
            elif effect.type == StatusEffect.POISON:
                damage = entity.base_stats.health * 0.03 * effect.strength
                entity.current_stats.health = max(
                    0,
                    entity.current_stats.health - damage
                )
            elif effect.type == StatusEffect.WEAKEN:
                entity.current_stats.attack = (
                    entity.base_stats.attack *
                    (1.0 - 0.2 * effect.strength)
                )
            elif effect.type == StatusEffect.STRENGTHEN:
                entity.current_stats.attack = (
                    entity.base_stats.attack *
                    (1.0 + 0.2 * effect.strength)
                )
            
            # Update duration
            effect.duration -= 1
            if effect.duration > 0:
                remaining_effects.append(effect)
        
        entity.status_effects = remaining_effects
        
        if entity.current_stats.health <= 0:
            entity.is_alive = False

    def heal_entity(
        self,
        entity_id: int,
        amount: float
    ) -> float:
        """Heal an entity"""
        entity = self.entities.get(entity_id)
        if not entity or not entity.is_alive:
            return 0
        
        old_health = entity.current_stats.health
        entity.current_stats.health = min(
            entity.base_stats.health,
            entity.current_stats.health + amount
        )
        
        return entity.current_stats.health - old_health

    def remove_status_effect(
        self,
        entity_id: int,
        effect_type: StatusEffect
    ) -> bool:
        """Remove a status effect"""
        entity = self.entities.get(entity_id)
        if not entity:
            return False
        
        original_length = len(entity.status_effects)
        entity.status_effects = [
            e for e in entity.status_effects
            if e.type != effect_type
        ]
        
        return len(entity.status_effects) < original_length

class TestCombat(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.combat = CombatSystem()
        
        # Create test stats
        self.test_stats = Stats(
            health=1000,
            mana=100,
            attack=100,
            defense=50,
            magic_attack=80,
            magic_defense=40,
            speed=10,
            critical_rate=0.1,
            critical_damage=2.0,
            dodge_rate=0.1,
            accuracy=1.0,
            resistances={
                DamageType.FIRE: 0.2,
                DamageType.ICE: 0.2,
                DamageType.LIGHTNING: 0.2,
                DamageType.POISON: 0.2
            }
        )

    def test_entity_registration(self):
        """Test entity registration"""
        # Register entity
        entity_id = self.combat.register_entity(
            "Test Entity",
            1,
            self.test_stats
        )
        
        # Verify registration
        self.assertIsNotNone(entity_id)
        entity = self.combat.entities[entity_id]
        self.assertEqual(entity.name, "Test Entity")
        self.assertEqual(entity.level, 1)
        self.assertEqual(entity.current_stats.health, 1000)

    def test_basic_combat(self):
        """Test basic combat action"""
        # Create entities
        attacker_id = self.combat.register_entity(
            "Attacker",
            1,
            self.test_stats
        )
        defender_id = self.combat.register_entity(
            "Defender",
            1,
            self.test_stats
        )
        
        # Create action
        action = CombatAction(
            source_id=attacker_id,
            target_id=defender_id,
            damage_type=DamageType.PHYSICAL,
            base_damage=100
        )
        
        # Process action
        result = self.combat.process_action(action)
        
        # Verify damage
        self.assertIsNotNone(result)
        self.assertGreater(result.damage_dealt, 0)
        defender = self.combat.entities[defender_id]
        self.assertLess(defender.current_stats.health, 1000)

    def test_status_effects(self):
        """Test status effects"""
        # Create entity
        entity_id = self.combat.register_entity(
            "Test Entity",
            1,
            self.test_stats
        )
        
        # Apply burn effect
        entity = self.combat.entities[entity_id]
        entity.status_effects.append(
            StatusEffectInstance(
                type=StatusEffect.BURN,
                duration=3,
                strength=1.0,
                source_id=0
            )
        )
        
        # Process effects
        initial_health = entity.current_stats.health
        self.combat.process_status_effects(entity_id)
        
        # Verify damage
        self.assertLess(
            entity.current_stats.health,
            initial_health
        )

    def test_healing(self):
        """Test healing"""
        # Create damaged entity
        entity_id = self.combat.register_entity(
            "Test Entity",
            1,
            self.test_stats
        )
        entity = self.combat.entities[entity_id]
        entity.current_stats.health = 500
        
        # Heal entity
        healed = self.combat.heal_entity(entity_id, 300)
        
        # Verify healing
        self.assertEqual(healed, 300)
        self.assertEqual(entity.current_stats.health, 800)

    def test_critical_hits(self):
        """Test critical hits"""
        # Create entities with 100% crit rate
        attacker_stats = Stats(**self.test_stats.__dict__)
        attacker_stats.critical_rate = 1.0
        
        attacker_id = self.combat.register_entity(
            "Attacker",
            1,
            attacker_stats
        )
        defender_id = self.combat.register_entity(
            "Defender",
            1,
            self.test_stats
        )
        
        # Create action
        action = CombatAction(
            source_id=attacker_id,
            target_id=defender_id,
            damage_type=DamageType.PHYSICAL,
            base_damage=100
        )
        
        # Process action
        result = self.combat.process_action(action)
        
        # Verify critical hit
        self.assertTrue(result.is_critical)
        self.assertGreater(
            result.damage_dealt,
            100  # Base damage
        )

    def test_damage_types(self):
        """Test different damage types"""
        # Create entities
        attacker_id = self.combat.register_entity(
            "Attacker",
            1,
            self.test_stats
        )
        defender_id = self.combat.register_entity(
            "Defender",
            1,
            self.test_stats
        )
        
        damage_types = [
            DamageType.PHYSICAL,
            DamageType.MAGICAL,
            DamageType.TRUE
        ]
        
        damages = []
        for dtype in damage_types:
            action = CombatAction(
                source_id=attacker_id,
                target_id=defender_id,
                damage_type=dtype,
                base_damage=100
            )
            
            result = self.combat.process_action(action)
            damages.append(result.damage_dealt)
            
            # Reset defender health
            defender = self.combat.entities[defender_id]
            defender.current_stats.health = defender.base_stats.health
        
        # Verify different damage calculations
        self.assertNotEqual(len(set(damages)), 1)

    def test_dodge_mechanics(self):
        """Test dodge mechanics"""
        # Create entities with 100% dodge rate
        defender_stats = Stats(**self.test_stats.__dict__)
        defender_stats.dodge_rate = float('inf')
        
        attacker_id = self.combat.register_entity(
            "Attacker",
            1,
            self.test_stats
        )
        defender_id = self.combat.register_entity(
            "Defender",
            1,
            defender_stats
        )
        
        # Create action
        action = CombatAction(
            source_id=attacker_id,
            target_id=defender_id,
            damage_type=DamageType.PHYSICAL,
            base_damage=100
        )
        
        # Process action
        result = self.combat.process_action(action)
        
        # Verify dodge
        self.assertTrue(result.is_dodged)
        self.assertEqual(result.damage_dealt, 0)

if __name__ == '__main__':
    unittest.main()
