from app import db
from datetime import datetime
from enum import Enum

class HunterClass(Enum):
    F = "F"
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"

class BaseJob(Enum):
    FIGHTER = "Fighter"
    MAGE = "Mage"
    ASSASSIN = "Assassin"
    ARCHER = "Archer"
    HEALER = "Healer"

class HealthStatus(Enum):
    NORMAL = "normal"
    BURNED = "burned"
    POISONED = "poisoned"
    FROZEN = "frozen"
    FEARED = "feared"
    CONFUSED = "confused"
    DISMEMBERED = "dismembered"
    DECAPITATED = "decapitated"
    SHADOW = "shadow"

class PlayerCharacter(db.Model):
    """Player character model"""
    __tablename__ = 'player_characters'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), unique=True, nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    hunter_class = db.Column(db.Enum(HunterClass), default=HunterClass.F)
    base_job = db.Column(db.Enum(BaseJob), nullable=False)
    current_job = db.Column(db.String(50), nullable=False)  # Can be mixed jobs
    job_level = db.Column(db.Integer, default=1)
    job_experience = db.Column(db.BigInteger, default=0)
    
    # Base Stats
    strength = db.Column(db.Integer, default=10)
    agility = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    vitality = db.Column(db.Integer, default=10)
    wisdom = db.Column(db.Integer, default=10)
    luck = db.Column(db.Integer, default=10)
    
    # Derived Stats
    max_hp = db.Column(db.Integer, default=100)
    current_hp = db.Column(db.Integer, default=100)
    max_mp = db.Column(db.Integer, default=100)
    current_mp = db.Column(db.Integer, default=100)
    physical_attack = db.Column(db.Integer, default=10)
    magical_attack = db.Column(db.Integer, default=10)
    physical_defense = db.Column(db.Integer, default=10)
    magical_defense = db.Column(db.Integer, default=10)
    critical_chance = db.Column(db.Float, default=5.0)  # Percentage
    critical_damage = db.Column(db.Float, default=150.0)  # Percentage
    dodge_chance = db.Column(db.Float, default=5.0)  # Percentage
    hit_chance = db.Column(db.Float, default=95.0)  # Percentage
    
    # Status
    health_status = db.Column(db.Enum(HealthStatus), default=HealthStatus.NORMAL)
    status_duration = db.Column(db.DateTime, nullable=True)
    is_dead = db.Column(db.Boolean, default=False)
    last_death = db.Column(db.DateTime, nullable=True)
    
    # Progress Tracking
    gates_cleared = db.Column(db.Integer, default=0)
    gates_failed = db.Column(db.Integer, default=0)
    bosses_defeated = db.Column(db.Integer, default=0)
    quests_completed = db.Column(db.Integer, default=0)
    achievements_earned = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_login = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', backref=db.backref('character', uselist=False))
    skills = db.relationship('PlayerSkill', backref='character', lazy='dynamic')
    inventory = db.relationship('Inventory', backref='character', uselist=False)
    achievements = db.relationship('Achievement', secondary='user_achievements', backref='characters')

    def __repr__(self):
        return f"<PlayerCharacter {self.name}>"

class PlayerSkill(db.Model):
    """Player skill model"""
    __tablename__ = 'player_skills'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    skill_id = db.Column(db.Integer, db.ForeignKey('skills.id'), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    is_active = db.Column(db.Boolean, default=True)
    cooldown_ends = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PlayerSkill {self.skill_id}>"

class Skill(db.Model):
    """Skill definition model"""
    __tablename__ = 'skills'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text, nullable=False)
    required_job = db.Column(db.String(50), nullable=False)
    required_level = db.Column(db.Integer, default=1)
    mana_cost = db.Column(db.Integer, nullable=False)
    cooldown = db.Column(db.Integer, nullable=False)  # in seconds
    damage_type = db.Column(db.String(20), nullable=True)  # physical, magical, heal
    base_power = db.Column(db.Integer, nullable=True)
    scaling_stat = db.Column(db.String(20), nullable=True)  # strength, intelligence, etc.
    scaling_factor = db.Column(db.Float, nullable=True)
    status_effect = db.Column(db.Enum(HealthStatus), nullable=True)
    effect_chance = db.Column(db.Float, nullable=True)  # Percentage
    effect_duration = db.Column(db.Integer, nullable=True)  # in seconds
    is_resurrection = db.Column(db.Boolean, default=False)
    is_monarch = db.Column(db.Boolean, default=False)  # For special skills like "Arise"
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Skill {self.name}>"

class JobHistory(db.Model):
    """Job history model"""
    __tablename__ = 'job_history'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    job_name = db.Column(db.String(50), nullable=False)
    level_reached = db.Column(db.Integer, nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<JobHistory {self.job_name}>"

class JobQuest(db.Model):
    """Job quest model"""
    __tablename__ = 'job_quests'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    required_job = db.Column(db.String(50), nullable=False)
    required_level = db.Column(db.Integer, nullable=False)
    quest_type = db.Column(db.String(20), nullable=False)  # rank_up, job_change
    description = db.Column(db.Text, nullable=False)
    requirements = db.Column(db.JSON, nullable=False)  # Quest completion requirements
    rewards = db.Column(db.JSON, nullable=False)  # Quest rewards
    status = db.Column(db.String(20), default='active')  # active, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<JobQuest {self.quest_type}>"
