from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from decimal import Decimal
from datetime import datetime
import random

@dataclass
class JobClass:
    name: str
    base_class: str
    rank: int
    required_level: int
    skills: List[str]
    stats_multiplier: Dict[str, float]

@dataclass
class Skill:
    name: str
    type: str
    mp_cost: int
    damage: int
    effects: List[Dict]
    required_level: int
    required_class: List[str]

@dataclass
class StatusEffect:
    name: str
    type: str
    duration: int
    damage_per_tick: int
    cure_item: str
    cure_skill: str

class JobSystem:
    def __init__(self):
        self.base_classes = ['Fighter', 'Mage', 'Assassin', 'Archer', 'Healer']
        self.job_classes = self._initialize_job_classes()
        
    def _initialize_job_classes(self) -> Dict[str, JobClass]:
        classes = {}
        
        # Base classes
        classes['Fighter'] = JobClass(
            name='Fighter',
            base_class='Fighter',
            rank=1,
            required_level=1,
            skills=['Basic Strike', 'Defensive Stance'],
            stats_multiplier={'strength': 1.2, 'hp': 1.2, 'defense': 1.1}
        )
        
        classes['Mage'] = JobClass(
            name='Mage',
            base_class='Mage',
            rank=1,
            required_level=1,
            skills=['Magic Bolt', 'Mana Shield'],
            stats_multiplier={'intelligence': 1.2, 'mp': 1.2, 'magic_defense': 1.1}
        )
        
        classes['Assassin'] = JobClass(
            name='Assassin',
            base_class='Assassin',
            rank=1,
            required_level=1,
            skills=['Backstab', 'Shadow Step'],
            stats_multiplier={'agility': 1.2, 'critical': 1.2, 'evasion': 1.1}
        )
        
        classes['Archer'] = JobClass(
            name='Archer',
            base_class='Archer',
            rank=1,
            required_level=1,
            skills=['Quick Shot', 'Eagle Eye'],
            stats_multiplier={'dexterity': 1.2, 'accuracy': 1.2, 'range': 1.1}
        )
        
        classes['Healer'] = JobClass(
            name='Healer',
            base_class='Healer',
            rank=1,
            required_level=1,
            skills=['Heal', 'Regenerate'],
            stats_multiplier={'wisdom': 1.2, 'mp': 1.2, 'healing': 1.1}
        )
        
        # Advanced classes (example)
        classes['Shadow Monarch'] = JobClass(
            name='Shadow Monarch',
            base_class='None',  # Special class
            rank=10,
            required_level=500,  # Level 500 required
            skills=['Arise', 'Domain Expansion', 'Shadow Army'],
            stats_multiplier={'all': 2.0}  # All stats doubled
        )
        
        return classes

    def can_change_class(self, user, target_class: str) -> Tuple[bool, str]:
        """Check if a user can change to a specific class"""
        if target_class not in self.job_classes:
            return False, "Invalid job class"
            
        job_class = self.job_classes[target_class]
        
        if user.level < job_class.required_level:
            return False, f"Required level: {job_class.required_level}"
            
        # Check if user has completed necessary quests/requirements
        # This would be expanded based on game requirements
        
        return True, "Eligible for class change"

    def change_class(self, user, new_class: str) -> Tuple[bool, str]:
        """Change a user's class"""
        can_change, message = self.can_change_class(user, new_class)
        if not can_change:
            return False, message
            
        # Update user's class and stats
        old_class = user.job_class
        user.job_class = new_class
        
        # Apply stat changes
        self._apply_class_stats(user, old_class, new_class)
        
        return True, f"Successfully changed class to {new_class}"

    def _apply_class_stats(self, user, old_class: str, new_class: str):
        """Apply stat changes when changing classes"""
        # Remove old class multipliers
        if old_class in self.job_classes:
            old_multipliers = self.job_classes[old_class].stats_multiplier
            for stat, mult in old_multipliers.items():
                if hasattr(user, stat):
                    setattr(user, stat, getattr(user, stat) / mult)
        
        # Apply new class multipliers
        new_multipliers = self.job_classes[new_class].stats_multiplier
        for stat, mult in new_multipliers.items():
            if hasattr(user, stat):
                setattr(user, stat, getattr(user, stat) * mult)

