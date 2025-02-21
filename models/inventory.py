"""
Inventory model for Terminusa Online
"""
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB
from enum import Enum

from models import db

class ItemType(Enum):
    WEAPON = "weapon"
    ARMOR = "armor"
    ACCESSORY = "accessory"
    CONSUMABLE = "consumable"
    MATERIAL = "material"
    QUEST_ITEM = "quest_item"
    MOUNT = "mount"
    PET = "pet"

class ItemRarity(Enum):
    COMMON = "common"
    UNCOMMON = "uncommon"
    RARE = "rare"
    EPIC = "epic"
    LEGENDARY = "legendary"
    MYTHICAL = "mythical"

class Inventory(db.Model):
    __tablename__ = 'inventories'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Main inventory storage
    items = db.Column(JSONB, nullable=False, default={})
    
    # Equipment slots
    equipment = db.Column(JSONB, nullable=False, default={
        'weapon': None,
        'armor': None,
        'helmet': None,
        'gloves': None,
        'boots': None,
        'accessory1': None,
        'accessory2': None,
        'mount': None,
        'pet': None
    })
    
    # Quick access slots for consumables
    quickslots = db.Column(JSONB, nullable=False, default={
        'slot1': None,
        'slot2': None,
        'slot3': None,
        'slot4': None
    })
    
    # Inventory limits
    max_slots = db.Column(db.Integer, default=50)
    max_weight = db.Column(db.Float, default=100.0)
    current_weight = db.Column(db.Float, default=0.0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __init__(self, user_id: int):
        self.user_id = user_id

    def add_item(self, item_id: str, item_data: Dict) -> Tuple[bool, str]:
        """Add an item to inventory"""
        try:
            # Check inventory space
            if len(self.items) >= self.max_slots:
                return False, "Inventory is full"
            
            # Check weight limit
            new_weight = self.current_weight + item_data.get('weight', 0)
            if new_weight > self.max_weight:
                return False, "Weight limit exceeded"
            
            # Add or stack item
            if item_data.get('stackable', False):
                if item_id in self.items:
                    self.items[item_id]['quantity'] += item_data['quantity']
                else:
                    self.items[item_id] = item_data
            else:
                # Generate unique instance ID for non-stackable items
                instance_id = f"{item_id}_{datetime.utcnow().timestamp()}"
                self.items[instance_id] = item_data
            
            self.current_weight = new_weight
            return True, "Item added successfully"
            
        except Exception as e:
            return False, str(e)

    def remove_item(self, item_id: str, quantity: int = 1) -> Tuple[bool, str]:
        """Remove an item from inventory"""
        try:
            if item_id not in self.items:
                return False, "Item not found"
            
            item = self.items[item_id]
            
            if item.get('stackable', False):
                if item['quantity'] < quantity:
                    return False, "Insufficient quantity"
                    
                item['quantity'] -= quantity
                if item['quantity'] <= 0:
                    del self.items[item_id]
            else:
                del self.items[item_id]
            
            self.current_weight -= item.get('weight', 0) * quantity
            return True, "Item removed successfully"
            
        except Exception as e:
            return False, str(e)

    def equip_item(self, item_id: str) -> Tuple[bool, str]:
        """Equip an item"""
        try:
            if item_id not in self.items:
                return False, "Item not found"
            
            item = self.items[item_id]
            slot = item.get('slot')
            
            if not slot:
                return False, "Item cannot be equipped"
            
            # Unequip current item in slot if any
            if self.equipment[slot]:
                old_item_id = self.equipment[slot]
                self.equipment[slot] = None
                # Move old item back to inventory
                if old_item_id in self.items:
                    self.items[old_item_id]['equipped'] = False
            
            # Equip new item
            self.equipment[slot] = item_id
            item['equipped'] = True
            
            return True, "Item equipped successfully"
            
        except Exception as e:
            return False, str(e)

    def unequip_item(self, slot: str) -> Tuple[bool, str]:
        """Unequip an item"""
        try:
            if slot not in self.equipment:
                return False, "Invalid equipment slot"
            
            item_id = self.equipment[slot]
            if not item_id:
                return False, "No item equipped in slot"
            
            # Check inventory space
            if len(self.items) >= self.max_slots:
                return False, "Inventory is full"
            
            # Unequip item
            self.equipment[slot] = None
            if item_id in self.items:
                self.items[item_id]['equipped'] = False
            
            return True, "Item unequipped successfully"
            
        except Exception as e:
            return False, str(e)

    def set_quickslot(self, slot: str, item_id: str) -> Tuple[bool, str]:
        """Set an item to a quickslot"""
        try:
            if slot not in self.quickslots:
                return False, "Invalid quickslot"
            
            if item_id and item_id not in self.items:
                return False, "Item not found"
            
            # Clear other quickslots with this item
            for qs in self.quickslots:
                if self.quickslots[qs] == item_id:
                    self.quickslots[qs] = None
            
            self.quickslots[slot] = item_id
            return True, "Quickslot set successfully"
            
        except Exception as e:
            return False, str(e)

    def use_item(self, item_id: str) -> Tuple[bool, str, Dict]:
        """Use a consumable item"""
        try:
            if item_id not in self.items:
                return False, "Item not found", {}
            
            item = self.items[item_id]
            if item['type'] != ItemType.CONSUMABLE.value:
                return False, "Item cannot be used", {}
            
            # Check if item can be used
            if not item.get('usable', False):
                return False, "Item cannot be used", {}
            
            # Get item effects
            effects = item.get('effects', {})
            
            # Remove one from quantity or remove item
            success, message = self.remove_item(item_id, 1)
            if not success:
                return False, message, {}
            
            return True, "Item used successfully", effects
            
        except Exception as e:
            return False, str(e), {}

    def has_item(self, item_id: str, quantity: int = 1) -> bool:
        """Check if inventory has item in specified quantity"""
        if item_id not in self.items:
            return False
            
        item = self.items[item_id]
        if item.get('stackable', False):
            return item['quantity'] >= quantity
        return True

    def get_equipped_items(self) -> Dict[str, Dict]:
        """Get all equipped items"""
        equipped = {}
        for slot, item_id in self.equipment.items():
            if item_id and item_id in self.items:
                equipped[slot] = self.items[item_id]
        return equipped

    def get_consumables(self) -> List[Dict]:
        """Get all consumable items"""
        return [
            {'id': item_id, **item_data}
            for item_id, item_data in self.items.items()
            if item_data['type'] == ItemType.CONSUMABLE.value
        ]

    def get_resurrection_potions(self) -> List[Dict]:
        """Get all resurrection potions"""
        return [
            {'id': item_id, **item_data}
            for item_id, item_data in self.items.items()
            if (item_data['type'] == ItemType.CONSUMABLE.value and 
                item_data.get('effect_type') == 'resurrection')
        ]

    def calculate_stats(self) -> Dict[str, float]:
        """Calculate total stats from equipped items"""
        total_stats = {
            'attack': 0,
            'defense': 0,
            'magic_attack': 0,
            'magic_defense': 0,
            'health': 0,
            'mana': 0,
            'critical_rate': 0,
            'critical_damage': 0,
            'speed': 0
        }
        
        # Add stats from equipped items
        for item_id in self.equipment.values():
            if item_id and item_id in self.items:
                item = self.items[item_id]
                stats = item.get('stats', {})
                for stat, value in stats.items():
                    if stat in total_stats:
                        total_stats[stat] += value
        
        return total_stats

    def to_dict(self) -> Dict:
        """Convert inventory data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'items': self.items,
            'equipment': self.equipment,
            'quickslots': self.quickslots,
            'max_slots': self.max_slots,
            'max_weight': self.max_weight,
            'current_weight': self.current_weight,
            'stats': self.calculate_stats()
        }
