from app import db
from datetime import datetime
from enum import Enum

class GateGrade(Enum):
    F = "F"
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    MONARCH = "MONARCH"

class MagicBeastType(Enum):
    NORMAL = "normal"
    ELITE = "elite"
    BOSS = "boss"
    MASTER = "master"
    MONARCH = "monarch"

class Gate(db.Model):
    """Gate (dungeon) model"""
    __tablename__ = 'gates'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    grade = db.Column(db.Enum(GateGrade), nullable=False)
    level_requirement = db.Column(db.Integer, nullable=False)
    rank_requirement = db.Column(db.Enum(GateGrade), nullable=False)
    min_players = db.Column(db.Integer, default=1)
    max_players = db.Column(db.Integer, default=1)
    
    # Rewards
    base_crystal_reward = db.Column(db.Integer, nullable=False)
    base_exp_reward = db.Column(db.Integer, nullable=False)
    loot_table = db.Column(db.JSON, nullable=False)  # Possible item drops and rates
    
    # Difficulty factors
    monster_level_bonus = db.Column(db.Float, default=1.0)
    monster_stat_bonus = db.Column(db.Float, default=1.0)
    monster_count_bonus = db.Column(db.Float, default=1.0)
    time_limit = db.Column(db.Integer, nullable=True)  # in seconds, null for no limit
    
    # AI Configuration
    ai_difficulty_adjustment = db.Column(db.Float, default=1.0)
    ai_behavior_pattern = db.Column(db.String(50), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    magic_beasts = db.relationship('MagicBeast', secondary='gate_magic_beasts', backref='gates')
    sessions = db.relationship('GateSession', backref='gate', lazy='dynamic')

    def __repr__(self):
        return f"<Gate {self.name} ({self.grade.value})>"

class MagicBeast(db.Model):
    """Magic Beast model"""
    __tablename__ = 'magic_beasts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    beast_type = db.Column(db.Enum(MagicBeastType), nullable=False)
    level = db.Column(db.Integer, nullable=False)
    
    # Base Stats
    hp = db.Column(db.Integer, nullable=False)
    mp = db.Column(db.Integer, nullable=False)
    physical_attack = db.Column(db.Integer, nullable=False)
    magical_attack = db.Column(db.Integer, nullable=False)
    physical_defense = db.Column(db.Integer, nullable=False)
    magical_defense = db.Column(db.Integer, nullable=False)
    speed = db.Column(db.Integer, nullable=False)
    
    # Combat Properties
    skills = db.Column(db.JSON, nullable=False)  # List of skill IDs
    loot_table = db.Column(db.JSON, nullable=False)  # Possible drops and rates
    crystal_value = db.Column(db.Integer, nullable=False)
    exp_value = db.Column(db.Integer, nullable=False)
    
    # AI Behavior
    ai_behavior_id = db.Column(db.Integer, db.ForeignKey('ai_behaviors.id'), nullable=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<MagicBeast {self.name}>"

class GateSession(db.Model):
    """Gate session model for tracking active and completed gate runs"""
    __tablename__ = 'gate_sessions'

    id = db.Column(db.Integer, primary_key=True)
    gate_id = db.Column(db.Integer, db.ForeignKey('gates.id'), nullable=False)
    party_id = db.Column(db.Integer, db.ForeignKey('parties.id'), nullable=True)  # Null for solo
    status = db.Column(db.String(20), default='active')  # active, completed, failed
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    time_taken = db.Column(db.Integer, nullable=True)  # in seconds
    
    # Session Results
    total_crystal_reward = db.Column(db.Integer, nullable=True)
    total_exp_reward = db.Column(db.Integer, nullable=True)
    dropped_items = db.Column(db.JSON, nullable=True)  # Items dropped during session
    player_deaths = db.Column(db.JSON, nullable=True)  # Player death records
    combat_log = db.Column(db.JSON, nullable=True)  # Detailed combat log
    
    # Performance Metrics
    damage_dealt = db.Column(db.JSON, nullable=True)  # Per player damage stats
    damage_taken = db.Column(db.JSON, nullable=True)  # Per player damage taken
    healing_done = db.Column(db.JSON, nullable=True)  # Per player healing stats
    kills = db.Column(db.JSON, nullable=True)  # Per player kill counts

    def __repr__(self):
        return f"<GateSession {self.id}>"

class AIBehavior(db.Model):
    """AI behavior patterns for magic beasts"""
    __tablename__ = 'ai_behaviors'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)
    description = db.Column(db.Text, nullable=False)
    behavior_type = db.Column(db.String(20), nullable=False)  # aggressive, defensive, balanced
    skill_priorities = db.Column(db.JSON, nullable=False)  # Skill usage priorities
    target_selection = db.Column(db.JSON, nullable=False)  # Target selection rules
    hp_thresholds = db.Column(db.JSON, nullable=False)  # Behavior changes at HP %
    mp_thresholds = db.Column(db.JSON, nullable=False)  # Behavior changes at MP %
    
    # Advanced AI Settings
    learning_rate = db.Column(db.Float, default=0.1)
    adaptation_factor = db.Column(db.Float, default=0.1)
    memory_length = db.Column(db.Integer, default=10)  # Number of rounds to remember
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    magic_beasts = db.relationship('MagicBeast', backref='ai_behavior')

    def __repr__(self):
        return f"<AIBehavior {self.name}>"

# Association Tables
gate_magic_beasts = db.Table('gate_magic_beasts',
    db.Column('gate_id', db.Integer, db.ForeignKey('gates.id'), primary_key=True),
    db.Column('magic_beast_id', db.Integer, db.ForeignKey('magic_beasts.id'), primary_key=True),
    db.Column('spawn_rate', db.Float, nullable=False),  # Percentage chance to spawn
    db.Column('min_count', db.Integer, nullable=False),  # Minimum number per gate
    db.Column('max_count', db.Integer, nullable=False)  # Maximum number per gate
)
