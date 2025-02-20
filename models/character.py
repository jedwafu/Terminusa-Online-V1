"""Character model definition."""

from database import db
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum
from sqlalchemy.orm import relationship
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

    def level_up(self):
        """Level up the character."""
        self.level += 1
        self.experience = 0  # Reset experience on level up
        self.max_health += 10  # Increase max health
        self.max_mana += 5  # Increase max mana
        db.session.commit()
