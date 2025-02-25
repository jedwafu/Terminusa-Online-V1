from datetime import datetime
from enum import Enum
from models import db

class QuestType(Enum):
    MAIN = 'Main'
    SIDE = 'Side'
    GUILD = 'Guild'
    DAILY = 'Daily'
    EVENT = 'Event'

class QuestStatus(Enum):
    AVAILABLE = 'Available'
    IN_PROGRESS = 'In Progress'
    COMPLETED = 'Completed'
    FAILED = 'Failed'

class Quest(db.Model):
    __tablename__ = 'quests'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quest_type = db.Column(db.Enum(QuestType), nullable=False)
    difficulty = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Requirements
    min_level = db.Column(db.Integer, default=1)
    required_items = db.Column(db.JSON, default={})
    
    # Rewards
    experience = db.Column(db.BigInteger, default=0)
    crystals = db.Column(db.BigInteger, default=0)
    items = db.Column(db.JSON, default={})
    
    # Relationships
    progress = db.relationship('QuestProgress', back_populates='quest')

class QuestProgress(db.Model):
    __tablename__ = 'quest_progress'
    
    id = db.Column(db.Integer, primary_key=True)
    quest_id = db.Column(db.Integer, db.ForeignKey('quests.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.Enum(QuestStatus), default=QuestStatus.AVAILABLE)
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    
    # Progress Tracking
    objectives = db.Column(db.JSON, default={})
    
    # Relationships
    quest = db.relationship('Quest', back_populates='progress')
    user = db.relationship('User', back_populates='quests')
