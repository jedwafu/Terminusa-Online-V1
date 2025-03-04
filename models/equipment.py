"""
Equipment model for Terminusa Online
"""
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from models import db

class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    
    # Equipment Status
    equipped = db.Column(db.Boolean, default=False)
    slot = db.Column(db.String(20), nullable=False)  # weapon, armor, accessory, etc.
    durability = db.Column(db.Integer, nullable=False)
    element = db.Column(db.String(20))  # fire, water, earth, etc.
    
    # Enhancement
    enhancement_level = db.Column(db.Integer, default=0)
    enhancement_stats = db.Column(JSONB, default={})
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    equipped_at = db.Column(db.DateTime)

    def __init__(self, user_id: int, item_id: int, slot: str, durability: int, element: str = None):
        self.user_id = user_id
        self.item_id = item_id
        self.slot = slot
        self.durability = durability
        self.element = element

    def equip(self) -> bool:
        """Equip the item"""
        try:
            # Unequip any item in the same slot
            Equipment.query.filter_by(
                user_id=self.user_id,
                slot=self.slot,
                equipped=True
            ).update({'equipped': False})
            
            self.equipped = True
            self.equipped_at = datetime.utcnow()
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def unequip(self) -> bool:
        """Unequip the item"""
        try:
            self.equipped = False
            self.equipped_at = None
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def enhance(self, stats_increase: dict) -> bool:
        """Enhance the equipment"""
        try:
            self.enhancement_level += 1
            self.enhancement_stats.update(stats_increase)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def repair(self, amount: int) -> bool:
        """Repair equipment durability"""
        try:
            self.durability = min(100, self.durability + amount)
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def to_dict(self) -> dict:
        """Convert equipment data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'item_id': self.item_id,
            'equipped': self.equipped,
            'slot': self.slot,
            'durability': self.durability,
            'element': self.element,
            'enhancement_level': self.enhancement_level,
            'enhancement_stats': self.enhancement_stats,
            'timestamps': {
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat(),
                'equipped': self.equipped_at.isoformat() if self.equipped_at else None
            }
        }

    @staticmethod
    def get_equipped(user_id: int) -> list['Equipment']:
        """Get all equipped items for a user"""
        return Equipment.query.filter_by(
            user_id=user_id,
            equipped=True
        ).all()

    @staticmethod
    def get_by_slot(user_id: int, slot: str) -> list['Equipment']:
        """Get all items in a specific slot"""
        return Equipment.query.filter_by(
            user_id=user_id,
            slot=slot
        ).all()
