from datetime import datetime
from models import db

class AIAgent(db.Model):
    __tablename__ = 'ai_agents'
    
    id = db.Column(db.Integer, primary_key=True)
    agent_type = db.Column(db.String(50), nullable=False)  # e.g., quest, gacha, gambling
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Configuration
    parameters = db.Column(db.JSON, default={})
    learning_rate = db.Column(db.Float, default=0.01)
    last_trained = db.Column(db.DateTime)

class PlayerBehavior(db.Model):
    __tablename__ = 'player_behaviors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    recorded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Behavior Data
    activity_type = db.Column(db.String(50))  # e.g., gate_hunting, gambling
    duration = db.Column(db.Integer)  # in seconds
    outcome = db.Column(db.JSON, default={})
    
    # Relationships
    user = db.relationship('User')

class AIRecommendation(db.Model):
    __tablename__ = 'ai_recommendations'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    generated_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Recommendation Details
    recommendation_type = db.Column(db.String(50))  # e.g., quest, gate, item
    details = db.Column(db.JSON, default={})
    confidence_score = db.Column(db.Float)
    
    # Relationships
    user = db.relationship('User')
