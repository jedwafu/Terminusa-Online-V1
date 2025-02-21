from datetime import datetime
from typing import Dict, List, Optional
from decimal import Decimal
from enum import Enum

from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.ext.mutable import MutableDict

from models.base import db, BaseModel

class GuildRank(Enum):
    RECRUIT = 'recruit'
    MEMBER = 'member'
    VETERAN = 'veteran'
    OFFICER = 'officer'
    LEADER = 'leader'

class QuestDifficulty(Enum):
    NORMAL = 'normal'
    HARD = 'hard'
    EXTREME = 'extreme'

class QuestStatus(Enum):
    ACTIVE = 'active'
    COMPLETED = 'completed'
    FAILED = 'failed'

class Guild(BaseModel):
    """Guild Model"""
    __tablename__ = 'guilds'

    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    crystal_balance = db.Column(db.Numeric(20, 2), default=0)
    exon_balance = db.Column(db.Numeric(20, 8), default=0)
    crystal_tax_rate = db.Column(db.Integer, default=10)  # Percentage
    exon_tax_rate = db.Column(db.Integer, default=10)    # Percentage
    max_members = db.Column(db.Integer, default=50)
    recruitment_status = db.Column(db.String(20), default='open')
    emblem = db.Column(db.String(255))
    min_level_requirement = db.Column(db.Integer, default=1)
    total_gates_cleared = db.Column(db.Integer, default=0)

    # Settings stored as JSON
    settings = db.Column(MutableDict.as_mutable(JSONB), default=dict)
    officer_permissions = db.Column(MutableDict.as_mutable(JSONB), default=dict)
    veteran_permissions = db.Column(MutableDict.as_mutable(JSONB), default=dict)
    quest_settings = db.Column(MutableDict.as_mutable(JSONB), default=dict)
    treasury_settings = db.Column(MutableDict.as_mutable(JSONB), default=dict)

    # Relationships
    leader = db.relationship('User', foreign_keys=[leader_id], backref='led_guild')
    members = db.relationship('GuildMember', backref='guild', lazy='dynamic')
    quests = db.relationship('GuildQuest', backref='guild', lazy='dynamic')
    transactions = db.relationship('GuildTransaction', backref='guild', lazy='dynamic')
    achievements = db.relationship('GuildAchievement', backref='guild', lazy='dynamic')

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Initialize default settings
        if not self.settings:
            self.settings = {
                'auto_accept_quests': False,
                'quest_difficulty': 'normal',
                'officers_can_invite': True,
                'officers_can_kick': True,
                'veterans_can_invite': False
            }
        if not self.officer_permissions:
            self.officer_permissions = {
                'invite': True,
                'kick': True,
                'manage_quests': True
            }
        if not self.veteran_permissions:
            self.veteran_permissions = {
                'invite': False,
                'start_quests': True
            }
        if not self.quest_settings:
            self.quest_settings = {
                'auto_accept': False,
                'require_approval': True
            }
        if not self.treasury_settings:
            self.treasury_settings = {
                'officers_withdraw': False
            }

    @property
    def active_members(self) -> List['GuildMember']:
        """Get list of active guild members"""
        return self.members.filter_by(active=True).all()

    @property
    def online_members(self) -> List['GuildMember']:
        """Get list of online guild members"""
        return [m for m in self.active_members if m.user.is_online]

    @property
    def average_level(self) -> float:
        """Calculate average level of guild members"""
        members = self.active_members
        if not members:
            return 0
        return sum(m.user.level for m in members) / len(members)

    def to_dict(self) -> Dict:
        """Convert guild to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'leader_id': self.leader_id,
            'level': self.level,
            'experience': self.experience,
            'crystal_balance': str(self.crystal_balance),
            'exon_balance': str(self.exon_balance),
            'crystal_tax_rate': self.crystal_tax_rate,
            'exon_tax_rate': self.exon_tax_rate,
            'max_members': self.max_members,
            'recruitment_status': self.recruitment_status,
            'emblem': self.emblem,
            'min_level_requirement': self.min_level_requirement,
            'total_gates_cleared': self.total_gates_cleared,
            'member_count': self.members.count(),
            'settings': self.settings,
            'created_at': self.created_at.isoformat()
        }

class GuildMember(BaseModel):
    """Guild Member Model"""
    __tablename__ = 'guild_members'

    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    rank = db.Column(db.String(20), nullable=False, default='recruit')
    joined_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    active = db.Column(db.Boolean, default=True)
    contribution_points = db.Column(db.Integer, default=0)
    quest_participation = db.Column(db.Integer, default=0)
    gates_cleared = db.Column(db.Integer, default=0)

    def to_dict(self) -> Dict:
        """Convert guild member to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'guild_id': self.guild_id,
            'rank': self.rank,
            'joined_at': self.joined_at.isoformat(),
            'active': self.active,
            'contribution_points': self.contribution_points,
            'quest_participation': self.quest_participation,
            'gates_cleared': self.gates_cleared
        }

class GuildQuest(BaseModel):
    """Guild Quest Model"""
    __tablename__ = 'guild_quests'

    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20), nullable=False, default='normal')
    status = db.Column(db.String(20), nullable=False, default='active')
    requirements = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    rewards = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    progress = db.Column(db.Integer, default=0)
    target = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    participants = db.Column(MutableDict.as_mutable(JSONB), default=dict)

    def to_dict(self) -> Dict:
        """Convert guild quest to dictionary"""
        return {
            'id': self.id,
            'guild_id': self.guild_id,
            'title': self.title,
            'description': self.description,
            'difficulty': self.difficulty,
            'status': self.status,
            'requirements': self.requirements,
            'rewards': self.rewards,
            'progress': self.progress,
            'target': self.target,
            'started_at': self.started_at.isoformat(),
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'completed_by': self.completed_by,
            'participants': self.participants
        }

class GuildTransaction(BaseModel):
    """Guild Transaction Model"""
    __tablename__ = 'guild_transactions'

    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    transaction_type = db.Column(db.String(50), nullable=False)
    crystal_amount = db.Column(db.Numeric(20, 2), default=0)
    exon_amount = db.Column(db.Numeric(20, 8), default=0)
    description = db.Column(db.Text)
    initiated_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    processed_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    def to_dict(self) -> Dict:
        """Convert guild transaction to dictionary"""
        return {
            'id': self.id,
            'guild_id': self.guild_id,
            'transaction_type': self.transaction_type,
            'crystal_amount': str(self.crystal_amount),
            'exon_amount': str(self.exon_amount),
            'description': self.description,
            'initiated_by': self.initiated_by,
            'processed_at': self.processed_at.isoformat()
        }

class GuildAchievement(BaseModel):
    """Guild Achievement Model"""
    __tablename__ = 'guild_achievements'

    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    requirements = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    rewards = db.Column(MutableDict.as_mutable(JSONB), nullable=False)
    progress = db.Column(db.Integer, default=0)
    target = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

    def to_dict(self) -> Dict:
        """Convert guild achievement to dictionary"""
        return {
            'id': self.id,
            'guild_id': self.guild_id,
            'name': self.name,
            'description': self.description,
            'requirements': self.requirements,
            'rewards': self.rewards,
            'progress': self.progress,
            'target': self.target,
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
