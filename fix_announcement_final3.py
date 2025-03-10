# Read the current content of models/announcement.py
with open('models/announcement.py', 'r') as f:
    content = f.read()

# Replace the entire file with a new version that doesn't use the relationship
new_content = """\"\"\"Announcement model definition.\"\"\"

from .base import BaseModel, TimestampMixin
from database import db
from sqlalchemy import Column, String, Text, Integer, Boolean

class Announcement(BaseModel, TimestampMixin):
    \"\"\"Announcement model for system-wide announcements.\"\"\"
    
    # Announcement fields
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)
    priority = Column(Integer, default=0)  # Higher number = higher priority
    is_active = Column(Boolean, default=True)
    
    # Author relationship
    author_id = Column(Integer, nullable=True)

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
            'author_id': self.author_id,
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

print("Successfully modified models/announcement.py")
