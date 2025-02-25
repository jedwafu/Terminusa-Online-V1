from datetime import datetime
from enum import Enum
from models import db

class MountType(Enum):
    BASIC = 'Basic'
    INTERMEDIATE = 'Intermediate'
    EXCELLENT = 'Excellent'
    LEGENDARY = 'Legendary'
    IMMORTAL = 'Immortal'

class PetType(Enum):
    BASIC = 'Basic'
    INTERMEDIATE = 'Intermediate'
    EXCELLENT = 'Excellent'
    LEGENDARY = 'Legendary'
    IMMORTAL = 'Immortal'

class Mount(db.Model):
    __tablename__ = 'mounts'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    mount_type = db.Column(db.Enum(MountType), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Stats
    speed = db.Column(db.Integer, default=10)
    stamina = db.Column(db.Integer, default=10)
    luck = db.Column(db.Integer, default=5)
    
    # Relationships
    owner = db.relationship('User', back_populates='mounts')

class Pet(db.Model):
    __tablename__ = 'pets'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    name = db.Column(db.String(100), nullable=False)
    pet_type = db.Column(db.Enum(PetType), nullable=False)
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Stats
    attack = db.Column(db.Integer, default=10)
    defense = db.Column(db.Integer, default=10)
    intelligence = db.Column(db.Integer, default=10)
    
    # Relationships
    owner = db.relationship('User', back_populates='pets')