class SkillSystem:
    def __init__(self):
        self.skills = self._initialize_skills()
        self.status_effects = self._initialize_status_effects()
        
    def _initialize_skills(self) -> Dict[str, Skill]:
        skills = {}
        
        # Basic class skills
        skills['Basic Strike'] = Skill(
            name='Basic Strike',
            type='physical',
            mp_cost=0,
            damage=10,
            effects=[],
            required_level=1,
            required_class=['Fighter']
        )
        
        skills['Magic Bolt'] = Skill(
            name='Magic Bolt',
            type='magical',
            mp_cost=10,
            damage=15,
            effects=[],
            required_level=1,
            required_class=['Mage']
        )
        
        # Special skills
        skills['Arise'] = Skill(
            name='Arise',
            type='monarch',
            mp_cost=100,
            damage=0,
            effects=[{'type': 'resurrect', 'shadow': True}],
            required_level=500,
            required_class=['Shadow Monarch']
        )
        
        skills['Regenerate'] = Skill(
            name='Regenerate',
            type='healing',
            mp_cost=50,
            damage=0,
            effects=[{'type': 'heal', 'amount': 100}, {'type': 'cure', 'status': 'dismembered'}],
            required_level=1,
            required_class=['Healer']
        )
        
        return skills

    def _initialize_status_effects(self) -> Dict[str, StatusEffect]:
        effects = {}
        
        effects['burn'] = StatusEffect(
            name='Burn',
            type='fire',
            duration=5,
            damage_per_tick=10,
            cure_item='Chill Antidote',
            cure_skill='Cure'
        )
        
        effects['poisoned'] = StatusEffect(
            name='Poisoned',
            type='poison',
            duration=8,
            damage_per_tick=5,
            cure_item='Cleansing Antidote',
            cure_skill='Cure'
        )
        
        effects['frozen'] = StatusEffect(
            name='Frozen',
            type='ice',
            duration=3,
            damage_per_tick=8,
            cure_item='Flame Antidote',
            cure_skill='Cure'
        )
        
        effects['feared'] = StatusEffect(
            name='Feared',
            type='psychic',
            duration=4,
            damage_per_tick=3,
            cure_item='Shilajit Antidote',
            cure_skill=None
        )
        
        effects['confused'] = StatusEffect(
            name='Confused',
            type='psychic',
            duration=4,
            damage_per_tick=3,
            cure_item='Shilajit Antidote',
            cure_skill=None
        )
        
        effects['dismembered'] = StatusEffect(
            name='Dismembered',
            type='physical',
            duration=-1,  # Permanent until cured
            damage_per_tick=15,
            cure_item=None,
            cure_skill='Regenerate'
        )
        
        effects['decapitated'] = StatusEffect(
            name='Decapitated',
            type='physical',
            duration=-1,  # Permanent until resurrected
            damage_per_tick=999999,  # Instant death
            cure_item='Advanced Resurrection Potion',
            cure_skill='Arise'
        )
        
        effects['shadow'] = StatusEffect(
            name='Shadow',
            type='monarch',
            duration=-1,  # Permanent until cured
            damage_per_tick=0,
            cure_item='Advanced Resurrection Potion',
            cure_skill=None
        )
        
        return effects

    def can_use_skill(self, user, skill_name: str) -> Tuple[bool, str]:
        """Check if a user can use a specific skill"""
        if skill_name not in self.skills:
            return False, "Skill not found"
            
        skill = self.skills[skill_name]
        
        if user.level < skill.required_level:
            return False, f"Required level: {skill.required_level}"
            
        if user.job_class not in skill.required_class:
            return False, f"Required class: {', '.join(skill.required_class)}"
            
        if user.mp < skill.mp_cost:
            return False, f"Not enough MP (required: {skill.mp_cost})"
            
        return True, "Can use skill"

    def use_skill(self, user, skill_name: str, target=None) -> Dict:
        """Use a skill"""
        can_use, message = self.can_use_skill(user, skill_name)
        if not can_use:
            return {'status': 'error', 'message': message}
            
        skill = self.skills[skill_name]
        user.mp -= skill.mp_cost
        
        result = {
            'status': 'success',
            'skill_name': skill_name,
            'mp_cost': skill.mp_cost,
            'damage': skill.damage,
            'effects': []
        }
        
        # Apply skill effects
        for effect in skill.effects:
            if effect['type'] == 'resurrect':
                if target and hasattr(target, 'is_dead') and target.is_dead:
                    target.is_dead = False
                    if effect.get('shadow', False):
                        self.apply_status_effect(target, 'shadow')
                    result['effects'].append('resurrection')
            
            elif effect['type'] == 'heal':
                if target:
                    target.hp = min(target.hp + effect['amount'], target.max_hp)
                    result['effects'].append(f"healed {effect['amount']} HP")
            
            elif effect['type'] == 'cure':
                if target and effect['status'] in self.status_effects:
                    self.remove_status_effect(target, effect['status'])
                    result['effects'].append(f"cured {effect['status']}")
        
        return result

    def apply_status_effect(self, target, effect_name: str) -> bool:
        """Apply a status effect to a target"""
        if effect_name not in self.status_effects:
            return False
            
        effect = self.status_effects[effect_name]
        
        # Add effect to target's status effects
        if hasattr(target, 'status_effects'):
            target.status_effects[effect_name] = {
                'type': effect.type,
                'duration': effect.duration,
                'damage_per_tick': effect.damage_per_tick,
                'applied_at': datetime.utcnow()
            }
        
        return True

    def remove_status_effect(self, target, effect_name: str) -> bool:
        """Remove a status effect from a target"""
        if not hasattr(target, 'status_effects'):
            return False
            
        if effect_name in target.status_effects:
            del target.status_effects[effect_name]
            return True
            
        return False

