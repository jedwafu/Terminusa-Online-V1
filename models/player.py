"""
Player model for Terminusa Online
"""
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class PlayerClass(Enum):
    WARRIOR = "warrior"
    MAGE = "mage"
    ROGUE = "rogue"
    PRIEST = "priest"
    RANGER = "ranger"

class JobType(Enum):
    BLACKSMITH = "blacksmith"
    ALCHEMIST = "alchemist"
    ENCHANTER = "enchanter"
    MERCHANT = "merchant"
    HUNTER = "hunter"

class PlayerCharacter(db.Model):
    """Player character model"""
    __tablename__ = 'player_characters'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    class_id = db.Column(db.Integer, db.ForeignKey('player_classes.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job_types.id'))
    
    # Relationships
    user = db.relationship('User', back_populates='characters')
    player_class = db.relationship('PlayerClass')
    job = db.relationship('JobType')

class Player(db.Model):
    __tablename__ = 'players'


    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Basic Info
    name = db.Column(db.String(50), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    player_class = db.Column(db.Enum(PlayerClass), nullable=False)
    job_type = db.Column(db.Enum(JobType), nullable=True)
    
    # Stats
    stats = db.Column(JSONB, nullable=False, default={
        'strength': 10,
        'intelligence': 10,
        'dexterity': 10,
        'vitality': 10,
        'wisdom': 10,
        'luck': 10
    })
    
    # Combat Stats
    combat_stats = db.Column(JSONB, nullable=False, default={
        'hp': 100,
        'mp': 100,
        'attack': 10,
        'defense': 10,
        'magic_attack': 10,
        'magic_defense': 10,
        'accuracy': 10,
        'evasion': 10,
        'critical_rate': 5,
        'critical_damage': 150
    })
    
    # Progress
    class_levels = db.Column(JSONB, nullable=False, default={
        'warrior': 1,
        'mage': 1,
        'rogue': 1,
        'priest': 1,
        'ranger': 1
    })
    
    job_levels = db.Column(JSONB, nullable=False, default={
        'blacksmith': 1,
        'alchemist': 1,
        'enchanter': 1,
        'merchant': 1,
        'hunter': 1
    })
    
    # Achievement Progress
    achievements = db.Column(JSONB, nullable=False, default={})
    titles = db.Column(JSONB, nullable=False, default=[])
    
    # Activity Stats
    gates_cleared = db.Column(db.Integer, default=0)
    quests_completed = db.Column(db.Integer, default=0)
    monsters_killed = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    pvp_wins = db.Column(db.Integer, default=0)
    pvp_losses = db.Column(db.Integer, default=0)
    
    # Status
    is_alive = db.Column(db.Boolean, default=True)
    last_death = db.Column(db.DateTime, nullable=True)
    resurrection_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __init__(self, user_id: int, name: str, player_class: PlayerClass):
        self.user_id = user_id
        self.name = name
        self.player_class = player_class
        self._initialize_class_bonuses()

    def _initialize_class_bonuses(self):
        """Initialize stats based on chosen class"""
        class_bonuses = {
            PlayerClass.WARRIOR: {
                'stats': {'strength': 5, 'vitality': 3},
                'combat_stats': {'hp': 50, 'attack': 5, 'defense': 5}
            },
            PlayerClass.MAGE: {
                'stats': {'intelligence': 5, 'wisdom': 3},
                'combat_stats': {'mp': 50, 'magic_attack': 5, 'magic_defense': 5}
            },
            PlayerClass.ROGUE: {
                'stats': {'dexterity': 5, 'luck': 3},
                'combat_stats': {'accuracy': 5, 'evasion': 5, 'critical_rate': 2}
            },
            PlayerClass.PRIEST: {
                'stats': {'wisdom': 5, 'vitality': 3},
                'combat_stats': {'mp': 30, 'magic_defense': 5, 'hp': 20}
            },
            PlayerClass.RANGER: {
                'stats': {'dexterity': 5, 'strength': 3},
                'combat_stats': {'accuracy': 5, 'attack': 3, 'critical_rate': 2}
            }
        }
        
        bonuses = class_bonuses[self.player_class]
        
        # Apply stat bonuses
        for stat, bonus in bonuses['stats'].items():
            self.stats[stat] += bonus
            
        # Apply combat stat bonuses
        for stat, bonus in bonuses['combat_stats'].items():
            self.combat_stats[stat] += bonus

    def gain_experience(self, amount: int) -> Dict:
        """Grant experience points and handle level ups"""
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
        """Check if player has enough exp to level up"""
        required_exp = self._get_required_exp()
        return self.experience >= required_exp

    def _get_required_exp(self) -> int:
        """Calculate required exp for next level"""
        return int(100 * (1.5 ** (self.level - 1)))

    def _level_up(self):
        """Process level up and stat increases"""
        self.level += 1
        
        # Base stat increases
        for stat in self.stats:
            self.stats[stat] += 2
            
        # Class-based bonus stats
        class_stat_focus = {
            PlayerClass.WARRIOR: ['strength', 'vitality'],
            PlayerClass.MAGE: ['intelligence', 'wisdom'],
            PlayerClass.ROGUE: ['dexterity', 'luck'],
            PlayerClass.PRIEST: ['wisdom', 'vitality'],
            PlayerClass.RANGER: ['dexterity', 'strength']
        }
        
        for stat in class_stat_focus[self.player_class]:
            self.stats[stat] += 1
            
        # Update combat stats
        self._update_combat_stats()

    def _update_combat_stats(self):
        """Update combat stats based on current stats"""
        stat_scaling = {
            'hp': ('vitality', 10),
            'mp': ('wisdom', 10),
            'attack': ('strength', 2),
            'defense': ('vitality', 2),
            'magic_attack': ('intelligence', 2),
            'magic_defense': ('wisdom', 2),
            'accuracy': ('dexterity', 1),
            'evasion': ('dexterity', 1),
            'critical_rate': ('luck', 0.2),
            'critical_damage': ('luck', 1)
        }
        
        for combat_stat, (base_stat, scaling) in stat_scaling.items():
            self.combat_stats[combat_stat] = int(
                self.combat_stats[combat_stat] + 
                (self.stats[base_stat] * scaling)
            )

    def die(self):
        """Handle player death"""
        if self.is_alive:
            self.is_alive = False
            self.last_death = datetime.utcnow()
            self.deaths += 1
            
            # Experience penalty (lose 5% of current level progress)
            level_start_exp = self._get_required_exp() * (self.level - 1)
            current_level_exp = self.experience - level_start_exp
            penalty = int(current_level_exp * 0.05)
            self.experience = max(level_start_exp, self.experience - penalty)
            
            return {
                'death_count': self.deaths,
                'exp_lost': penalty,
                'resurrection_available': self.can_resurrect()
            }

    def resurrect(self, use_potion: bool = False):
        """Handle player resurrection"""
        if not self.is_alive and (use_potion or self.can_resurrect()):
            self.is_alive = True
            if not use_potion:
                self.resurrection_count += 1
            
            # Restore some HP/MP
            self.combat_stats['hp'] = int(self.combat_stats['hp'] * 0.5)
            self.combat_stats['mp'] = int(self.combat_stats['mp'] * 0.5)
            
            return {
                'success': True,
                'current_hp': self.combat_stats['hp'],
                'current_mp': self.combat_stats['mp'],
                'resurrection_count': self.resurrection_count
            }
        return {'success': False, 'message': 'Cannot resurrect'}

    def can_resurrect(self) -> bool:
        """Check if player can resurrect without potion"""
        if self.last_death:
            # Can resurrect once per hour
            time_since_death = datetime.utcnow() - self.last_death
            return time_since_death.total_seconds() >= 3600
        return False

    def to_dict(self) -> Dict:
        """Convert player data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'level': self.level,
            'experience': self.experience,
            'player_class': self.player_class.value,
            'job_type': self.job_type.value if self.job_type else None,
            'stats': self.stats,
            'combat_stats': self.combat_stats,
            'class_levels': self.class_levels,
            'job_levels': self.job_levels,
            'achievements': self.achievements,
            'titles': self.titles,
            'activity_stats': {
                'gates_cleared': self.gates_cleared,
                'quests_completed': self.quests_completed,
                'monsters_killed': self.monsters_killed,
                'deaths': self.deaths,
                'pvp_wins': self.pvp_wins,
                'pvp_losses': self.pvp_losses
            },
            'status': {
                'is_alive': self.is_alive,
                'last_death': self.last_death.isoformat() if self.last_death else None,
                'resurrection_count': self.resurrection_count
            }
        }
