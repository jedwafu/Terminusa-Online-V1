from datetime import datetime
from typing import Dict, List, Optional, Any
from sqlalchemy import (
    Column, Integer, String, Float, Boolean, DateTime,
    ForeignKey, Table, JSON, Enum as SQLEnum, Text
)
from sqlalchemy.orm import relationship
from database import db
import enum

# Association Tables
user_achievements = Table(
    'user_achievements', db.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('achievement_id', Integer, ForeignKey('achievements.id'))
)

guild_members = Table(
    'guild_members', db.metadata,
    Column('user_id', Integer, ForeignKey('users.id')),
    Column('guild_id', Integer, ForeignKey('guilds.id')),
    Column('role', String)
)

party_members = Table(
    'party_members', db.metadata,
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
    SKILL_BOOK = "skill_book"
    RUNE = "rune"

class ItemRarity(enum.Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHIC = "mythic"
    DIVINE = "divine"

class GateType(enum.Enum):
    NORMAL = "normal"
    ELITE = "elite"
    BOSS = "boss"
    EVENT = "event"
    DUNGEON = "dungeon"
    RAID = "raid"

class SkillType(enum.Enum):
    PASSIVE = "passive"
    ACTIVE = "active"
    ULTIMATE = "ultimate"
    SPECIAL = "special"

class DamageType(enum.Enum):
    PHYSICAL = "physical"
    MAGICAL = "magical"
    TRUE = "true"
    ELEMENTAL = "elemental"

# Models
class User(db.Model):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    password = Column(String, nullable=False)
    salt = Column(String, nullable=False)
    role = Column(String, default='player')
    is_email_verified = Column(Boolean, default=False)
    email_verification_token = Column(String, unique=True)
    email_verification_sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    last_active = Column(DateTime)

    # Relationships
    wallet = relationship("Wallet", back_populates="user", uselist=False)
    inventory = relationship("Inventory", back_populates="user", uselist=False)
    character = relationship("PlayerCharacter", back_populates="user", uselist=False)
    achievements = relationship("Achievement", secondary=user_achievements)
    guilds = relationship("Guild", secondary=guild_members)
    parties = relationship("Party", secondary=party_members)

class PlayerCharacter(db.Model):
    __tablename__ = 'player_characters'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    rank = Column(String, default='F')
    title = Column(String)
    
    # Base Stats
    strength = Column(Integer, default=10)
    agility = Column(Integer, default=10)
    intelligence = Column(Integer, default=10)
    vitality = Column(Integer, default=10)
    wisdom = Column(Integer, default=10)
    
    # Derived Stats
    hp = Column(Integer, default=100)
    mp = Column(Integer, default=100)
    hp_regen = Column(Float, default=1.0)
    mp_regen = Column(Float, default=1.0)
    physical_attack = Column(Integer, default=10)
    magical_attack = Column(Integer, default=10)
    physical_defense = Column(Integer, default=10)
    magical_defense = Column(Integer, default=10)
    
    # Combat Stats
    critical_chance = Column(Float, default=5.0)
    critical_damage = Column(Float, default=150.0)
    dodge_chance = Column(Float, default=5.0)
    hit_chance = Column(Float, default=95.0)
    
    # Status
    status_effects = Column(JSON, default=dict)
    buffs = Column(JSON, default=dict)
    debuffs = Column(JSON, default=dict)
    
    # Skills and Abilities
    skills = relationship("PlayerSkill", back_populates="character")
    equipped_skills = Column(JSON, default=dict)
    
    # Progress
    gates_cleared = Column(Integer, default=0)
    bosses_defeated = Column(Integer, default=0)
    quests_completed = Column(Integer, default=0)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, onupdate=datetime.utcnow)
    
    user = relationship("User", back_populates="character")

class PlayerSkill(db.Model):
    __tablename__ = 'player_skills'

    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('player_characters.id'))
    name = Column(String, nullable=False)
    description = Column(Text)
    type = Column(SQLEnum(SkillType), nullable=False)
    level = Column(Integer, default=1)
    max_level = Column(Integer, default=10)
    damage_type = Column(SQLEnum(DamageType))
    cooldown = Column(Float)
    mana_cost = Column(Integer)
    effects = Column(JSON)
    requirements = Column(JSON)
    
    character = relationship("PlayerCharacter", back_populates="skills")

class Wallet(db.Model):
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

class Item(db.Model):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(SQLEnum(ItemType), nullable=False)
    rarity = Column(SQLEnum(ItemRarity), nullable=False)
    level_requirement = Column(Integer, default=1)
    stats = Column(JSON)
    effects = Column(JSON)
    durability = Column(Integer)
    max_durability = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

