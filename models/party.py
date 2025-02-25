from datetime import datetime
from models import db

class Party(db.Model):
    __tablename__ = 'parties'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_activity = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Party Settings
    settings = db.Column(db.JSON, default={
        'loot_distribution': 'equal',  # Options: equal, need, greed
        'experience_share': True,
        'auto_accept_requests': False
    })
    
    # Relationships
    members = db.relationship('PartyMember', back_populates='party')
    quests = db.relationship('PartyQuest', back_populates='party')

class PartyMember(db.Model):
    __tablename__ = 'party_members'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    role = db.Column(db.String(20))  # Optional role assignment
    
    # Relationships
    party = db.relationship('Party', back_populates='members')
    user = db.relationship('User', back_populates='party_membership')

class PartyQuest(db.Model):
    __tablename__ = 'party_quests'
    __table_args__ = {'extend_existing': True}

    
    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id'))
    quest_id = db.Column(db.Integer)  # Reference to quest system
    status = db.Column(db.String(20), default='active')
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    party = db.relationship('Party', back_populates='quests')
