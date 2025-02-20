"""
Models package initialization.
Exposes all models through a clean interface.
"""

from database import db

# Import all models
from .gate import Gate, GateGrade, MagicBeast, MagicBeastType, GateSession, AIBehavior
from .character import (
    PlayerCharacter, PlayerSkill, Skill, JobHistory, 
    JobQuest, HunterClass, BaseJob, HealthStatus
)
from .currency import Currency, Transaction, CurrencyType, TransactionType
from .inventory import Item, ItemType, Inventory, ItemRarity
from .social import Guild, GuildMember, Party, PartyMember, Friend
from .progression import Achievement, Quest, QuestProgress, Milestone
from .ai import AIModel, AITrainingData, AIEvaluation, AIMetric

# Define which models are exposed
__all__ = [
    # Gate related models
    'Gate', 'GateGrade', 'MagicBeast', 'MagicBeastType', 
    'GateSession', 'AIBehavior',
    
    # Character related models
    'PlayerCharacter', 'PlayerSkill', 'Skill', 'JobHistory',
    'JobQuest', 'HunterClass', 'BaseJob', 'HealthStatus',
    
    # Currency related models
    'Currency', 'Transaction', 'CurrencyType', 'TransactionType',
    
    # Inventory related models
    'Item', 'ItemType', 'Inventory', 'ItemRarity',
    
    # Social related models
    'Guild', 'GuildMember', 'Party', 'PartyMember', 'Friend',
    
    # Progression related models
    'Achievement', 'Quest', 'QuestProgress', 'Milestone',
    
    # AI related models
    'AIModel', 'AITrainingData', 'AIEvaluation', 'AIMetric'
]
