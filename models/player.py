from .base import BaseModel
from database import db

class PlayerCharacter(BaseModel):
    """Player character model"""
    __tablename__ = 'player_characters'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    class_id = db.Column(db.Integer, db.ForeignKey('player_classes.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job_types.id'))
    
    # Relationships
    user = db.relationship('User', back_populates='characters')
    player_class = db.relationship('PlayerClass')
    job = db.relationship('JobType')

class Player(BaseModel):
    """Player model representing a game character"""
    __tablename__ = 'players'
    
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.Integer, default=0)
    class_id = db.Column(db.Integer, db.ForeignKey('player_classes.id'))
    job_id = db.Column(db.Integer, db.ForeignKey('job_types.id'))
    
    # Relationships
    user = db.relationship('User', back_populates='characters')
    player_class = db.relationship('PlayerClass')
    job = db.relationship('JobType')

class PlayerClass(BaseModel):
    """Player class model"""
    __tablename__ = 'player_classes'
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    base_stats = db.Column(db.JSON)

class JobType(BaseModel):
    """Job type model"""
    __tablename__ = 'job_types'
    
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    requirements = db.Column(db.JSON)
