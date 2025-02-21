"""
Mount and Pet models for Terminusa Online
"""
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class MountType(Enum):
    GROUND = "ground"
    FLYING = "flying"
    AQUATIC = "aquatic"
    HYBRID = "hybrid"

class PetType(Enum):
    COMBAT = "combat"
    UTILITY = "utility"
    GATHERING = "gathering"
    SUPPORT = "support"

class Mount(db.Model):
    __tablename__ = 'mounts'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    
    # Mount Info
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.Enum(MountType), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    
    # Mount Stats
    stats = db.Column(JSONB, nullable=False, default={
        'speed': 100,
        'stamina': 100,
        'carrying_capacity': 100,
        'durability': 100
    })
    
    # Mount Abilities
    abilities = db.Column(JSONB, nullable=False, default=[])
    active_ability = db.Column(db.String(50), nullable=True)
    
    # Mount Status
    is_active = db.Column(db.Boolean, default=False)
    is_resting = db.Column(db.Boolean, default=False)
    stamina_current = db.Column(db.Integer, default=100)
    durability_current = db.Column(db.Integer, default=100)
    
    # Mount Customization
    appearance = db.Column(JSONB, nullable=False, default={})
    equipment = db.Column(JSONB, nullable=False, default={})
    
    # Trading Info
    is_tradeable = db.Column(db.Boolean, default=True)
    trade_restriction = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = db.Column(db.DateTime, nullable=True)

    def __init__(self, owner_id: int, name: str, type: MountType, rarity: str):
        self.owner_id = owner_id
        self.name = name
        self.type = type
        self.rarity = rarity
        self._initialize_stats()

    def _initialize_stats(self):
        """Initialize mount stats based on type and rarity"""
        # Base stats multiplier based on rarity
        rarity_multipliers = {
            'Basic': 1.0,
            'Intermediate': 1.2,
            'Excellent': 1.5,
            'Legendary': 2.0,
            'Immortal': 3.0
        }
        
        # Base stats based on type
        type_stats = {
            MountType.GROUND: {
                'speed': 100,
                'stamina': 120,
                'carrying_capacity': 150,
                'durability': 130
            },
            MountType.FLYING: {
                'speed': 150,
                'stamina': 100,
                'carrying_capacity': 80,
                'durability': 90
            },
            MountType.AQUATIC: {
                'speed': 120,
                'stamina': 130,
                'carrying_capacity': 100,
                'durability': 110
            },
            MountType.HYBRID: {
                'speed': 110,
                'stamina': 110,
                'carrying_capacity': 110,
                'durability': 110
            }
        }
        
        multiplier = rarity_multipliers.get(self.rarity, 1.0)
        base_stats = type_stats.get(self.type, type_stats[MountType.GROUND])
        
        self.stats = {
            stat: int(value * multiplier)
            for stat, value in base_stats.items()
        }

    def gain_experience(self, amount: int) -> Dict:
        """Grant experience points to mount"""
        self.experience += amount
        
        level_ups = 0
        while self._check_level_up():
            self._level_up()
            level_ups += 1
            
        return {
            'gained_exp': amount,
            'level_ups': level_ups,
            'current_level': self.level,
            'current_exp': self.experience
        }

    def _check_level_up(self) -> bool:
        """Check if mount has enough exp to level up"""
        required_exp = self._get_required_exp()
        return self.experience >= required_exp

    def _get_required_exp(self) -> int:
        """Calculate required exp for next level"""
        return int(1000 * (1.2 ** (self.level - 1)))

    def _level_up(self):
        """Process mount level up and stat increases"""
        self.level += 1
        
        # Increase stats based on mount type
        stat_increases = {
            MountType.GROUND: {
                'stamina': 10,
                'carrying_capacity': 15,
                'durability': 12
            },
            MountType.FLYING: {
                'speed': 15,
                'stamina': 8
            },
            MountType.AQUATIC: {
                'speed': 10,
                'stamina': 12,
                'durability': 8
            },
            MountType.HYBRID: {
                'speed': 8,
                'stamina': 8,
                'carrying_capacity': 8,
                'durability': 8
            }
        }
        
        for stat, increase in stat_increases.get(self.type, {}).items():
            self.stats[stat] += increase

    def rest(self) -> Dict:
        """Rest mount to recover stamina and durability"""
        if not self.is_resting:
            self.is_resting = True
            self.is_active = False
            return {
                'success': True,
                'message': 'Mount is now resting'
            }
        return {
            'success': False,
            'message': 'Mount is already resting'
        }

    def recover(self, amount: int) -> Dict:
        """Recover mount's stamina and durability"""
        old_stamina = self.stamina_current
        old_durability = self.durability_current
        
        self.stamina_current = min(self.stats['stamina'], 
                                 self.stamina_current + amount)
        self.durability_current = min(self.stats['durability'], 
                                    self.durability_current + amount)
        
        return {
            'stamina_recovered': self.stamina_current - old_stamina,
            'durability_recovered': self.durability_current - old_durability
        }

    def to_dict(self) -> Dict:
        """Convert mount data to dictionary"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'type': self.type.value,
            'rarity': self.rarity,
            'level': self.level,
            'experience': self.experience,
            'stats': self.stats,
            'abilities': self.abilities,
            'active_ability': self.active_ability,
            'status': {
                'is_active': self.is_active,
                'is_resting': self.is_resting,
                'stamina': self.stamina_current,
                'durability': self.durability_current
            },
            'customization': {
                'appearance': self.appearance,
                'equipment': self.equipment
            },
            'trading': {
                'is_tradeable': self.is_tradeable,
                'restriction': self.trade_restriction
            }
        }

class Pet(db.Model):
    __tablename__ = 'pets'

    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    
    # Pet Info
    name = db.Column(db.String(50), nullable=False)
    type = db.Column(db.Enum(PetType), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    
    # Pet Stats
    stats = db.Column(JSONB, nullable=False, default={
        'attack': 10,
        'defense': 10,
        'speed': 10,
        'intelligence': 10
    })
    
    # Pet Abilities
    abilities = db.Column(JSONB, nullable=False, default=[])
    active_ability = db.Column(db.String(50), nullable=True)
    
    # Pet Status
    is_active = db.Column(db.Boolean, default=False)
    is_resting = db.Column(db.Boolean, default=False)
    energy_current = db.Column(db.Integer, default=100)
    happiness = db.Column(db.Integer, default=100)
    
    # Pet Customization
    appearance = db.Column(JSONB, nullable=False, default={})
    equipment = db.Column(JSONB, nullable=False, default={})
    
    # Trading Info
    is_tradeable = db.Column(db.Boolean, default=True)
    trade_restriction = db.Column(db.String(50), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = db.Column(db.DateTime, nullable=True)

    def __init__(self, owner_id: int, name: str, type: PetType, rarity: str):
        self.owner_id = owner_id
        self.name = name
        self.type = type
        self.rarity = rarity
        self._initialize_stats()

    def _initialize_stats(self):
        """Initialize pet stats based on type and rarity"""
        # Base stats multiplier based on rarity
        rarity_multipliers = {
            'Basic': 1.0,
            'Intermediate': 1.2,
            'Excellent': 1.5,
            'Legendary': 2.0,
            'Immortal': 3.0
        }
        
        # Base stats based on type
        type_stats = {
            PetType.COMBAT: {
                'attack': 15,
                'defense': 12,
                'speed': 10,
                'intelligence': 8
            },
            PetType.UTILITY: {
                'attack': 8,
                'defense': 10,
                'speed': 12,
                'intelligence': 15
            },
            PetType.GATHERING: {
                'attack': 5,
                'defense': 8,
                'speed': 15,
                'intelligence': 12
            },
            PetType.SUPPORT: {
                'attack': 6,
                'defense': 15,
                'speed': 8,
                'intelligence': 12
            }
        }
        
        multiplier = rarity_multipliers.get(self.rarity, 1.0)
        base_stats = type_stats.get(self.type, type_stats[PetType.UTILITY])
        
        self.stats = {
            stat: int(value * multiplier)
            for stat, value in base_stats.items()
        }

    def gain_experience(self, amount: int) -> Dict:
        """Grant experience points to pet"""
        self.experience += amount
        
        level_ups = 0
        while self._check_level_up():
            self._level_up()
            level_ups += 1
            
        return {
            'gained_exp': amount,
            'level_ups': level_ups,
            'current_level': self.level,
            'current_exp': self.experience
        }

    def _check_level_up(self) -> bool:
        """Check if pet has enough exp to level up"""
        required_exp = self._get_required_exp()
        return self.experience >= required_exp

    def _get_required_exp(self) -> int:
        """Calculate required exp for next level"""
        return int(800 * (1.2 ** (self.level - 1)))

    def _level_up(self):
        """Process pet level up and stat increases"""
        self.level += 1
        
        # Increase stats based on pet type
        stat_increases = {
            PetType.COMBAT: {
                'attack': 3,
                'defense': 2
            },
            PetType.UTILITY: {
                'intelligence': 3,
                'speed': 2
            },
            PetType.GATHERING: {
                'speed': 3,
                'intelligence': 2
            },
            PetType.SUPPORT: {
                'defense': 3,
                'intelligence': 2
            }
        }
        
        for stat, increase in stat_increases.get(self.type, {}).items():
            self.stats[stat] += increase

    def rest(self) -> Dict:
        """Rest pet to recover energy"""
        if not self.is_resting:
            self.is_resting = True
            self.is_active = False
            return {
                'success': True,
                'message': 'Pet is now resting'
            }
        return {
            'success': False,
            'message': 'Pet is already resting'
        }

    def feed(self, food_quality: int) -> Dict:
        """Feed pet to increase happiness"""
        old_happiness = self.happiness
        increase = min(food_quality, 100 - self.happiness)
        self.happiness += increase
        
        return {
            'happiness_increased': increase,
            'current_happiness': self.happiness,
            'previous_happiness': old_happiness
        }

    def to_dict(self) -> Dict:
        """Convert pet data to dictionary"""
        return {
            'id': self.id,
            'owner_id': self.owner_id,
            'name': self.name,
            'type': self.type.value,
            'rarity': self.rarity,
            'level': self.level,
            'experience': self.experience,
            'stats': self.stats,
            'abilities': self.abilities,
            'active_ability': self.active_ability,
            'status': {
                'is_active': self.is_active,
                'is_resting': self.is_resting,
                'energy': self.energy_current,
                'happiness': self.happiness
            },
            'customization': {
                'appearance': self.appearance,
                'equipment': self.equipment
            },
            'trading': {
                'is_tradeable': self.is_tradeable,
                'restriction': self.trade_restriction
            }
        }
