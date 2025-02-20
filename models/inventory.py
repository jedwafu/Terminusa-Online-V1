from app import db
from datetime import datetime
from enum import Enum

class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    QUEST = "quest"
    LICENSE = "license"
    MOUNT = "mount"
    PET = "pet"

class ItemGrade(Enum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    EXCELLENT = "excellent"
    LEGENDARY = "legendary"
    IMMORTAL = "immortal"

class ItemSlot(Enum):
    WEAPON = "weapon"
    HEAD = "head"
    CHEST = "chest"
    LEGS = "legs"
    FEET = "feet"
    HANDS = "hands"
    NECK = "neck"
    RING = "ring"
    MOUNT = "mount"
    PET = "pet"

class Item(db.Model):
    """Item definition model"""
    __tablename__ = 'items'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    item_type = db.Column(db.Enum(ItemType), nullable=False)
    grade = db.Column(db.Enum(ItemGrade), nullable=False)
    slot = db.Column(db.Enum(ItemSlot), nullable=True)
    level_requirement = db.Column(db.Integer, default=1)
    job_requirement = db.Column(db.String(50), nullable=True)
    
    # Item Properties
    durability_max = db.Column(db.Integer, nullable=True)
    is_tradeable = db.Column(db.Boolean, default=True)
    is_stackable = db.Column(db.Boolean, default=False)
    max_stack = db.Column(db.Integer, default=1)
    
    # Shop Properties
    crystal_price = db.Column(db.Integer, nullable=True)
    exon_price = db.Column(db.Integer, nullable=True)
    can_sell = db.Column(db.Boolean, default=True)
    sell_price = db.Column(db.Integer, nullable=True)
    
    # Stats (for equipment)
    stats = db.Column(db.JSON, nullable=True)  # {"strength": 10, "agility": 5, etc.}
    
    # Effects (for consumables)
    effects = db.Column(db.JSON, nullable=True)  # {"heal": 100, "duration": 30, etc.}
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Item {self.name}>"

class Inventory(db.Model):
    """Player inventory model"""
    __tablename__ = 'inventories'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    max_slots = db.Column(db.Integer, default=20)
    crystal_balance = db.Column(db.Integer, default=0)  # For dropped currency
    exon_balance = db.Column(db.Integer, default=0)  # For dropped currency
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    items = db.relationship('InventoryItem', backref='inventory', lazy='dynamic')
    equipped_items = db.relationship('EquippedItem', backref='inventory', lazy='dynamic')

    def __repr__(self):
        return f"<Inventory {self.id}>"

class InventoryItem(db.Model):
    """Item instance in inventory"""
    __tablename__ = 'inventory_items'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventories.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    slot_number = db.Column(db.Integer, nullable=False)
    durability = db.Column(db.Integer, nullable=True)
    is_bound = db.Column(db.Boolean, default=False)
    bound_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    item = db.relationship('Item')

    def __repr__(self):
        return f"<InventoryItem {self.item_id}>"

class EquippedItem(db.Model):
    """Currently equipped items"""
    __tablename__ = 'equipped_items'

    id = db.Column(db.Integer, primary_key=True)
    inventory_id = db.Column(db.Integer, db.ForeignKey('inventories.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    slot = db.Column(db.Enum(ItemSlot), nullable=False)
    durability = db.Column(db.Integer, nullable=True)
    equipped_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    item = db.relationship('Item')

    def __repr__(self):
        return f"<EquippedItem {self.item_id}>"

class ItemDrop(db.Model):
    """Item drop history"""
    __tablename__ = 'item_drops'

    id = db.Column(db.Integer, primary_key=True)
    gate_session_id = db.Column(db.Integer, db.ForeignKey('gate_sessions.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    crystal_amount = db.Column(db.Integer, default=0)
    exon_amount = db.Column(db.Integer, default=0)
    dropped_at = db.Column(db.DateTime, default=datetime.utcnow)
    collected = db.Column(db.Boolean, default=False)
    collected_at = db.Column(db.DateTime, nullable=True)
    collected_by_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=True)

    def __repr__(self):
        return f"<ItemDrop {self.item_id}>"

class Trade(db.Model):
    """Player trade model"""
    __tablename__ = 'trades'

    id = db.Column(db.Integer, primary_key=True)
    initiator_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, completed
    crystal_amount = db.Column(db.Integer, default=0)
    exon_amount = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    items = db.relationship('TradeItem', backref='trade', lazy='dynamic')

    def __repr__(self):
        return f"<Trade {self.id}>"

class TradeItem(db.Model):
    """Items included in a trade"""
    __tablename__ = 'trade_items'

    id = db.Column(db.Integer, primary_key=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=False)
    inventory_item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    offered_by_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)

    def __repr__(self):
        return f"<TradeItem {self.inventory_item_id}>"

class ShopTransaction(db.Model):
    """Shop transaction history"""
    __tablename__ = 'shop_transactions'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    quantity = db.Column(db.Integer, default=1)
    transaction_type = db.Column(db.String(20), nullable=False)  # buy, sell
    crystal_amount = db.Column(db.Integer, default=0)
    exon_amount = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ShopTransaction {self.id}>"