class GateSystem:
    def __init__(self):
        self.gates = self._initialize_gates()
        
    def _initialize_gates(self) -> Dict:
        return {
            'E': {
                'min_level': 1,
                'max_level': 10,
                'crystal_reward': (10, 50),
                'monster_count': (2, 5),
                'monster_types': ['normal'],
                'boss_chance': 0.0
            },
            'D': {
                'min_level': 10,
                'max_level': 20,
                'crystal_reward': (40, 100),
                'monster_count': (3, 6),
                'monster_types': ['normal', 'elite'],
                'boss_chance': 0.1
            },
            'C': {
                'min_level': 20,
                'max_level': 35,
                'crystal_reward': (80, 200),
                'monster_count': (4, 7),
                'monster_types': ['normal', 'elite'],
                'boss_chance': 0.2
            },
            'B': {
                'min_level': 35,
                'max_level': 50,
                'crystal_reward': (150, 400),
                'monster_count': (5, 8),
                'monster_types': ['normal', 'elite', 'boss'],
                'boss_chance': 0.3
            },
            'A': {
                'min_level': 50,
                'max_level': 70,
                'crystal_reward': (300, 800),
                'monster_count': (6, 9),
                'monster_types': ['elite', 'boss'],
                'boss_chance': 0.4
            },
            'S': {
                'min_level': 70,
                'max_level': 90,
                'crystal_reward': (600, 1500),
                'monster_count': (7, 10),
                'monster_types': ['elite', 'boss', 'monarch'],
                'boss_chance': 0.5
            },
            'SS': {
                'min_level': 90,
                'max_level': 120,
                'crystal_reward': (1000, 3000),
                'monster_count': (8, 12),
                'monster_types': ['boss', 'monarch'],
                'boss_chance': 0.6
            },
            'SSS': {
                'min_level': 120,
                'max_level': 999,
                'crystal_reward': (2000, 6000),
                'monster_count': (10, 15),
                'monster_types': ['monarch'],
                'boss_chance': 1.0
            }
        }

    def can_enter_gate(self, user, gate) -> Tuple[bool, str]:
        """Check if a user can enter a specific gate"""
        gate_info = self.gates.get(gate.grade)
        if not gate_info:
            return False, "Invalid gate grade"
            
        if user.level < gate_info['min_level']:
            return False, f"Required level: {gate_info['min_level']}"
            
        # Additional checks (equipment, party size, etc.)
        return True, "Can enter gate"

    def generate_gate_monsters(self, gate, party_size: int) -> List[Dict]:
        """Generate monsters for a gate instance"""
        gate_info = self.gates[gate.grade]
        
        # Adjust monster count based on party size
        base_count = random.randint(*gate_info['monster_count'])
        adjusted_count = base_count + (party_size - 1)
        
        monsters = []
        for _ in range(adjusted_count):
            monster_type = random.choice(gate_info['monster_types'])
            if monster_type == 'monarch' or (monster_type == 'boss' and random.random() < gate_info['boss_chance']):
                # Generate boss/monarch monster
                monsters.append({
                    'type': monster_type,
                    'level': random.randint(gate_info['min_level'], gate_info['max_level']),
                    'hp_multiplier': 5.0 if monster_type == 'monarch' else 3.0,
                    'damage_multiplier': 3.0 if monster_type == 'monarch' else 2.0
                })
            else:
                # Generate normal/elite monster
                monsters.append({
                    'type': monster_type,
                    'level': random.randint(gate_info['min_level'], gate_info['max_level']),
                    'hp_multiplier': 1.5 if monster_type == 'elite' else 1.0,
                    'damage_multiplier': 1.5 if monster_type == 'elite' else 1.0
                })
        
        return monsters

    def calculate_rewards(self, gate, party_size: int, total_luck: int) -> Dict:
        """Calculate rewards for completing a gate"""
        gate_info = self.gates[gate.grade]
        
        # Base crystal reward
        base_reward = random.randint(*gate_info['crystal_reward'])
        
        # Adjust for party size (diminishing returns)
        party_modifier = 1 / (1 + (party_size - 1) * 0.2)  # Each additional member reduces rewards by 20%
        
        # Luck bonus (each point of luck adds 0.1% to rewards)
        luck_modifier = 1 + (total_luck * 0.001)
        
        final_reward = int(base_reward * party_modifier * luck_modifier)
        
        return {
            'crystals': final_reward,
            'base_reward': base_reward,
            'party_modifier': party_modifier,
            'luck_modifier': luck_modifier
        }

