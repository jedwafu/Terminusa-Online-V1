"""
Guild model for Terminusa Online
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from models import db

class Guild(db.Model):
    __tablename__ = 'guilds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(500))
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id', deferrable=True, initially='DEFERRED'), nullable=False)
    
    # Guild stats
    level = db.Column(db.Integer)
    experience = db.Column(db.BigInteger)
    reputation = db.Column(db.Integer)
    
    # Currency balances
    crystal_balance = db.Column(db.BigInteger)
    exon_balance = db.Column(db.Numeric(18, 9))
    
    # Tax rates
    crystal_tax_rate = db.Column(db.Integer)
    exon_tax_rate = db.Column(db.Integer)
    
    # Member limits
    max_members = db.Column(db.Integer)
    max_quests = db.Column(db.Integer)
    
    # Member stats
    total_members = db.Column(db.Integer)
    active_members = db.Column(db.Integer)
    
    # Achievement stats
    total_gates_cleared = db.Column(db.Integer)
    total_quests_completed = db.Column(db.Integer)
    
    # Guild settings
    recruitment_status = db.Column(db.String(20))
    min_level_requirement = db.Column(db.Integer)
    settings = db.Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name: str, leader_id: int, **kwargs):
        self.name = name
        self.leader_id = leader_id
        self.level = kwargs.get('level', 1)
        self.experience = kwargs.get('experience', 0)
        self.reputation = kwargs.get('reputation', 0)
        self.crystal_balance = kwargs.get('crystal_balance', 0)
        self.exon_balance = kwargs.get('exon_balance', 0)
        self.crystal_tax_rate = kwargs.get('crystal_tax_rate', 0)
        self.exon_tax_rate = kwargs.get('exon_tax_rate', 0)
        self.max_members = kwargs.get('max_members', 50)
        self.max_quests = kwargs.get('max_quests', 5)
        self.total_members = kwargs.get('total_members', 1)
        self.active_members = kwargs.get('active_members', 1)
        self.total_gates_cleared = kwargs.get('total_gates_cleared', 0)
        self.total_quests_completed = kwargs.get('total_quests_completed', 0)
        self.recruitment_status = kwargs.get('recruitment_status', 'open')
        self.min_level_requirement = kwargs.get('min_level_requirement', 1)
        self.settings = kwargs.get('settings', {})

    def to_dict(self) -> dict:
        """Convert guild to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'leader_id': self.leader_id,
            'level': self.level,
            'experience': self.experience,
            'reputation': self.reputation,
            'crystal_balance': self.crystal_balance,
            'exon_balance': float(self.exon_balance) if self.exon_balance else 0,
            'crystal_tax_rate': self.crystal_tax_rate,
            'exon_tax_rate': self.exon_tax_rate,
            'max_members': self.max_members,
            'max_quests': self.max_quests,
            'total_members': self.total_members,
            'active_members': self.active_members,
            'total_gates_cleared': self.total_gates_cleared,
            'total_quests_completed': self.total_quests_completed,
            'recruitment_status': self.recruitment_status,
            'min_level_requirement': self.min_level_requirement,
            'settings': self.settings,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }

class GuildMember(db.Model):
    __tablename__ = 'guild_members'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id', deferrable=True, initially='DEFERRED'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', deferrable=True, initially='DEFERRED'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    contribution_points = db.Column(db.Integer, default=0)
    weekly_contribution = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    def __init__(self, guild_id: int, user_id: int, role: str = 'member'):
        self.guild_id = guild_id
        self.user_id = user_id
        self.role = role

    def to_dict(self) -> dict:
        """Convert guild member to dictionary"""
        return {
            'id': self.id,
            'guild_id': self.guild_id,
            'user_id': self.user_id,
            'role': self.role,
            'joined_at': self.joined_at.isoformat() if self.joined_at else None,
            'contribution_points': self.contribution_points,
            'weekly_contribution': self.weekly_contribution,
            'last_active': self.last_active.isoformat() if self.last_active else None
        }

class GuildQuest(db.Model):
    __tablename__ = 'guild_quests'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id', deferrable=True, initially='DEFERRED'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    difficulty = db.Column(db.String(20))
    reward_type = db.Column(db.String(20))
    reward_amount = db.Column(db.Integer)
    required_members = db.Column(db.Integer)
    current_members = db.Column(db.Integer, default=0)
    status = db.Column(db.String(20), default='active')
    progress = db.Column(db.Integer, default=0)
    deadline = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)

    def __init__(self, guild_id: int, name: str, **kwargs):
        self.guild_id = guild_id
        self.name = name
        self.description = kwargs.get('description')
        self.difficulty = kwargs.get('difficulty', 'normal')
        self.reward_type = kwargs.get('reward_type', 'crystals')
        self.reward_amount = kwargs.get('reward_amount', 0)
        self.required_members = kwargs.get('required_members', 1)
        self.deadline = kwargs.get('deadline')

    def to_dict(self) -> dict:
        """Convert guild quest to dictionary"""
        return {
            'id': self.id,
            'guild_id': self.guild_id,
            'name': self.name,
            'description': self.description,
            'difficulty': self.difficulty,
            'reward_type': self.reward_type,
            'reward_amount': self.reward_amount,
            'required_members': self.required_members,
            'current_members': self.current_members,
            'status': self.status,
            'progress': self.progress,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
