"""
Database models initialization for Terminusa Online
"""
from flask_sqlalchemy import SQLAlchemy
from .base import BaseModel

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import all models
from .user import User
from .player import Player, PlayerClass, JobType, PlayerCharacter
from .inventory import Inventory, ItemType, ItemRarity
from .item import Item

# Import game-related models
from .announcement import Announcement
from .achievement import Achievement
from .gate import Gate
from .guild import Guild, GuildMember, GuildQuest
from .mount_pet import Mount, Pet
from .transaction import Transaction, TransactionType, TransactionStatus
from .wallet import Wallet, SwapTransaction, TaxConfig
from .currency import Currency
from .party import Party
from .social import Friend, BlockedUser
from .progression import PlayerProgress, ClassProgress, JobProgress

# Setup model relationships
def init_models():
    """Initialize model relationships"""
    
    # User relationships
    User.player = db.relationship('Player', backref='user', uselist=False)
    User.inventory = db.relationship('Inventory', backref='user', uselist=False)
    User.achievements = db.relationship('Achievement', backref='user')
    User.transactions = db.relationship('Transaction', backref='user')
    User.guild_membership = db.relationship('GuildMember', backref='user')
    User.progress = db.relationship('PlayerProgress', backref='user', uselist=False)
    User.announcements = db.relationship('Announcement', backref=db.backref('author', lazy='joined'), lazy='dynamic')
    User.friends = db.relationship('Friend',
        foreign_keys=[Friend.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )
    User.blocked = db.relationship('BlockedUser',
        foreign_keys=[BlockedUser.user_id],
        backref=db.backref('user', lazy='joined'),
        lazy='dynamic',
        cascade='all, delete-orphan'
    )

    # Player relationships
    Player.class_progress = db.relationship('ClassProgress', backref='player')
    Player.job_progress = db.relationship('JobProgress', backref='player')
    Player.mounts = db.relationship('Mount', backref='player')
    Player.pets = db.relationship('Pet', backref='player')

    # Guild relationships
    Guild.members = db.relationship('GuildMember', backref='guild')
    Guild.quests = db.relationship('GuildQuest', backref='guild')
    Guild.transactions = db.relationship('GuildTransaction', backref='guild')

    # Gate relationships
    Gate.cleared_by = db.relationship('User',
        secondary='gate_clears',
        backref=db.backref('cleared_gates', lazy='dynamic')
    )

def create_tables():
    """Create all database tables"""
    db.create_all()

def drop_tables():
    """Drop all database tables"""
    db.drop_all()
