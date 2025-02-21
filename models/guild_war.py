from datetime import datetime
from typing import Dict, List, Optional
from enum import Enum

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict, MutableList

from models.base import db, BaseModel

class WarStatus(Enum):
    PENDING = 'pending'
    PREPARATION = 'preparation'
    ACTIVE = 'active'
    COMPLETED = 'completed'
    CANCELLED = 'cancelled'

class TerritoryType(Enum):
    GATE = 'gate'
    RESOURCE = 'resource'
    STRONGHOLD = 'stronghold'
    OUTPOST = 'outpost'

class TerritoryStatus(Enum):
    NEUTRAL = 'neutral'
    FRIENDLY = 'friendly'
    ENEMY = 'enemy'
    CONTESTED = 'contested'

class GuildWar(BaseModel):
    """Guild War Model"""
    __tablename__ = 'guild_wars'

    challenger_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    status = db.Column(db.String(20), nullable=False, default=WarStatus.PENDING.value)
    start_time = db.Column(db.DateTime, nullable=False)
    end_time = db.Column(db.DateTime, nullable=False)
    winner_id = db.Column(db.Integer, db.ForeignKey('guilds.id'))
    
    # Store participants as JSON {guild_id: [member_ids]}
    participants = db.Column(MutableDict.as_mutable(JSONB), default=dict)
    
    # Store scores as JSON {guild_id: score}
    scores = db.Column(MutableDict.as_mutable(JSONB), default=dict)
    
    # Store rewards as JSON
    rewards = db.Column(MutableDict.as_mutable(JSONB), default=dict)

    # Relationships
    challenger = db.relationship('Guild', foreign_keys=[challenger_id], backref='wars_initiated')
    target = db.relationship('Guild', foreign_keys=[target_id], backref='wars_targeted')
    winner = db.relationship('Guild', foreign_keys=[winner_id], backref='wars_won')
    territories = db.relationship('WarTerritory', backref='war', lazy='dynamic')
    events = db.relationship('WarEvent', backref='war', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        if not self.participants:
            self.participants = {
                str(self.challenger_id): [],
                str(self.target_id): []
            }
        if not self.scores:
            self.scores = {
                str(self.challenger_id): 0,
                str(self.target_id): 0
            }

    @property
    def is_active(self) -> bool:
        """Check if war is currently active"""
        now = datetime.utcnow()
        return (self.status == WarStatus.ACTIVE.value and
                self.start_time <= now <= self.end_time)

    def add_participant(self, guild_id: int, member_id: int) -> bool:
        """Add a participant to the war"""
        guild_key = str(guild_id)
        if guild_key not in self.participants:
            return False
            
        if member_id not in self.participants[guild_key]:
            self.participants[guild_key].append(member_id)
            return True
            
        return False

    def remove_participant(self, guild_id: int, member_id: int) -> bool:
        """Remove a participant from the war"""
        guild_key = str(guild_id)
        if guild_key not in self.participants:
            return False
            
        if member_id in self.participants[guild_key]:
            self.participants[guild_key].remove(member_id)
            return True
            
        return False

    def update_score(self, guild_id: int, points: int) -> None:
        """Update guild's war score"""
        guild_key = str(guild_id)
        if guild_key in self.scores:
            self.scores[guild_key] += points

    def to_dict(self) -> Dict:
        """Convert war to dictionary"""
        return {
            'id': self.id,
            'challenger_id': self.challenger_id,
            'target_id': self.target_id,
            'status': self.status,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'winner_id': self.winner_id,
            'participants': self.participants,
            'scores': self.scores,
            'rewards': self.rewards,
            'created_at': self.created_at.isoformat()
        }

class WarTerritory(BaseModel):
    """War Territory Model"""
    __tablename__ = 'war_territories'

    war_id = db.Column(db.Integer, db.ForeignKey('guild_wars.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(20), default=TerritoryStatus.NEUTRAL.value)
    controller_id = db.Column(db.Integer, db.ForeignKey('guilds.id'))
    position_x = db.Column(db.Float, nullable=False)
    position_y = db.Column(db.Float, nullable=False)
    
    # Store bonuses as JSON {type: value}
    bonuses = db.Column(MutableDict.as_mutable(JSONB), default=dict)
    
    # Store defense data as JSON
    defense_data = db.Column(MutableDict.as_mutable(JSONB), default=dict)

    # Relationships
    controller = db.relationship('Guild', backref='controlled_territories')

    def to_dict(self) -> Dict:
        """Convert territory to dictionary"""
        return {
            'id': self.id,
            'war_id': self.war_id,
            'name': self.name,
            'type': self.type,
            'status': self.status,
            'controller_id': self.controller_id,
            'controller_name': self.controller.name if self.controller else None,
            'position_x': self.position_x,
            'position_y': self.position_y,
            'bonuses': self.bonuses,
            'defense_data': self.defense_data
        }

class WarEvent(BaseModel):
    """War Event Model"""
    __tablename__ = 'war_events'

    war_id = db.Column(db.Integer, db.ForeignKey('guild_wars.id'), nullable=False)
    type = db.Column(db.String(50), nullable=False)
    initiator_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    target_id = db.Column(db.Integer)  # Could be territory_id or user_id depending on event type
    points = db.Column(db.Integer, default=0)
    
    # Store event details as JSON
    details = db.Column(MutableDict.as_mutable(JSONB), default=dict)

    # Relationships
    initiator = db.relationship('User', backref='war_events')

    def to_dict(self) -> Dict:
        """Convert event to dictionary"""
        return {
            'id': self.id,
            'war_id': self.war_id,
            'type': self.type,
            'initiator_id': self.initiator_id,
            'initiator_name': self.initiator.username if self.initiator else None,
            'target_id': self.target_id,
            'points': self.points,
            'details': self.details,
            'created_at': self.created_at.isoformat()
        }

class WarParticipant(BaseModel):
    """War Participant Model"""
    __tablename__ = 'war_participants'

    war_id = db.Column(db.Integer, db.ForeignKey('guild_wars.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    points_contributed = db.Column(db.Integer, default=0)
    kills = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    territories_captured = db.Column(db.Integer, default=0)
    
    # Store participant stats as JSON
    stats = db.Column(MutableDict.as_mutable(JSONB), default=dict)

    # Relationships
    war = db.relationship('GuildWar', backref='participants_data')
    user = db.relationship('User', backref='war_participations')
    guild = db.relationship('Guild', backref='war_participants')

    def to_dict(self) -> Dict:
        """Convert participant to dictionary"""
        return {
            'id': self.id,
            'war_id': self.war_id,
            'user_id': self.user_id,
            'username': self.user.username,
            'guild_id': self.guild_id,
            'points_contributed': self.points_contributed,
            'kills': self.kills,
            'deaths': self.deaths,
            'territories_captured': self.territories_captured,
            'stats': self.stats
        }
