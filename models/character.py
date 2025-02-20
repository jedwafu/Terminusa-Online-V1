from database import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Table
import enum

class HunterClass(enum.Enum):
    NOVICE = "Novice"
    FIGHTER = "Fighter"
    RANGER = "Ranger"
    MAGE = "Mage"
    TANK = "Tank"
    HEALER = "Healer"
    ASSASSIN = "Assassin"
    SUMMONER = "Summoner"

class BaseJob(enum.Enum):
    NONE = "None"
    WARRIOR = "Warrior"
    ARCHER = "Archer"
    WIZARD = "Wizard"
    KNIGHT = "Knight"
    PRIEST = "Priest"
    ROGUE = "Rogue"
    TAMER = "Tamer"

class HealthStatus(enum.Enum):
    HEALTHY = "Healthy"
    INJURED = "Injured"
    CRITICAL = "Critical"
    EXHAUSTED = "Exhausted"
    RECOVERING = "Recovering"

class PlayerCharacter(db.Model):
    __tablename__ = 'player_characters'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    hunter_class = Column(Enum(HunterClass), default=HunterClass.NOVICE)
    base_job = Column(Enum(BaseJob), default=BaseJob.NONE)
    health = Column(Integer, default=100)
    max_health = Column(Integer, default=100)
    mana = Column(Integer, default=100)
    max_mana = Column(Integer, default=100)
    strength = Column(Integer, default=10)
    agility = Column(Integer, default=10)
    intelligence = Column(Integer, default=10)
    vitality = Column(Integer, default=10)
    status = Column(Enum(HealthStatus), default=HealthStatus.HEALTHY)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='characters')
    skills = relationship('PlayerSkill', back_populates='character')
    job_history = relationship('JobHistory', back_populates='character')
    quests = relationship('JobQuest', back_populates='character')

    def __repr__(self):
        return f'<PlayerCharacter {self.name} (Level {self.level} {self.hunter_class.value})>'

class Skill(db.Model):
    __tablename__ = 'skills'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    hunter_class = Column(Enum(HunterClass), nullable=False)
    base_job = Column(Enum(BaseJob), nullable=False)
    level_requirement = Column(Integer, default=1)
    mana_cost = Column(Integer, default=0)
    cooldown = Column(Integer, default=0)
    damage = Column(Integer, default=0)
    healing = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    player_skills = relationship('PlayerSkill', back_populates='skill')

    def __repr__(self):
        return f'<Skill {self.name} ({self.hunter_class.value})>'

class PlayerSkill(db.Model):
    __tablename__ = 'player_skills'

    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('player_characters.id'), nullable=False)
    skill_id = Column(Integer, ForeignKey('skills.id'), nullable=False)
    level = Column(Integer, default=1)
    experience = Column(Integer, default=0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    character = relationship('PlayerCharacter', back_populates='skills')
    skill = relationship('Skill', back_populates='player_skills')

    def __repr__(self):
        return f'<PlayerSkill {self.skill.name} (Level {self.level})>'

class JobHistory(db.Model):
    __tablename__ = 'job_history'

    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('player_characters.id'), nullable=False)
    job = Column(Enum(BaseJob), nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime)
    level_reached = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    character = relationship('PlayerCharacter', back_populates='job_history')

    def __repr__(self):
        return f'<JobHistory {self.job.value} (Level {self.level_reached})>'

class JobQuest(db.Model):
    __tablename__ = 'job_quests'

    id = Column(Integer, primary_key=True)
    character_id = Column(Integer, ForeignKey('player_characters.id'), nullable=False)
    job = Column(Enum(BaseJob), nullable=False)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    level_requirement = Column(Integer, default=1)
    reward_experience = Column(Integer, default=0)
    reward_items = Column(String(500))  # JSON string of rewards
    status = Column(String(20), default='active')  # active, completed, failed
    start_date = Column(DateTime, default=datetime.utcnow)
    completion_date = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    character = relationship('PlayerCharacter', back_populates='quests')

    def __repr__(self):
        return f'<JobQuest {self.name} ({self.status})>'
