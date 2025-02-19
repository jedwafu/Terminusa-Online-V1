from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from enum import Enum

db = SQLAlchemy()

class HunterClass(Enum):
    F = "F"
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"

class JobClass(Enum):
    FIGHTER = "Fighter"
    MAGE = "Mage"
    ASSASSIN = "Assassin"
    ARCHER = "Archer"
    HEALER = "Healer"

class GateRank(Enum):
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    MONARCH = "Monarch"

class ItemRarity(Enum):
    COMMON = "Common"
    UNCOMMON = "Uncommon"
    RARE = "Rare"
    EPIC = "Epic"
    LEGENDARY = "Legendary"
    IMMORTAL = "Immortal"

class MountPetRarity(Enum):
    BASIC = "Basic"
    INTERMEDIATE = "Intermediate"
    EXCELLENT = "Excellent"
    LEGENDARY = "Legendary"
    IMMORTAL = "Immortal"

class HealthStatus(Enum):
    NORMAL = "Normal"
    BURNED = "Burned"
    POISONED = "Poisoned"
    FROZEN = "Frozen"
    FEARED = "Feared"
    CONFUSED = "Confused"
    DISMEMBERED = "Dismembered"
    DECAPITATED = "Decapitated"
    SHADOW = "Shadow"

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    web3_wallet = db.Column(db.String(64))
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Game-specific fields
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.BigInteger, default=0)
    hunter_class = db.Column(db.Enum(HunterClass), default=HunterClass.F)
    job_class = db.Column(db.Enum(JobClass))
    job_level = db.Column(db.Integer, default=1)
    
    # Currencies
    solana_balance = db.Column(db.Float, default=0.0)
    exons_balance = db.Column(db.Float, default=0.0)
    crystals = db.Column(db.Integer, default=100)  # Starting crystals
    
    # Stats
    strength = db.Column(db.Integer, default=10)
    agility = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    vitality = db.Column(db.Integer, default=10)
    luck = db.Column(db.Integer, default=10)
    
    # Combat stats
    hp = db.Column(db.Integer, default=100)
    max_hp = db.Column(db.Integer, default=100)
    mp = db.Column(db.Integer, default=100)
    max_mp = db.Column(db.Integer, default=100)
    
    # Status
    health_status = db.Column(db.Enum(HealthStatus), default=HealthStatus.NORMAL)
    is_in_gate = db.Column(db.Boolean, default=False)
    is_in_party = db.Column(db.Boolean, default=False)
    inventory_slots = db.Column(db.Integer, default=20)
    
    # Relationships
    inventory_items = db.relationship('InventoryItem', backref='owner', lazy=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'))
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id'))
    achievements = db.relationship('Achievement', backref='user', lazy=True)
    quests = db.relationship('Quest', backref='user', lazy=True)
    skills = db.relationship('Skill', backref='user', lazy=True)
    mounts = db.relationship('Mount', backref='owner', lazy=True)
    pets = db.relationship('Pet', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

class Guild(db.Model):
    __tablename__ = 'guilds'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.BigInteger, default=0)
    crystals = db.Column(db.Integer, default=0)
    exons_balance = db.Column(db.Float, default=0.0)
    
    # Specify foreign_keys for the relationship to resolve ambiguity
    members = db.relationship('User', 
                            foreign_keys=[User.guild_id],
                            backref='guild', 
                            lazy=True)
    leader = db.relationship('User',
                           foreign_keys=[leader_id],
                           backref='led_guild',
                           lazy=True)
    quests = db.relationship('GuildQuest', backref='guild', lazy=True)

class Party(db.Model):
    __tablename__ = 'parties'
    
    id = db.Column(db.Integer, primary_key=True)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    gate_id = db.Column(db.Integer, db.ForeignKey('gates.id'))
    is_in_combat = db.Column(db.Boolean, default=False)
    
    # Specify foreign_keys for the relationships to resolve ambiguity
    members = db.relationship('User',
                            foreign_keys=[User.party_id],
                            backref='party',
                            lazy=True)
    leader = db.relationship('User',
                           foreign_keys=[leader_id],
                           backref='led_party',
                           lazy=True)

class Gate(db.Model):
    __tablename__ = 'gates'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    rank = db.Column(db.Enum(GateRank), nullable=False)
    min_level = db.Column(db.Integer, default=1)
    min_hunter_class = db.Column(db.Enum(HunterClass), default=HunterClass.F)
    crystal_reward_min = db.Column(db.Integer)
    crystal_reward_max = db.Column(db.Integer)
    
    magic_beasts = db.relationship('MagicBeast', backref='gate', lazy=True)
    active_parties = db.relationship('Party', backref='gate', lazy=True)

class MagicBeast(db.Model):
    __tablename__ = 'magic_beasts'
    
    id = db.Column(db.Integer, primary_key=True)
    gate_id = db.Column(db.Integer, db.ForeignKey('gates.id'))
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    rank = db.Column(db.Enum(GateRank))
    hp = db.Column(db.Integer)
    max_hp = db.Column(db.Integer)
    mp = db.Column(db.Integer)
    max_mp = db.Column(db.Integer)
    is_monarch = db.Column(db.Boolean, default=False)
    is_shadow = db.Column(db.Boolean, default=False)
    shadow_owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'))
    quantity = db.Column(db.Integer, default=1)
    durability = db.Column(db.Integer, default=100)
    is_equipped = db.Column(db.Boolean, default=False)

class Item(db.Model):
    __tablename__ = 'items'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.String(50))  # equipment, potion, etc.
    rarity = db.Column(db.Enum(ItemRarity))
    level_requirement = db.Column(db.Integer, default=1)
    price_crystals = db.Column(db.Integer)
    price_exons = db.Column(db.Float)
    is_tradeable = db.Column(db.Boolean, default=True)

