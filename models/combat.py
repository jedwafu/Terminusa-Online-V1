from datetime import datetime
from enum import Enum
from models import db

class CombatType(Enum):
    SOLO = 'Solo'
    PARTY = 'Party'

class CombatStatus(Enum):
    PREPARING = 'Preparing'
    IN_PROGRESS = 'In Progress'
    COMPLETED = 'Completed'
    FAILED = 'Failed'

class CombatResult(db.Model):
    __tablename__ = 'combat_results'
    
    id = db.Column(db.Integer, primary_key=True)
    combat_type = db.Column(db.Enum(CombatType), nullable=False)
    gate_id = db.Column(db.Integer)  # Reference to gate system
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)
    status = db.Column(db.Enum(CombatStatus), default=CombatStatus.PREPARING)
    
    # Participants
    participants = db.Column(db.JSON, default=[])
    
    # Results
    experience_gained = db.Column(db.BigInteger, default=0)
    crystals_gained = db.Column(db.BigInteger, default=0)
    items_gained = db.Column(db.JSON, default={})
    
    # Damage Tracking
    damage_dealt = db.Column(db.JSON, default={})
    damage_taken = db.Column(db.JSON, default={})
    
    # Relationships
    logs = db.relationship('CombatLog', back_populates='combat')

class CombatLog(db.Model):
    __tablename__ = 'combat_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    combat_id = db.Column(db.Integer, db.ForeignKey('combat_results.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    message = db.Column(db.Text)
    
    # Relationships
    combat = db.relationship('CombatResult', back_populates='logs')
