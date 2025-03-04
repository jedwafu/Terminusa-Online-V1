"""
Job models for Terminusa Online
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from models import db

class Job(db.Model):
    __tablename__ = 'jobs'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=True)
    description = db.Column(db.Text)
    
    # Job Requirements
    level_requirement = db.Column(db.Integer, default=1)
    prerequisite_job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'))
    
    # Job Stats
    base_stats = db.Column(JSONB, default={})
    stat_growth = db.Column(JSONB, default={})
    
    # Job Skills
    available_skills = db.Column(JSONB, default=[])
    skill_tree = db.Column(JSONB, default={})
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    quests = db.relationship('JobQuest', backref='job', lazy='dynamic')
    prerequisite_for = db.relationship(
        'Job',
        backref=db.backref('prerequisite_job', remote_side=[id]),
        uselist=True
    )

    def __init__(self, name: str, description: str = None, level_requirement: int = 1):
        self.name = name
        self.description = description
        self.level_requirement = level_requirement

    def to_dict(self) -> dict:
        """Convert job data to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'level_requirement': self.level_requirement,
            'prerequisite_job_id': self.prerequisite_job_id,
            'base_stats': self.base_stats,
            'stat_growth': self.stat_growth,
            'available_skills': self.available_skills,
            'skill_tree': self.skill_tree,
            'timestamps': {
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat()
            }
        }

class JobQuest(db.Model):
    __tablename__ = 'job_quests'

    id = db.Column(db.Integer, primary_key=True)
    job_id = db.Column(db.Integer, db.ForeignKey('jobs.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Quest Requirements
    level_requirement = db.Column(db.Integer, default=1)
    prerequisites = db.Column(JSONB, default=[])  # List of prerequisite quest IDs
    
    # Quest Objectives
    objectives = db.Column(JSONB, default={})
    required_items = db.Column(JSONB, default={})
    
    # Quest Rewards
    experience_reward = db.Column(db.Integer, default=0)
    crystal_reward = db.Column(db.Integer, default=0)
    item_rewards = db.Column(JSONB, default={})
    skill_rewards = db.Column(JSONB, default=[])
    
    # Quest Status
    is_repeatable = db.Column(db.Boolean, default=False)
    cooldown_hours = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, job_id: int, name: str, description: str = None):
        self.job_id = job_id
        self.name = name
        self.description = description

    def to_dict(self) -> dict:
        """Convert job quest data to dictionary"""
        return {
            'id': self.id,
            'job_id': self.job_id,
            'name': self.name,
            'description': self.description,
            'level_requirement': self.level_requirement,
            'prerequisites': self.prerequisites,
            'objectives': self.objectives,
            'required_items': self.required_items,
            'rewards': {
                'experience': self.experience_reward,
                'crystals': self.crystal_reward,
                'items': self.item_rewards,
                'skills': self.skill_rewards
            },
            'is_repeatable': self.is_repeatable,
            'cooldown_hours': self.cooldown_hours,
            'timestamps': {
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat()
            }
        }

    @staticmethod
    def get_available_quests(job_id: int, player_level: int) -> list['JobQuest']:
        """Get all available quests for a job and player level"""
        return JobQuest.query.filter(
            JobQuest.job_id == job_id,
            JobQuest.level_requirement <= player_level
        ).all()
