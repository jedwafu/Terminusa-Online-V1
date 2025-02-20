from flask_sqlalchemy import SQLAlchemy
from app import db

# Import all models
from .currency import (
    Currency, CurrencyType, Wallet, Transaction, 
    TokenSwap, LoyaltyReward
)

from .character import (
    PlayerCharacter, PlayerSkill, Skill, JobHistory,
    JobQuest, HunterClass, BaseJob, HealthStatus
)

from .gate import (
    Gate, GateGrade, MagicBeast, MagicBeastType,
    GateSession, AIBehavior, gate_magic_beasts
)

from .inventory import (
    Item, ItemType, ItemGrade, ItemSlot, Inventory,
    InventoryItem, EquippedItem, ItemDrop, Trade,
    TradeItem, ShopTransaction
)

from .social import (
    Guild, GuildRank, GuildMember, GuildQuest,
    GuildLog, Party, PartyMember, PartyInvitation,
    PartyLog
)

from .progression import (
    Achievement, Quest, QuestType, QuestStatus,
    PlayerQuest, PlayerAchievement, QuestLog,
    QuestBank, ReferralReward, user_achievements
)

from .ai import (
    AIModel, AIModelType, PlayerActivityType,
    PlayerProfile, ActivityLog, AIDecision,
    GachaSystem, GachaHistory, GamblingSystem,
    GamblingHistory
)

# List all models for easy access
__all__ = [
    # Currency Models
    'Currency', 'CurrencyType', 'Wallet', 'Transaction',
    'TokenSwap', 'LoyaltyReward',
    
    # Character Models
    'PlayerCharacter', 'PlayerSkill', 'Skill', 'JobHistory',
    'JobQuest', 'HunterClass', 'BaseJob', 'HealthStatus',
    
    # Gate Models
    'Gate', 'GateGrade', 'MagicBeast', 'MagicBeastType',
    'GateSession', 'AIBehavior', 'gate_magic_beasts',
    
    # Inventory Models
    'Item', 'ItemType', 'ItemGrade', 'ItemSlot', 'Inventory',
    'InventoryItem', 'EquippedItem', 'ItemDrop', 'Trade',
    'TradeItem', 'ShopTransaction',
    
    # Social Models
    'Guild', 'GuildRank', 'GuildMember', 'GuildQuest',
    'GuildLog', 'Party', 'PartyMember', 'PartyInvitation',
    'PartyLog',
    
    # Progression Models
    'Achievement', 'Quest', 'QuestType', 'QuestStatus',
    'PlayerQuest', 'PlayerAchievement', 'QuestLog',
    'QuestBank', 'ReferralReward', 'user_achievements',
    
    # AI Models
    'AIModel', 'AIModelType', 'PlayerActivityType',
    'PlayerProfile', 'ActivityLog', 'AIDecision',
    'GachaSystem', 'GachaHistory', 'GamblingSystem',
    'GamblingHistory'
]

# Initialize all models
def init_app(app):
    """Initialize all models with the app"""
    db.init_app(app)
