from app import db
from datetime import datetime
from enum import Enum

class GuildRank(Enum):
    MASTER = "master"
    DEPUTY = "deputy"
    ELDER = "elder"
    VETERAN = "veteran"
    MEMBER = "member"
    RECRUIT = "recruit"

class Guild(db.Model):
    """Guild model"""
    __tablename__ = 'guilds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=True)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    crystal_balance = db.Column(db.BigInteger, default=0)
    exon_balance = db.Column(db.BigInteger, default=0)
    max_members = db.Column(db.Integer, default=50)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Guild Stats
    total_gates_cleared = db.Column(db.Integer, default=0)
    total_quests_completed = db.Column(db.Integer, default=0)
    total_boss_kills = db.Column(db.Integer, default=0)
    weekly_activity = db.Column(db.Integer, default=0)
    
    # Relationships
    members = db.relationship('GuildMember', backref='guild', lazy='dynamic')
    quests = db.relationship('GuildQuest', backref='guild', lazy='dynamic')
    logs = db.relationship('GuildLog', backref='guild', lazy='dynamic')

    def __repr__(self):
        return f"<Guild {self.name}>"

class GuildMember(db.Model):
    """Guild member model"""
    __tablename__ = 'guild_members'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    rank = db.Column(db.Enum(GuildRank), default=GuildRank.RECRUIT)
    contribution_points = db.Column(db.Integer, default=0)
    weekly_contribution = db.Column(db.Integer, default=0)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Member Stats
    gates_cleared = db.Column(db.Integer, default=0)
    quests_completed = db.Column(db.Integer, default=0)
    boss_kills = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<GuildMember {self.character_id}>"

class GuildQuest(db.Model):
    """Guild quest model"""
    __tablename__ = 'guild_quests'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.JSON, nullable=False)  # Quest completion requirements
    rewards = db.Column(db.JSON, nullable=False)  # Quest rewards
    status = db.Column(db.String(20), default='active')  # active, completed, failed
    start_time = db.Column(db.DateTime, default=datetime.utcnow)
    end_time = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Quest Progress
    current_progress = db.Column(db.JSON, nullable=False, default=dict)
    participating_members = db.Column(db.JSON, nullable=False, default=list)

    def __repr__(self):
        return f"<GuildQuest {self.name}>"

class GuildLog(db.Model):
    """Guild activity log"""
    __tablename__ = 'guild_logs'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<GuildLog {self.action}>"

class Party(db.Model):
    """Party model"""
    __tablename__ = 'parties'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=True)
    leader_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    status = db.Column(db.String(20), default='forming')  # forming, active, disbanded
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    disbanded_at = db.Column(db.DateTime, nullable=True)
    
    # Party Stats
    average_level = db.Column(db.Float, default=0)
    total_luck = db.Column(db.Integer, default=0)
    
    # Current Activity
    current_gate_id = db.Column(db.Integer, db.ForeignKey('gates.id'), nullable=True)
    gate_entered_at = db.Column(db.DateTime, nullable=True)
    
    # Relationships
    members = db.relationship('PartyMember', backref='party', lazy='dynamic')
    invitations = db.relationship('PartyInvitation', backref='party', lazy='dynamic')

    def __repr__(self):
        return f"<Party {self.id}>"

class PartyMember(db.Model):
    """Party member model"""
    __tablename__ = 'party_members'

    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    left_at = db.Column(db.DateTime, nullable=True)
    
    # Combat Stats
    damage_dealt = db.Column(db.BigInteger, default=0)
    damage_taken = db.Column(db.BigInteger, default=0)
    healing_done = db.Column(db.BigInteger, default=0)
    deaths = db.Column(db.Integer, default=0)
    
    # Contribution
    contribution_score = db.Column(db.Float, default=0)
    loot_priority = db.Column(db.Integer, default=0)

    def __repr__(self):
        return f"<PartyMember {self.character_id}>"

class PartyInvitation(db.Model):
    """Party invitation model"""
    __tablename__ = 'party_invitations'

    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id'), nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    invitee_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, nullable=False)
    responded_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<PartyInvitation {self.id}>"

class PartyLog(db.Model):
    """Party activity log"""
    __tablename__ = 'party_logs'

    id = db.Column(db.Integer, primary_key=True)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=True)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<PartyLog {self.action}>"
