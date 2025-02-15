from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Table, JSON, Enum as SQLEnum
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
import enum

Base = declarative_base()

# Association Tables
user_achievements = Table(
    'user_achievements', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('achievement_id', Integer, ForeignKey('achievements.id'))
)

user_items = Table(
    'user_items', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('item_id', Integer, ForeignKey('items.id'))
)

guild_members = Table(
    'guild_members', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('guild_id', Integer, ForeignKey('guilds.id')),
    Column('role', String)
)

party_members = Table(
    'party_members', Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('party_id', Integer, ForeignKey('parties.id'))
)

# Enums
class UserRole(enum.Enum):
    PLAYER = "player"
    MODERATOR = "moderator"
    ADMIN = "admin"

class ItemType(enum.Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    QUEST = "quest"

class ItemRarity(enum.Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"

class GateType(enum.Enum):
    NORMAL = "normal"
    ELITE = "elite"
    BOSS = "boss"
    EVENT = "event"

# Models
class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password_hash = Column(String, nullable=False)
    role = Column(SQLEnum(UserRole), default=UserRole.PLAYER)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    gold = Column(Integer, default=0)
    crystals = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    is_active = Column(Boolean, default=True)
    settings = Column(JSON)

    # Relationships
    inventory = relationship("Inventory", back_populates="user")
    achievements = relationship("Achievement", secondary=user_achievements)
    guild_memberships = relationship("Guild", secondary=guild_members)
    party_memberships = relationship("Party", secondary=party_members)
    wallet = relationship("Wallet", back_populates="user")

class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(SQLEnum(ItemType), nullable=False)
    rarity = Column(SQLEnum(ItemRarity), nullable=False)
    level_requirement = Column(Integer, default=1)
    stats = Column(JSON)
    tradeable = Column(Boolean, default=True)
    stackable = Column(Boolean, default=False)
    max_stack = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class Inventory(Base):
    __tablename__ = 'inventories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    max_slots = Column(Integer, default=100)
    items = Column(JSON)  # {slot_id: {item_id, quantity}}
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="inventory")

class Wallet(Base):
    __tablename__ = 'wallets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    balance = Column(JSON)  # {currency: amount}
    created_at = Column(DateTime, default=datetime.utcnow)
    last_updated = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wallet")

class Guild(Base):
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    leader_id = Column(Integer, ForeignKey('users.id'))
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    members = relationship("User", secondary=guild_members)
    settings = Column(JSON)

class Party(Base):
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    leader_id = Column(Integer, ForeignKey('users.id'))
    max_size = Column(Integer, default=4)
    created_at = Column(DateTime, default=datetime.utcnow)
    members = relationship("User", secondary=party_members)
    settings = Column(JSON)

class Achievement(Base):
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    requirements = Column(JSON)
    rewards = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Gate(Base):
    __tablename__ = 'gates'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(SQLEnum(GateType), nullable=False)
    level_requirement = Column(Integer, default=1)
    min_players = Column(Integer, default=1)
    max_players = Column(Integer, default=4)
    rewards = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class MagicBeast(Base):
    __tablename__ = 'magic_beasts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    level = Column(Integer, default=1)
    stats = Column(JSON)
    abilities = Column(JSON)
    drops = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIBehavior(Base):
    __tablename__ = 'ai_behaviors'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    conditions = Column(JSON)
    actions = Column(JSON)
    priorities = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(Base):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    description = Column(String)
    transaction_metadata = Column(JSON)  # Changed from metadata to transaction_metadata
    created_at = Column(DateTime, default=datetime.utcnow)

class MarketListing(Base):
    __tablename__ = 'market_listings'

    id = Column(Integer, primary_key=True)
    seller_id = Column(Integer, ForeignKey('users.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    quantity = Column(Integer, default=1)
    price = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='active')

class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    channel = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSON)  # Changed from metadata to message_metadata

class UserSession(Base):
    __tablename__ = 'user_sessions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    token = Column(String, nullable=False)
    ip_address = Column(String)
    user_agent = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)
    last_activity = Column(DateTime)

class AuditLog(Base):
    __tablename__ = 'audit_logs'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String, nullable=False)
    details = Column(JSON)
    ip_address = Column(String)
    created_at = Column(DateTime, default=datetime.utcnow)

class SystemMetric(Base):
    __tablename__ = 'system_metrics'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    tags = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class GameEvent(Base):
    __tablename__ = 'game_events'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    rewards = Column(JSON)
    requirements = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
    status = Column(String, default='scheduled')
