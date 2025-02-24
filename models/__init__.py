"""
Database models initialization for Terminusa Online
"""
from flask_sqlalchemy import SQLAlchemy

# Initialize SQLAlchemy
db = SQLAlchemy()

# Import all models
from .user import User
from .player import Player, PlayerClass, JobType
from .inventory import Inventory, ItemType, ItemRarity
from .item import Item

# Import game-related models
from .announcement import Announcement
from .achievement import Achievement
from .gate import Gate
from .guild import Guild, GuildMember, GuildQuest
from .mount_pet import Mount, Pet
from .transaction import Transaction
from .currency import Currency
from .social import Friend, BlockedUser
from .progression import PlayerProgress, ClassProgress, JobProgress



def create_tables():
    """Create all database tables"""
    db.create_all()

def drop_tables():
    """Drop all database tables"""
    db.drop_all()
