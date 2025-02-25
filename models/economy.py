from datetime import datetime
from models import db

class GamblingRecord(db.Model):
    __tablename__ = 'gambling_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    game_type = db.Column(db.String(50))  # e.g., coin_flip
    bet_amount = db.Column(db.BigInteger)  # Crystals
    outcome = db.Column(db.JSON, default={})
    
    # Relationships
    user = db.relationship('User')

class ReferralRecord(db.Model):
    __tablename__ = 'referral_records'
    
    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    referred_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Reward Details
    reward_crystals = db.Column(db.BigInteger, default=0)
    reward_exons = db.Column(db.Numeric(precision=18, scale=9), default=0)
    
    # Relationships
    referrer = db.relationship('User', foreign_keys=[referrer_id])
    referred = db.relationship('User', foreign_keys=[referred_id])

class LoyaltyRecord(db.Model):
    __tablename__ = 'loyalty_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    period_start = db.Column(db.DateTime)
    period_end = db.Column(db.DateTime)
    total_held = db.Column(db.Numeric(precision=18, scale=9))  # Exons
    total_crystals = db.Column(db.BigInteger)
    reward_crystals = db.Column(db.BigInteger, default=0)
    
    # Relationships
    user = db.relationship('User')
