"""Announcement model definition."""

from .base import BaseModel, TimestampMixin
from database import db
from sqlalchemy import Column, String, Text

class Announcement(BaseModel, TimestampMixin):
    """Announcement model for system-wide announcements."""
    
    # Announcement fields
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    def __repr__(self):
        """String representation of Announcement."""
        return f'<Announcement {self.title}>'

    def to_dict(self):
        """Convert announcement to dictionary."""
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_latest(cls, limit=5):
        """Get latest announcements."""
        return cls.query.order_by(cls.created_at.desc()).limit(limit).all()
