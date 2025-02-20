from database import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Table
import enum

# Association table for gate-magic_beast relationship
gate_magic_beasts = Table(
    'gate_magic_beasts',
    db.Model.metadata,
    Column('gate_id', Integer, ForeignKey('gates.id'), primary_key=True),
    Column('magic_beast_id', Integer, ForeignKey('magic_beasts.id'), primary_key=True)
)

class GateGrade(enum.Enum):
    F = "F"
    E = "E"
    D = "D"
    C = "C"
    B = "B"
    A = "A"
    S = "S"
    SS = "SS"
    SSS = "SSS"

class MagicBeastType(enum.Enum):
    NORMAL = "Normal"
    ELITE = "Elite"
    BOSS = "Boss"
    RAID = "Raid"
    EVENT = "Event"

class Gate(db.Model):
    __tablename__ = 'gates'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    grade = Column(Enum(GateGrade), nullable=False)
    level = Column(Integer, nullable=False)
    difficulty = Column(Float, nullable=False)
    is_active = Column(Boolean, default=True)
    max_players = Column(Integer, default=1)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    magic_beasts = relationship('MagicBeast', secondary=gate_magic_beasts, back_populates='gates')
    sessions = relationship('GateSession', back_populates='gate')

    def __repr__(self):
        return f'<Gate {self.name} ({self.grade.value})>'

class MagicBeast(db.Model):
    __tablename__ = 'magic_beasts'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    type = Column(Enum(MagicBeastType), nullable=False)
    level = Column(Integer, nullable=False)
    hp = Column(Integer, nullable=False)
    attack = Column(Integer, nullable=False)
    defense = Column(Integer, nullable=False)
    speed = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    gates = relationship('Gate', secondary=gate_magic_beasts, back_populates='magic_beasts')
    behaviors = relationship('AIBehavior', back_populates='magic_beast')

    def __repr__(self):
        return f'<MagicBeast {self.name} ({self.type.value})>'

class GateSession(db.Model):
    __tablename__ = 'gate_sessions'

    id = Column(Integer, primary_key=True)
    gate_id = Column(Integer, ForeignKey('gates.id'), nullable=False)
    player_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    start_time = Column(DateTime, default=datetime.utcnow)
    end_time = Column(DateTime)
    status = Column(String(20), default='active')  # active, completed, failed
    score = Column(Integer)
    rewards = Column(String(500))  # JSON string of rewards
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    gate = relationship('Gate', back_populates='sessions')
    player = relationship('User', back_populates='gate_sessions')

    def __repr__(self):
        return f'<GateSession {self.id} ({self.status})>'

class AIBehavior(db.Model):
    __tablename__ = 'ai_behaviors'

    id = Column(Integer, primary_key=True)
    magic_beast_id = Column(Integer, ForeignKey('magic_beasts.id'), nullable=False)
    trigger_condition = Column(String(200), nullable=False)
    action = Column(String(200), nullable=False)
    cooldown = Column(Integer, default=0)
    priority = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    magic_beast = relationship('MagicBeast', back_populates='behaviors')

    def __repr__(self):
        return f'<AIBehavior {self.id} for MagicBeast {self.magic_beast_id}>'
