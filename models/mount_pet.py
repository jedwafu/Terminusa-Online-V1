from datetime import datetime
from typing import Dict, List
from database import db
from sqlalchemy.dialects.postgresql import JSONB

class Mount(db.Model):
    """Model for player mounts"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)  # Basic, Intermediate, Excellent, Legendary, Immortal
    level_requirement = db.Column(db.Integer, nullable=False)
    stats = db.Column(JSONB, nullable=False)  # {speed, stamina, carrying_capacity}
    is_equipped = db.Column(db.Boolean, default=False)
    is_tradeable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('mounts', lazy=True))

    def __init__(self, **kwargs):
        super(Mount, self).__init__(**kwargs)
        if not self.stats:
            self.stats = {
                'speed': 10,
                'stamina': 100,
                'carrying_capacity': 50
            }

    @property
    def total_stats(self) -> int:
        """Calculate total stats value"""
        return sum(self.stats.values())

    def to_dict(self) -> Dict:
        """Convert mount to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'rarity': self.rarity,
            'level_requirement': self.level_requirement,
            'stats': self.stats,
            'is_equipped': self.is_equipped,
            'is_tradeable': self.is_tradeable,
            'created_at': self.created_at.isoformat()
        }

class Pet(db.Model):
    """Model for player pets"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.String(20), nullable=False)  # Basic, Intermediate, Excellent, Legendary, Immortal
    level_requirement = db.Column(db.Integer, nullable=False)
    abilities = db.Column(JSONB, nullable=False)  # List of ability names
    is_active = db.Column(db.Boolean, default=False)
    is_tradeable = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Special ability cooldowns
    last_ability_use = db.Column(JSONB, default={})  # {ability_name: timestamp}
    ability_cooldowns = db.Column(JSONB, default={})  # {ability_name: cooldown_seconds}

    # Relationships
    user = db.relationship('User', backref=db.backref('pets', lazy=True))

    def __init__(self, **kwargs):
        super(Pet, self).__init__(**kwargs)
        if not self.abilities:
            self.abilities = ['Item Finder']
        if not self.last_ability_use:
            self.last_ability_use = {}
        if not self.ability_cooldowns:
            self.ability_cooldowns = {
                'Item Finder': 3600,          # 1 hour
                'Combat Support': 1800,        # 30 minutes
                'Stat Boost': 7200,           # 2 hours
                'Special Skill': 14400,       # 4 hours
                'Unique Ability': 28800       # 8 hours
            }

    def can_use_ability(self, ability_name: str) -> bool:
        """Check if an ability is ready to use"""
        if ability_name not in self.abilities:
            return False

        last_use = self.last_ability_use.get(ability_name)
        if not last_use:
            return True

        cooldown = self.ability_cooldowns.get(ability_name, 3600)
        time_since_use = (datetime.utcnow() - datetime.fromisoformat(last_use)).total_seconds()
        return time_since_use >= cooldown

    def use_ability(self, ability_name: str) -> bool:
        """Use a pet ability"""
        if not self.can_use_ability(ability_name):
            return False

        self.last_ability_use[ability_name] = datetime.utcnow().isoformat()
        db.session.commit()
        return True

    def get_ability_effects(self, ability_name: str) -> Dict:
        """Get the effects of an ability"""
        effects = {
            'Item Finder': {
                'type': 'loot_bonus',
                'value': {
                    'Basic': 1.1,        # 10% increased loot chance
                    'Intermediate': 1.2,  # 20% increased loot chance
                    'Excellent': 1.3,    # 30% increased loot chance
                    'Legendary': 1.4,    # 40% increased loot chance
                    'Immortal': 1.5      # 50% increased loot chance
                }.get(self.rarity, 1.1)
            },
            'Combat Support': {
                'type': 'damage_bonus',
                'value': {
                    'Basic': 1.05,       # 5% increased damage
                    'Intermediate': 1.1,  # 10% increased damage
                    'Excellent': 1.15,   # 15% increased damage
                    'Legendary': 1.2,    # 20% increased damage
                    'Immortal': 1.25     # 25% increased damage
                }.get(self.rarity, 1.05)
            },
            'Stat Boost': {
                'type': 'stat_bonus',
                'value': {
                    'Basic': 1.1,        # 10% increased stats
                    'Intermediate': 1.15, # 15% increased stats
                    'Excellent': 1.2,    # 20% increased stats
                    'Legendary': 1.25,   # 25% increased stats
                    'Immortal': 1.3      # 30% increased stats
                }.get(self.rarity, 1.1)
            },
            'Special Skill': {
                'type': 'special_effect',
                'value': {
                    'Basic': 'Minor Heal',
                    'Intermediate': 'Medium Heal',
                    'Excellent': 'Major Heal',
                    'Legendary': 'Full Heal',
                    'Immortal': 'Group Heal'
                }.get(self.rarity, 'Minor Heal')
            },
            'Unique Ability': {
                'type': 'unique_effect',
                'value': None  # Set dynamically when pet is generated
            }
        }
        return effects.get(ability_name, {'type': 'none', 'value': 0})

    def to_dict(self) -> Dict:
        """Convert pet to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'rarity': self.rarity,
            'level_requirement': self.level_requirement,
            'abilities': self.abilities,
            'is_active': self.is_active,
            'is_tradeable': self.is_tradeable,
            'created_at': self.created_at.isoformat(),
            'cooldowns': {
                ability: {
                    'ready': self.can_use_ability(ability),
                    'cooldown': self.ability_cooldowns.get(ability),
                    'last_use': self.last_ability_use.get(ability)
                }
                for ability in self.abilities
            }
        }