class Inventory(db.Model):
    __tablename__ = 'inventories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), unique=True)
    max_slots = Column(Integer, default=20)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="inventory")
    items = relationship("InventoryItem", back_populates="inventory")

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'

    id = Column(Integer, primary_key=True)
    inventory_id = Column(Integer, ForeignKey('inventories.id'))
    item_id = Column(Integer, ForeignKey('items.id'))
    quantity = Column(Integer, default=1)
    slot = Column(Integer)
    is_equipped = Column(Boolean, default=False)
    durability = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    inventory = relationship("Inventory", back_populates="items")
    item = relationship("Item")

class Guild(db.Model):
    __tablename__ = 'guilds'

    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)
    description = Column(String)
    leader_id = Column(Integer, ForeignKey('users.id'))
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

class GuildMember(db.Model):
    __tablename__ = 'guild_member_details'

    id = Column(Integer, primary_key=True)
    guild_id = Column(Integer, ForeignKey('guilds.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    role = Column(String, default='member')
    contribution = Column(Integer, default=0)
    joined_at = Column(DateTime, default=datetime.utcnow)

class Party(db.Model):
    __tablename__ = 'parties'

    id = Column(Integer, primary_key=True)
    leader_id = Column(Integer, ForeignKey('users.id'))
    max_size = Column(Integer, default=4)
    created_at = Column(DateTime, default=datetime.utcnow)

class PartyMember(db.Model):
    __tablename__ = 'party_member_details'

    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'))
    user_id = Column(Integer, ForeignKey('users.id'))
    joined_at = Column(DateTime, default=datetime.utcnow)

class PartyInvitation(db.Model):
    __tablename__ = 'party_invitations'

    id = Column(Integer, primary_key=True)
    party_id = Column(Integer, ForeignKey('parties.id'))
    inviter_id = Column(Integer, ForeignKey('users.id'))
    invitee_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String, default='pending')
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)

class Gate(db.Model):
    __tablename__ = 'gates'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    type = Column(SQLEnum(GateType), nullable=False)
    level_requirement = Column(Integer, default=1)
    rank_requirement = Column(String, default='F')
    min_players = Column(Integer, default=1)
    max_players = Column(Integer, default=4)
    rewards = Column(JSON)
    monster_level = Column(Integer, default=1)
    monster_rank = Column(String, default='F')
    clear_conditions = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

    @property
    def grade(self):
        """Calculate grade based on level requirement and monster rank"""
        grades = ['E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS']
        base_index = min(self.level_requirement // 10, len(grades) - 1)
        rank_bonus = {'F': 0, 'E': 0, 'D': 1, 'C': 1, 'B': 2, 'A': 2, 'S': 3}
        index = min(base_index + rank_bonus.get(self.monster_rank, 0), len(grades) - 1)
        return grades[index]

    @property
    def min_level(self):
        """Alias for level_requirement"""
        return self.level_requirement

    @property
    def crystal_reward(self):
        """Calculate crystal reward based on grade"""
        base_rewards = {
            'E': 10, 'D': 20, 'C': 40, 'B': 80,
            'A': 160, 'S': 320, 'SS': 640, 'SSS': 1280
        }
        return base_rewards.get(self.grade, 10)

    @property
    def magic_beasts(self):
        """Get magic beasts for this gate from monster data"""
        from sqlalchemy import text
        result = db.session.execute(
            text("""
                SELECT mb.* FROM magic_beasts mb
                WHERE mb.level <= :monster_level
                AND mb.rank = :monster_rank
                LIMIT 3
            """),
            {'monster_level': self.monster_level, 'monster_rank': self.monster_rank}
        )
        return [dict(r) for r in result]

class GateSession(db.Model):
    __tablename__ = 'gate_sessions'

    id = Column(Integer, primary_key=True)
    gate_id = Column(Integer, ForeignKey('gates.id'))
    party_id = Column(Integer, ForeignKey('parties.id'))
    status = Column(String, default='active')
    started_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)
    clear_time = Column(Integer)  # in seconds
    rewards_claimed = Column(Boolean, default=False)

class MagicBeast(db.Model):
    __tablename__ = 'magic_beasts'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    level = Column(Integer, default=1)
    rank = Column(String, default='F')
    stats = Column(JSON)
    abilities = Column(JSON)
    drops = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    requirements = Column(JSON)
    rewards = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class AIBehavior(db.Model):
    __tablename__ = 'ai_behaviors'

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    description = Column(String)
    conditions = Column(JSON)
    actions = Column(JSON)
    priorities = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    type = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    currency = Column(String, nullable=False)
    description = Column(String)
    transaction_metadata = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)

class ChatMessage(db.Model):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True)
    sender_id = Column(Integer, ForeignKey('users.id'))
    channel = Column(String, nullable=False)
    content = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    message_metadata = Column(JSON)
