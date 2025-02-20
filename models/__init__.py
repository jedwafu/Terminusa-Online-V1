"""
Models package initialization.
Exposes all models through a clean interface while avoiding circular imports.
"""

from database import db

# Base models that don't have dependencies
from .currency import (
    Currency, Transaction, TokenSwap,
    CurrencyType, TransactionType
)

# Models with dependencies on base models
from .character import (
    PlayerCharacter, PlayerSkill, Skill, JobHistory, 
    JobQuest, HunterClass, BaseJob, HealthStatus
)

from .gate import (
    Gate, GateGrade, MagicBeast, MagicBeastType, 
    GateSession, AIBehavior
)

from .inventory import (
    Item, ItemType, Inventory, ItemRarity,
    Equipment, EquipmentSlot, EquipmentType
)

from .social import (
    Guild, GuildMember, GuildRank,
    Party, PartyMember, PartyRole,
    Friend, FriendStatus
)

from .progression import (
    Achievement, AchievementType,
    Quest, QuestType, QuestStatus,
    QuestProgress, QuestReward,
    Milestone, MilestoneType
)

from .ai import (
    AIModel, AITrainingData,
    AIEvaluation, AIMetric,
    PlayerActivity, ActivityType
)

# Define which models are exposed
__all__ = [
    # Currency related models
    'Currency', 'Transaction', 'TokenSwap',
    'CurrencyType', 'TransactionType',
    
    # Character related models
    'PlayerCharacter', 'PlayerSkill', 'Skill', 
    'JobHistory', 'JobQuest', 'HunterClass', 
    'BaseJob', 'HealthStatus',
    
    # Gate related models
    'Gate', 'GateGrade', 'MagicBeast', 
    'MagicBeastType', 'GateSession', 'AIBehavior',
    
    # Inventory related models
    'Item', 'ItemType', 'Inventory', 'ItemRarity',
    'Equipment', 'EquipmentSlot', 'EquipmentType',
    
    # Social related models
    'Guild', 'GuildMember', 'GuildRank',
    'Party', 'PartyMember', 'PartyRole',
    'Friend', 'FriendStatus',
    
    # Progression related models
    'Achievement', 'AchievementType',
    'Quest', 'QuestType', 'QuestStatus',
    'QuestProgress', 'QuestReward',
    'Milestone', 'MilestoneType',
    
    # AI related models
    'AIModel', 'AITrainingData',
    'AIEvaluation', 'AIMetric',
    'PlayerActivity', 'ActivityType'
]

# Initialize default data
def init_db():
    """Initialize database with default data"""
    from .currency import init_currencies
    
    # Admin wallet and username from environment variables
    admin_wallet = "FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw"
    admin_username = "adminbb"
    
    # Initialize currencies
    init_currencies(admin_wallet, admin_username)
