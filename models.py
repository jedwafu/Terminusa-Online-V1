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
    password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    role = Column(String, default='user')
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    inventory = relationship("Inventory", back_populates="user", uselist=False)
    achievements = relationship("Achievement", secondary=user_achievements)
    guilds = relationship("Guild", secondary=guild_members)
    parties = relationship("Party", secondary=party_members)

class Wallet(Base):
    __tablename__ = 'wallets'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    address = Column(String, unique=True, nullable=False)
    encrypted_privkey = Column(String, nullable=False)
    iv = Column(String, nullable=False)
    sol_balance = Column(Float, default=0)
    crystals = Column(Integer, default=0)
    exons = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="wallet")

class Item(Base):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(SQLEnum(ItemType), nullable=False)
    rarity = Column(SQLEnum(ItemRarity), nullable=False)
    level_requirement = Column(Integer, default=1)
    stats = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Inventory(Base):
    __tablename__ = 'inventories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    max_slots = Column(Integer, default=100)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="inventory")
    items = relationship("InventoryItem", back_populates="inventory")

class InventoryItem(Base):
    __tablename__ = 'inventory_items'

    id = Column(Integer, primary_key=True)
    inventory_id = Column(Integer, ForeignKey('inventories.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    quantity = Column(Integer, default=1)
    slot = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory = relationship("Inventory", back_populates="items")
    item = relationship("Item")

class Guild(Base):
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    leader_id = Column(Integer, ForeignKey('users.id'))
    level = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)

class GuildMember(Base):
    __tablename__ = 'guild_member_details'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String, default='member')
    joined_at = Column(DateTime, default=datetime.utcnow)

class Party(Base):
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    leader_id = Column(Integer, ForeignKey('users.id'))
    max_size = Column(Integer, default=4)
    created_at = Column(DateTime, default=datetime.utcnow)

class PartyMember(Base):
    __tablename__ = 'party_member_details'

    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    joined_at = Column(DateTime, default=datetime.utcnow)

class PartyInvitation(Base):
    __tablename__ = 'party_invitations'

    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'))
    inviter_id = Column(Integer, ForeignKey('users.id'))
    invitee_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

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

class GateSession(Base):
    __tablename__ = 'gate_sessions'

    id = Column(Integer, primary_key=True)
    gate_id = Column(Integer, ForeignKey('gates.id'))
    party_id = Column(Integer, ForeignKey('parties.id'))
    status = Column(String, default='active')
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

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

class Achievement(Base):
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    requirements = Column(JSON)
    rewards = Column(JSON)
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
    transaction_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    channel = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSON)
