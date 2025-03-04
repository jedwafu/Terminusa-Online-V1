"""
Fix for indentation error in the Announcement model
"""
import os

def fix_announcement_model():
    """Fix the Announcement model to prevent circular imports and fix indentation"""
    # Create a new version with correct indentation
    new_content = """\"\"\"Announcement model definition.\"\"\"

from .base import BaseModel, TimestampMixin
from database import db
from sqlalchemy import Column, String, Text, Integer, Boolean, ForeignKey
from sqlalchemy.orm import relationship

class Announcement(BaseModel, TimestampMixin):
    \"\"\"Announcement model for system-wide announcements.\"\"\"
    
    # Announcement fields
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    is_active = Column(Boolean, default=True)
    
    # Author relationship - use nullable=True to allow announcements without authors
    author_id = Column(Integer, ForeignKey('users.id', name='fk_announcement_author'), nullable=True)
    
    # Use property instead of direct relationship to avoid circular imports
    @property
    def author_name(self):
        \"\"\"Get the author's username if available.\"\"\"
        if not self.author_id:
            return None
        
        # Import User here to avoid circular imports
        from .user import User
        author = User.query.get(self.author_id)
        return author.username if author else None

    def __repr__(self):
        \"\"\"String representation of Announcement.\"\"\"
        return f'<Announcement {self.title}>'

    def to_dict(self):
        \"\"\"Convert announcement to dictionary.\"\"\"
        return {
            'id': self.id,
            'title': self.title,
            'content': self.content,
            'priority': self.priority,
            'is_active': self.is_active,
            'author': self.author_name,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

    @classmethod
    def get_latest(cls, limit=5):
        \"\"\"Get latest active announcements.\"\"\"
        return cls.query.filter_by(is_active=True)\\
            .order_by(cls.priority.desc(), cls.created_at.desc())\\
            .limit(limit)\\
            .all()

    @classmethod
    def get_all_active(cls):
        \"\"\"Get all active announcements.\"\"\"
        return cls.query.filter_by(is_active=True)\\
            .order_by(cls.priority.desc(), cls.created_at.desc())\\
            .all()

    @classmethod
    def get_by_id(cls, announcement_id):
        \"\"\"Get announcement by ID.\"\"\"
        return cls.query.get(announcement_id)
"""

    # Write the modified content back to models/announcement.py
    with open('models/announcement.py', 'w') as f:
        f.write(new_content)

    print("Successfully modified models/announcement.py with correct indentation")

if __name__ == "__main__":
    fix_announcement_model()