class Mount(db.Model):
    __tablename__ = 'mounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.Enum(MountPetRarity))
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.BigInteger, default=0)
    is_active = db.Column(db.Boolean, default=False)

class Pet(db.Model):
    __tablename__ = 'pets'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    rarity = db.Column(db.Enum(MountPetRarity))
    level = db.Column(db.Integer, default=1)
    exp = db.Column(db.BigInteger, default=0)
    is_active = db.Column(db.Boolean, default=False)

class Skill(db.Model):
    __tablename__ = 'skills'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    level = db.Column(db.Integer, default=1)
    mp_cost = db.Column(db.Integer)
    cooldown = db.Column(db.Integer)  # in seconds
    damage = db.Column(db.Integer)
    heal = db.Column(db.Integer)
    status_effect = db.Column(db.Enum(HealthStatus))
    is_resurrection = db.Column(db.Boolean, default=False)
    is_arise = db.Column(db.Boolean, default=False)

class Quest(db.Model):
    __tablename__ = 'quests'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    requirements = db.Column(db.JSON)
    rewards = db.Column(db.JSON)
    is_completed = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)
    is_job_quest = db.Column(db.Boolean, default=False)

class GuildQuest(db.Model):
    __tablename__ = 'guild_quests'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    requirements = db.Column(db.JSON)
    rewards = db.Column(db.JSON)
    is_completed = db.Column(db.Boolean, default=False)
    expires_at = db.Column(db.DateTime)

class Achievement(db.Model):
    __tablename__ = 'achievements'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    requirements = db.Column(db.JSON)
    rewards = db.Column(db.JSON)
    is_completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    from_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    to_user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    currency_type = db.Column(db.String(20))  # solana, exons, crystals
    amount = db.Column(db.Float)
    tax_amount = db.Column(db.Float)
    transaction_type = db.Column(db.String(50))  # trade, shop, gate_reward, etc.
    transaction_hash = db.Column(db.String(100))  # for blockchain transactions
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

def init_db(app):
    """Initialize database with Flask app context"""
    db.init_app(app)
    with app.app_context():
        db.create_all()
