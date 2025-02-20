from database import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, JSON
import enum

class ItemType(enum.Enum):
    WEAPON = "Weapon"
    ARMOR = "Armor"
    ACCESSORY = "Accessory"
    CONSUMABLE = "Consumable"
    MATERIAL = "Material"
    LICENSE = "License"
    SPECIAL = "Special"

class ItemRarity(enum.Enum):
    BASIC = "Basic"
    INTERMEDIATE = "Intermediate"
    EXCELLENT = "Excellent"
    LEGENDARY = "Legendary"
    IMMORTAL = "Immortal"

class EquipmentType(enum.Enum):
    # Weapons
    SWORD = "Sword"
    STAFF = "Staff"
    DAGGER = "Dagger"
    BOW = "Bow"
    WAND = "Wand"
    
    # Armor
    HELMET = "Helmet"
    CHEST = "Chest"
    GLOVES = "Gloves"
    BOOTS = "Boots"
    SHIELD = "Shield"
    
    # Accessories
    RING = "Ring"
    NECKLACE = "Necklace"
    EARRING = "Earring"
    BELT = "Belt"

class EquipmentSlot(enum.Enum):
    MAIN_HAND = "Main Hand"
    OFF_HAND = "Off Hand"
    HEAD = "Head"
    CHEST = "Chest"
    HANDS = "Hands"
    FEET = "Feet"
    RING_1 = "Ring 1"
    RING_2 = "Ring 2"
    NECKLACE = "Necklace"
    EARRING_1 = "Earring 1"
    EARRING_2 = "Earring 2"
    BELT = "Belt"

class Item(db.Model):
    __tablename__ = 'items'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    type = Column(Enum(ItemType), nullable=False)
    rarity = Column(Enum(ItemRarity), nullable=False)
    level_requirement = Column(Integer, default=1)
    is_tradeable = Column(Boolean, default=True)
    is_stackable = Column(Boolean, default=False)
    max_stack = Column(Integer, default=1)
    buy_price_exons = Column(Float)
    buy_price_crystals = Column(Float)
    sell_price_exons = Column(Float)
    sell_price_crystals = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Equipment specific fields
    equipment_type = Column(Enum(EquipmentType))
    equipment_slot = Column(Enum(EquipmentSlot))
    durability = Column(Float)  # Current durability
    max_durability = Column(Float, default=100.0)  # Maximum durability
    stats = Column(JSON)  # Equipment stats as JSON

    # Relationships
    inventories = relationship('Inventory', back_populates='item')
    equipment = relationship('Equipment', back_populates='item')

    def __repr__(self):
        return f'<Item {self.name} ({self.type.value})>'

    def calculate_durability_loss(self, damage_taken, mana_used, time_spent):
        """Calculate durability loss based on combat factors"""
        durability_loss = (
            (damage_taken * 0.01) +  # 1% per damage taken
            (mana_used * 0.005) +    # 0.5% per mana used
            (time_spent * 0.1)       # 0.1% per second
        )
        return min(durability_loss, self.durability)

    def repair_cost_crystals(self):
        """Calculate repair cost in crystals"""
        if self.durability >= self.max_durability:
            return 0
        
        missing_durability = self.max_durability - self.durability
        base_cost = missing_durability * (
            10 if self.rarity == ItemRarity.BASIC else
            20 if self.rarity == ItemRarity.INTERMEDIATE else
            40 if self.rarity == ItemRarity.EXCELLENT else
            80 if self.rarity == ItemRarity.LEGENDARY else
            160  # IMMORTAL
        )
        return base_cost

class Inventory(db.Model):
    __tablename__ = 'inventories'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    quantity = Column(Integer, default=1)
    slot = Column(Integer)  # Inventory slot number
    is_locked = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='inventory')
    item = relationship('Item', back_populates='inventories')

    def __repr__(self):
        return f'<Inventory {self.user.username} - {self.item.name} x{self.quantity}>'

class Equipment(db.Model):
    __tablename__ = 'equipment'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    item_id = Column(Integer, ForeignKey('items.id'), nullable=False)
    slot = Column(Enum(EquipmentSlot), nullable=False)
    is_broken = Column(Boolean, default=False)
    equipped_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='equipment')
    item = relationship('Item', back_populates='equipment')

    def __repr__(self):
        return f'<Equipment {self.user.username} - {self.item.name} ({self.slot.value})>'

    def update_durability(self, damage_taken, mana_used, time_spent):
        """Update equipment durability based on combat factors"""
        if not self.is_broken:
            durability_loss = self.item.calculate_durability_loss(
                damage_taken, mana_used, time_spent
            )
            self.item.durability -= durability_loss
            
            if self.item.durability <= 0:
                self.item.durability = 0
                self.is_broken = True
            
            db.session.commit()

# Initialize default items
def init_items():
    """Initialize default items"""
    default_items = [
        # Licenses
        {
            'name': 'Job Reset License',
            'description': 'Allows resetting current job',
            'type': ItemType.LICENSE,
            'rarity': ItemRarity.BASIC,
            'buy_price_exons': 1000,
            'is_tradeable': False
        },
        {
            'name': 'Job License',
            'description': 'Required for job advancement',
            'type': ItemType.LICENSE,
            'rarity': ItemRarity.BASIC,
            'buy_price_exons': 2000,
            'is_tradeable': False
        },
        {
            'name': 'Hunter Class Upgrade License',
            'description': 'Required for hunter class advancement',
            'type': ItemType.LICENSE,
            'rarity': ItemRarity.BASIC,
            'buy_price_exons': 5000,
            'is_tradeable': False
        },
        {
            'name': 'Remote Shop License',
            'description': 'Enables remote shop access',
            'type': ItemType.LICENSE,
            'rarity': ItemRarity.BASIC,
            'buy_price_exons': 3000,
            'is_tradeable': False
        },
        
        # Consumables
        {
            'name': 'Basic Life Potion',
            'description': 'Restores 30% HP',
            'type': ItemType.CONSUMABLE,
            'rarity': ItemRarity.BASIC,
            'buy_price_crystals': 100,
            'is_stackable': True,
            'max_stack': 100
        },
        {
            'name': 'High Grade Life Potion',
            'description': 'Restores 70% HP',
            'type': ItemType.CONSUMABLE,
            'rarity': ItemRarity.INTERMEDIATE,
            'buy_price_crystals': 300,
            'is_stackable': True,
            'max_stack': 100
        },
        {
            'name': 'Basic Resurrection Potion',
            'description': 'Revives with 50% HP',
            'type': ItemType.CONSUMABLE,
            'rarity': ItemRarity.EXCELLENT,
            'buy_price_exons': 1000,
            'is_stackable': True,
            'max_stack': 10
        },
        {
            'name': 'Advanced Resurrection Potion',
            'description': 'Revives with 100% HP, works on decapitated/shadow status',
            'type': ItemType.CONSUMABLE,
            'rarity': ItemRarity.LEGENDARY,
            'buy_price_exons': 3000,
            'is_stackable': True,
            'max_stack': 5
        }
    ]
    
    for item_data in default_items:
        item = Item.query.filter_by(name=item_data['name']).first()
        if not item:
            item = Item(**item_data)
            db.session.add(item)
    
    db.session.commit()
