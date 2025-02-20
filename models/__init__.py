"""
Models package for Terminusa Online.
Contains all database models for the application.
"""

from database import db
from .base import User, Announcement
from .gate import Gate, GateGrade, MagicBeast, MagicBeastType, GateSession, AIBehavior
from .character import PlayerCharacter, PlayerSkill, Skill, JobHistory, JobQuest, HunterClass, BaseJob, HealthStatus
from .currency import Currency, CurrencyType, Wallet, Transaction, TokenSwap, LoyaltyReward
from .inventory import Item, ItemType, ItemGrade, ItemSlot, Inventory, InventoryItem, EquippedItem, ItemDrop, Trade, TradeItem, ShopTransaction
from .social import Guild, GuildRank, GuildMember, GuildQuest, GuildLog, Party, PartyMember, PartyInvitation, PartyLog
from .progression import Achievement, Quest, QuestType, QuestStatus, PlayerQuest, PlayerAchievement, QuestLog, QuestBank, ReferralReward
from .ai import AIModel, AIModelType, PlayerActivityType, PlayerProfile, ActivityLog, AIDecision, GachaSystem, GachaHistory, GamblingSystem, GamblingHistory

# Initialize all models
def init_app(app):
    """Initialize all models with the app"""
    db.init_app(app)

# Export all models
__all__ = [
    # Database
    'db', 'init_app',
    
    # Base Models
    'User', 'Announcement',
    
    # Gate Models
    'Gate', 'GateGrade', 'MagicBeast', 'MagicBeastType',
    'GateSession', 'AIBehavior',
    
    # Character Models
    'PlayerCharacter', 'PlayerSkill', 'Skill', 'JobHistory',
    'JobQuest', 'HunterClass', 'BaseJob', 'HealthStatus',
    
    # Currency Models
    'Currency', 'CurrencyType', 'Wallet', 'Transaction',
    'TokenSwap', 'LoyaltyReward',
    
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
    'QuestBank', 'ReferralReward',
    
    # AI Models
    'AIModel', 'AIModelType', 'PlayerActivityType',
    'PlayerProfile', 'ActivityLog', 'AIDecision',
    'GachaSystem', 'GachaHistory', 'GamblingSystem',
    'GamblingHistory'
]
