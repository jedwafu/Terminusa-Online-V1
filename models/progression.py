from app import db
from datetime import datetime
from enum import Enum

class QuestType(Enum):
    MAIN = "main"
    DAILY = "daily"
    WEEKLY = "weekly"
    ACHIEVEMENT = "achievement"
    JOB = "job"
    GUILD = "guild"
    EVENT = "event"

class QuestStatus(Enum):
    AVAILABLE = "available"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class Achievement(db.Model):
    """Achievement model"""
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    category = db.Column(db.String(50), nullable=False)  # combat, exploration, social, etc.
    hidden = db.Column(db.Boolean, default=False)
    
    # Requirements
    requirements = db.Column(db.JSON, nullable=False)  # Achievement conditions
    progress_tracking = db.Column(db.JSON, nullable=False)  # How to track progress
    
    # Rewards
    crystal_reward = db.Column(db.Integer, default=0)
    stat_rewards = db.Column(db.JSON, nullable=True)  # Permanent stat bonuses
    title_reward = db.Column(db.String(50), nullable=True)
    
    # AI Configuration
    ai_weight = db.Column(db.Float, default=1.0)  # Influences AI decision making
    activity_requirements = db.Column(db.JSON, nullable=True)  # Required player activities
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Achievement {self.name}>"

class Quest(db.Model):
    """Quest model"""
    __tablename__ = 'quests'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    quest_type = db.Column(db.Enum(QuestType), nullable=False)
    level_requirement = db.Column(db.Integer, default=1)
    hunter_class_requirement = db.Column(db.String(20), nullable=True)
    job_requirement = db.Column(db.String(50), nullable=True)
    
    # Quest Chain
    prerequisite_quest_id = db.Column(db.Integer, db.ForeignKey('quests.id'), nullable=True)
    next_quest_id = db.Column(db.Integer, db.ForeignKey('quests.id'), nullable=True)
    
    # Requirements
    objectives = db.Column(db.JSON, nullable=False)  # Quest objectives
    time_limit = db.Column(db.Integer, nullable=True)  # In seconds, null for no limit
    
    # Rewards
    crystal_reward = db.Column(db.Integer, default=0)
    exon_reward = db.Column(db.Integer, default=0)
    exp_reward = db.Column(db.Integer, default=0)
    item_rewards = db.Column(db.JSON, nullable=True)  # List of item IDs and quantities
    
    # AI Configuration
    ai_weight = db.Column(db.Float, default=1.0)
    activity_requirements = db.Column(db.JSON, nullable=True)
    player_preference_weight = db.Column(db.JSON, nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Quest {self.name}>"

class PlayerQuest(db.Model):
    """Player quest progress model"""
    __tablename__ = 'player_quests'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quests.id'), nullable=False)
    status = db.Column(db.Enum(QuestStatus), default=QuestStatus.AVAILABLE)
    progress = db.Column(db.JSON, nullable=False)  # Current progress on objectives
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    quest = db.relationship('Quest')

    def __repr__(self):
        return f"<PlayerQuest {self.quest_id}>"

class PlayerAchievement(db.Model):
    """Player achievement progress model"""
    __tablename__ = 'player_achievements'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    achievement_id = db.Column(db.Integer, db.ForeignKey('achievements.id'), nullable=False)
    progress = db.Column(db.JSON, nullable=False)  # Current progress
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime, nullable=True)
    rewards_claimed = db.Column(db.Boolean, default=False)
    
    # Relationships
    achievement = db.relationship('Achievement')

    def __repr__(self):
        return f"<PlayerAchievement {self.achievement_id}>"

class QuestLog(db.Model):
    """Quest activity log"""
    __tablename__ = 'quest_logs'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    quest_id = db.Column(db.Integer, db.ForeignKey('quests.id'), nullable=False)
    action = db.Column(db.String(50), nullable=False)
    details = db.Column(db.JSON, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<QuestLog {self.action}>"

class QuestBank(db.Model):
    """AI-powered quest generation configuration"""
    __tablename__ = 'quest_bank'

    id = db.Column(db.Integer, primary_key=True)
    template_name = db.Column(db.String(100), nullable=False)
    quest_type = db.Column(db.Enum(QuestType), nullable=False)
    template = db.Column(db.JSON, nullable=False)  # Quest template structure
    variables = db.Column(db.JSON, nullable=False)  # Dynamic variables
    conditions = db.Column(db.JSON, nullable=False)  # When to generate this quest
    
    # AI Configuration
    activity_weights = db.Column(db.JSON, nullable=False)  # Weight by activity type
    player_type_weights = db.Column(db.JSON, nullable=False)  # Weight by player type
    difficulty_curve = db.Column(db.JSON, nullable=False)  # How difficulty scales
    reward_curve = db.Column(db.JSON, nullable=False)  # How rewards scale
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<QuestBank {self.template_name}>"

class ReferralReward(db.Model):
    """Referral system rewards"""
    __tablename__ = 'referral_rewards'

    id = db.Column(db.Integer, primary_key=True)
    referrer_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    referred_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    milestone = db.Column(db.Integer, nullable=False)  # Multiple of 100
    crystal_reward = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, completed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<ReferralReward {self.milestone}>"

# Association Tables
user_achievements = db.Table('user_achievements',
    db.Column('character_id', db.Integer, db.ForeignKey('player_characters.id'), primary_key=True),
    db.Column('achievement_id', db.Integer, db.ForeignKey('achievements.id'), primary_key=True),
    db.Column('completed_at', db.DateTime, nullable=True)
)
