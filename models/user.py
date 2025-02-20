"""User model definition."""

from flask_login import UserMixin
from .base import BaseModel, StatusMixin, TimestampMixin
from database import db
from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship

class User(BaseModel, StatusMixin, TimestampMixin, UserMixin):
    """User model for authentication and profile management."""
    
    # User authentication fields
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    password = Column(String(128), nullable=False)
    salt = Column(String(128), nullable=True)
    
    # User role and status
    role = Column(String(20), default='player')
    is_admin = Column(Boolean, default=False)
    is_email_verified = Column(Boolean, default=False)
    
    # Timestamps
    last_login = Column(DateTime, nullable=True)

    # Relationships
    currencies = relationship('Currency', back_populates='user', lazy='dynamic')
    transactions = relationship('Transaction', back_populates='user', lazy='dynamic')
    token_swaps = relationship('TokenSwap', back_populates='user', lazy='dynamic')
    characters = relationship('PlayerCharacter', back_populates='user', lazy='dynamic')  # Added relationship

    def __repr__(self):
        """String representation of User."""
        return f'<User {self.username}>'

    def to_dict(self):
        """Convert user to dictionary."""
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'role': self.role,
            'is_admin': self.is_admin,
            'is_email_verified': self.is_email_verified,
            'last_login': self.last_login.isoformat() if self.last_login else None,
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

    def get_id(self):
        """Required by Flask-Login."""
        return str(self.id)

    @property
    def is_authenticated(self):
        """Required by Flask-Login."""
        return True

    @property
    def is_active(self):
        """Required by Flask-Login."""
        return self.status == 'active'

    @property
    def is_anonymous(self):
        """Required by Flask-Login."""
        return False
