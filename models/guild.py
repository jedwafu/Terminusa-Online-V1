from datetime import datetime
from models import db

class Guild(db.Model):
    __tablename__ = 'guilds'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)
    description = db.Column(db.Text)
    country = db.Column(db.String(2), nullable=True)  # ISO 2-letter country code
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    funds = db.Column(db.Numeric(precision=18, scale=9), default=0)  # Exons
    crystals = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Guild Settings
    settings = db.Column(db.JSON, default={
        'recruitment': {
            'open': True,
            'requirements': {
                'min_level': 1,
                'min_activity': 0
            }
        },
        'tax_rate': 0.02  # 2% tax for guild-related transactions
    })
    
    # Relationships
    members = db.relationship('GuildMember', back_populates='guild')
    quests = db.relationship('GuildQuest', back_populates='guild')
    transactions = db.relationship('GuildTransaction', back_populates='guild')

class GuildMember(db.Model):
    __tablename__ = 'guild_members'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    rank = db.Column(db.String(20), default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    contribution = db.Column(db.Numeric(precision=18, scale=9), default=0)  # Exons contributed
    
    # Relationships
    guild = db.relationship('Guild', back_populates='members')
    user = db.relationship('User', back_populates='guild_membership')

class GuildQuest(db.Model):
    __tablename__ = 'guild_quests'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'))
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    status = db.Column(db.String(20), default='active')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Relationships
    guild = db.relationship('Guild', back_populates='quests')

class GuildTransaction(db.Model):
    __tablename__ = 'guild_transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    amount = db.Column(db.Numeric(precision=18, scale=9))  # Exons
    transaction_type = db.Column(db.String(20))  # deposit, withdrawal, tax, etc.
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    guild = db.relationship('Guild', back_populates='transactions')
