"""
Item model for Terminusa Online
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from models import db
from .inventory import ItemType, ItemRarity

class Item(db.Model):
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(db.Enum(ItemType), nullable=False)
    rarity = db.Column(db.Enum(ItemRarity), nullable=False)
    
    # Item properties
    level_requirement = db.Column(db.Integer, default=1)
    durability = db.Column(db.Integer)
    max_durability = db.Column(db.Integer)
    stackable = db.Column(db.Boolean, default=False)
    tradeable = db.Column(db.Boolean, default=True)
    usable = db.Column(db.Boolean, default=False)
    
    # Item stats and effects
    stats = db.Column(JSONB, default={})
    effects = db.Column(JSONB, default={})
    
    # Market information
    price_crystals = db.Column(db.Integer)
    price_exons = db.Column(db.Float)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, name: str, type: ItemType, rarity: ItemRarity, **kwargs):
        self.name = name
        self.type = type
        self.rarity = rarity
        for key, value in kwargs.items():
            setattr(self, key, value)

    def to_dict(self) -> dict:
        """Convert item to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'rarity': self.rarity.value,
            'level_requirement': self.level_requirement,
            'durability': self.durability,
            'max_durability': self.max_durability,
            'stackable': self.stackable,
            'tradeable': self.tradeable,
            'usable': self.usable,
            'stats': self.stats,
            'effects': self.effects,
            'price_crystals': self.price_crystals,
            'price_exons': self.price_exons
        }

    @staticmethod
    def get_by_name(name: str) -> 'Item':
        """Get item by name"""
        return Item.query.filter_by(name=name).first()

    @staticmethod
    def get_by_type(type: ItemType) -> list['Item']:
        """Get items by type"""
        return Item.query.filter_by(type=type).all()

    @staticmethod
    def get_by_rarity(rarity: ItemRarity) -> list['Item']:
        """Get items by rarity"""
        return Item.query.filter_by(rarity=rarity).all()
