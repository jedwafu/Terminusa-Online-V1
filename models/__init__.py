"""Models package initialization."""

from .base import BaseModel, StatusMixin, TimestampMixin
from .user import User
from .announcement import Announcement
from .currency import Currency, Transaction, TokenSwap, CurrencyType, TransactionType
from .gate import Gate
from .character import Character
from .inventory import Inventory
from .social import Social
from .progression import Progression
from .ai import AI

__all__ = [
    'BaseModel',
    'StatusMixin',
    'TimestampMixin',
    'User',
    'Announcement',
    'Currency',
    'Transaction',
    'TokenSwap',
    'CurrencyType',
    'TransactionType',
    'Gate',
    'Character',
    'Inventory',
    'Social',
    'Progression',
    'AI'
]

# Configure SQLAlchemy event listeners and model relationships
from sqlalchemy import event
from sqlalchemy.orm import configure_mappers

# Configure all mappers
configure_mappers()
