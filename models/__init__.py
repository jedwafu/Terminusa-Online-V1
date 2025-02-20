"""
Models package initialization.
Exposes all models through a clean interface while avoiding circular imports.
"""

from database import db

# Import base model and mixins
from .user import User  # Add User model import
from .base import (
    BaseModel, SoftDeleteMixin, TimestampMixin,
    VersionMixin, StatusMixin, AuditMixin
)

# Base models that don't have dependencies
from .currency import (
    Currency, Transaction, TokenSwap,
    CurrencyType, TransactionType,
    init_currencies
)

from .inventory import (
    Item, ItemType, Inventory, ItemRarity,
    Equipment, EquipmentSlot, EquipmentType,
    init_items
)

from .ai import (
    AIModel, AITrainingData, AIEvaluation,
    AIMetric, ActivityType, PlayerActivity,
    init_ai_models
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

from .social import (
    Guild, GuildMember, GuildRank,
    Party, PartyMember, PartyRole,
    Friend, FriendStatus,
    init_guild_settings
)

from .progression import (
    Achievement, AchievementType,
    Quest, QuestType, QuestStatus,
    QuestProgress, QuestReward,
    Milestone, MilestoneType,
    UserAchievement, UserMilestone,
    init_progression
)

# Define which models are exposed
__all__ = [
    # User model
    'User',
    
    # Base models and mixins
    'BaseModel', 'SoftDeleteMixin', 'TimestampMixin',
    'VersionMixin', 'StatusMixin', 'AuditMixin',
    
    # Currency related models
    'Currency', 'Transaction', 'TokenSwap',
    'CurrencyType', 'TransactionType',
    
    # Inventory related models
    'Item', 'ItemType', 'Inventory', 'ItemRarity',
    'Equipment', 'EquipmentSlot', 'EquipmentType',
    
    # AI related models
    'AIModel', 'AITrainingData', 'AIEvaluation',
    'AIMetric', 'ActivityType', 'PlayerActivity',
    
    # Character related models
    'PlayerCharacter', 'PlayerSkill', 'Skill', 
    'JobHistory', 'JobQuest', 'HunterClass', 
    'BaseJob', 'HealthStatus',
    
    # Gate related models
    'Gate', 'GateGrade', 'MagicBeast', 
    'MagicBeastType', 'GateSession', 'AIBehavior',
    
    # Social related models
    'Guild', 'GuildMember', 'GuildRank',
    'Party', 'PartyMember', 'PartyRole',
    'Friend', 'FriendStatus',
    
    # Progression related models
    'Achievement', 'AchievementType',
    'Quest', 'QuestType', 'QuestStatus',
    'QuestProgress', 'QuestReward',
    'Milestone', 'MilestoneType',
    'UserAchievement', 'UserMilestone'
]

# Initialize database with default data
def init_db():
    """Initialize database with default data"""
    # Admin wallet and username from environment variables
    admin_wallet = "FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw"
    admin_username = "adminbb"
    
    # Initialize all models in correct order
    init_currencies(admin_wallet, admin_username)
    init_items()
    init_ai_models()
    init_guild_settings()
    init_progression()