class DurabilitySystem:
    def __init__(self):
        self.durability_loss_rates = {
            'damage_taken': 0.01,  # 0.01% per point of damage
            'mana_used': 0.005,    # 0.005% per point of mana
            'time_spent': 0.1      # 0.1% per minute
        }

    def calculate_durability_loss(self, damage_taken: int, mana_used: int, time_spent_minutes: int) -> float:
        """Calculate durability loss based on various factors"""
        damage_loss = damage_taken * self.durability_loss_rates['damage_taken']
        mana_loss = mana_used * self.durability_loss_rates['mana_used']
        time_loss = time_spent_minutes * self.durability_loss_rates['time_spent']
        
        return damage_loss + mana_loss + time_loss

    def apply_durability_loss(self, equipment: Dict, damage_taken: int, mana_used: int, time_spent_minutes: int) -> Dict:
        """Apply durability loss to equipment"""
        loss = self.calculate_durability_loss(damage_taken, mana_used, time_spent_minutes)
        
        equipment['durability'] = max(0, equipment['durability'] - loss)
        
        if equipment['durability'] == 0:
            equipment['broken'] = True
        
        return equipment

    def repair_equipment(self, equipment: Dict, amount: float = 100.0) -> Dict:
        """Repair equipment durability"""
        if equipment.get('broken', False) and amount < 100:
            return equipment  # Can't partially repair broken equipment
            
        equipment['durability'] = min(100, equipment['durability'] + amount)
        if equipment['durability'] == 100:
            equipment['broken'] = False
            
        return equipment

    def can_use_equipment(self, equipment: Dict) -> Tuple[bool, str]:
        """Check if equipment can be used"""
        if equipment.get('broken', False):
            return False, "Equipment is broken"
            
        if equipment.get('durability', 0) <= 0:
            return False, "Equipment has no durability"
            
        return True, "Equipment can be used"
