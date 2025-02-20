from database import db
from .base import User, Announcement

# Initialize all models
def init_app(app):
    """Initialize all models with the app"""
    db.init_app(app)

__all__ = ['db', 'User', 'Announcement', 'init_app']
