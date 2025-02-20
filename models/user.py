"""User model definition."""

from .base import BaseModel, StatusMixin, TimestampMixin
from database import db
from sqlalchemy import Column, String, Boolean

class User(BaseModel, StatusMixin, TimestampMixin):
    """User model for authentication and profile management."""
    
    # User authentication fields
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password_hash = Column(String(128), nullable=False)
    
    # User role
    is_admin = Column(Boolean, default=False)

    def __repr__(self):
        """String representation of User."""
        return f'<User {self.username}>'

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'is_active': self.is_active
        }

    @classmethod
    def get_by_username(cls, username):
        """Get user by username."""
        return cls.query.filter_by(username=username).first()

    @classmethod
    def get_by_email(cls, email):
        """Get user by email."""
        return cls.query.filter_by(email=email).first()
