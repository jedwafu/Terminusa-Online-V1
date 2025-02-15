import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ItemType(Enum):
    """Types of items"""
    WEAPON = auto()
    ARMOR = auto()
    ACCESSORY = auto()
    CONSUMABLE = auto()
    MATERIAL = auto()
    QUEST = auto()
    COSMETIC = auto()

class ItemRarity(Enum):
    """Item rarity levels"""
    COMMON = auto()
    UNCOMMON = auto()
    RARE = auto()
    EPIC = auto()
    LEGENDARY = auto()
    MYTHICAL = auto()

class EquipmentSlot(Enum):
    """Equipment slots"""
    HEAD = auto()
    CHEST = auto()
    LEGS = auto()
    WEAPON = auto()
    OFFHAND = auto()
    ACCESSORY1 = auto()
    ACCESSORY2 = auto()

@dataclass
class ItemStats:
    """Item statistics"""
    attack: int = 0
    defense: int = 0
    magic_attack: int = 0
    magic_defense: int = 0
    health: int = 0
    mana: int = 0
    strength: int = 0
    agility: int = 0
    intelligence: int = 0
    luck: int = 0

@dataclass
class Item:
    """Item data"""
    id: int
    name: str
    type: ItemType
    rarity: ItemRarity
    level: int
    stats: ItemStats
    durability: Optional[int] = None
    max_durability: Optional[int] = None
    stackable: bool = False
    max_stack: int = 1
    tradeable: bool = True
    description: str = ""
    effects: List[Dict] = None
    slot: Optional[EquipmentSlot] = None

class InventorySystem:
    """Manages player inventories"""
    def __init__(self):
        self.inventories: Dict[int, Dict[int, List[Item]]] = {}  # user_id -> slot -> items
        self.equipment: Dict[int, Dict[EquipmentSlot, Optional[Item]]] = {}  # user_id -> slot -> item
        self.max_slots = 30

    def create_inventory(self, user_id: int):
        """Create inventory for user"""
        if user_id not in self.inventories:
            self.inventories[user_id] = {}
            self.equipment[user_id] = {slot: None for slot in EquipmentSlot}

    def add_item(self, user_id: int, item: Item, quantity: int = 1) -> bool:
        """Add item to inventory"""
        if user_id not in self.inventories:
            return False
        
        if item.stackable:
            # Find existing stack
            for slot, items in self.inventories[user_id].items():
                for existing in items:
                    if existing.id == item.id and len(items) < item.max_stack:
                        items.append(item)
                        return True
        
        # Find empty slot
        for slot in range(self.max_slots):
            if slot not in self.inventories[user_id]:
                self.inventories[user_id][slot] = [item]
                return True
            elif len(self.inventories[user_id][slot]) == 0:
                self.inventories[user_id][slot] = [item]
                return True
        
        return False

    def remove_item(self, user_id: int, slot: int, quantity: int = 1) -> Optional[Item]:
        """Remove item from inventory"""
        if user_id not in self.inventories or slot not in self.inventories[user_id]:
            return None
        
        items = self.inventories[user_id][slot]
        if not items:
            return None
        
        item = items.pop()
        if not items:
            del self.inventories[user_id][slot]
        
        return item

    def equip_item(self, user_id: int, slot: int) -> bool:
        """Equip item from inventory"""
        if user_id not in self.inventories or slot not in self.inventories[user_id]:
            return False
        
        items = self.inventories[user_id][slot]
        if not items:
            return False
        
        item = items[0]
        if not item.slot:
            return False
        
        # Unequip existing item
        if self.equipment[user_id][item.slot]:
            old_item = self.equipment[user_id][item.slot]
            if not self.add_item(user_id, old_item):
                return False
        
        # Equip new item
        self.equipment[user_id][item.slot] = item
        self.remove_item(user_id, slot)
        return True

    def unequip_item(self, user_id: int, slot: EquipmentSlot) -> bool:
        """Unequip item"""
        if user_id not in self.equipment or not self.equipment[user_id][slot]:
            return False
        
        item = self.equipment[user_id][slot]
        if self.add_item(user_id, item):
            self.equipment[user_id][slot] = None
            return True
        
        return False

    def get_equipment_stats(self, user_id: int) -> ItemStats:
        """Calculate total equipment stats"""
        if user_id not in self.equipment:
            return ItemStats()
        
        total_stats = ItemStats()
        for item in self.equipment[user_id].values():
            if item:
                for stat_name, value in item.stats.__dict__.items():
                    current = getattr(total_stats, stat_name)
                    setattr(total_stats, stat_name, current + value)
        
        return total_stats

class TestInventory(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.inventory_system = InventorySystem()
        
        # Create test items
        self.items = [
            Item(
                id=1,
                name="Iron Sword",
                type=ItemType.WEAPON,
                rarity=ItemRarity.COMMON,
                level=1,
                stats=ItemStats(attack=10),
                durability=100,
                max_durability=100,
                slot=EquipmentSlot.WEAPON
            ),
            Item(
                id=2,
                name="Leather Armor",
                type=ItemType.ARMOR,
                rarity=ItemRarity.COMMON,
                level=1,
                stats=ItemStats(defense=5),
                durability=100,
                max_durability=100,
                slot=EquipmentSlot.CHEST
            ),
            Item(
                id=3,
                name="Health Potion",
                type=ItemType.CONSUMABLE,
                rarity=ItemRarity.COMMON,
                level=1,
                stats=ItemStats(),
                stackable=True,
                max_stack=10
            )
        ]
        
        # Create test inventory
        self.test_user_id = 1
        self.inventory_system.create_inventory(self.test_user_id)

    def test_basic_inventory(self):
        """Test basic inventory operations"""
        # Add item
        success = self.inventory_system.add_item(
            self.test_user_id,
            self.items[0]  # Iron Sword
        )
        self.assertTrue(success)
        
        # Remove item
        item = self.inventory_system.remove_item(self.test_user_id, 0)
        self.assertIsNotNone(item)
        self.assertEqual(item.name, "Iron Sword")

    def test_stacking(self):
        """Test item stacking"""
        # Add stackable items
        potion = self.items[2]  # Health Potion
        
        for _ in range(5):
            success = self.inventory_system.add_item(
                self.test_user_id,
                potion
            )
            self.assertTrue(success)
        
        # Verify stack
        inventory = self.inventory_system.inventories[self.test_user_id]
        stack = next(iter(inventory.values()))
        self.assertEqual(len(stack), 5)

    def test_equipment(self):
        """Test equipment system"""
        # Add equipment
        self.inventory_system.add_item(
            self.test_user_id,
            self.items[0]  # Iron Sword
        )
        
        # Equip item
        success = self.inventory_system.equip_item(self.test_user_id, 0)
        self.assertTrue(success)
        
        # Verify equipment
        equipment = self.inventory_system.equipment[self.test_user_id]
        self.assertIsNotNone(equipment[EquipmentSlot.WEAPON])
        self.assertEqual(
            equipment[EquipmentSlot.WEAPON].name,
            "Iron Sword"
        )

    def test_equipment_stats(self):
        """Test equipment stats calculation"""
        # Equip multiple items
        self.inventory_system.add_item(self.test_user_id, self.items[0])
        self.inventory_system.add_item(self.test_user_id, self.items[1])
        
        self.inventory_system.equip_item(self.test_user_id, 0)  # Sword
        self.inventory_system.equip_item(self.test_user_id, 1)  # Armor
        
        # Calculate total stats
        stats = self.inventory_system.get_equipment_stats(self.test_user_id)
        
        self.assertEqual(stats.attack, 10)  # From sword
        self.assertEqual(stats.defense, 5)   # From armor

    def test_inventory_limits(self):
        """Test inventory space limits"""
        # Fill inventory
        item = self.items[0]
        added = 0
        
        while self.inventory_system.add_item(self.test_user_id, item):
            added += 1
        
        self.assertEqual(added, self.inventory_system.max_slots)
        
        # Try to add one more
        success = self.inventory_system.add_item(self.test_user_id, item)
        self.assertFalse(success)

    def test_equipment_swapping(self):
        """Test equipment slot swapping"""
        # Add two weapons
        sword1 = self.items[0]
        sword2 = Item(
            id=4,
            name="Steel Sword",
            type=ItemType.WEAPON,
            rarity=ItemRarity.UNCOMMON,
            level=5,
            stats=ItemStats(attack=15),
            durability=100,
            max_durability=100,
            slot=EquipmentSlot.WEAPON
        )
        
        self.inventory_system.add_item(self.test_user_id, sword1)
        self.inventory_system.add_item(self.test_user_id, sword2)
        
        # Equip first sword
        self.inventory_system.equip_item(self.test_user_id, 0)
        
        # Equip second sword
        self.inventory_system.equip_item(self.test_user_id, 1)
        
        # Verify equipment and inventory
        equipment = self.inventory_system.equipment[self.test_user_id]
        self.assertEqual(equipment[EquipmentSlot.WEAPON].name, "Steel Sword")
        
        # First sword should be back in inventory
        inventory = self.inventory_system.inventories[self.test_user_id]
        found = False
        for items in inventory.values():
            if items and items[0].name == "Iron Sword":
                found = True
                break
        self.assertTrue(found)

    def test_durability(self):
        """Test item durability"""
        # Create item with durability
        sword = self.items[0]
        sword.durability = 50  # Half durability
        
        self.inventory_system.add_item(self.test_user_id, sword)
        self.inventory_system.equip_item(self.test_user_id, 0)
        
        equipment = self.inventory_system.equipment[self.test_user_id]
        self.assertEqual(equipment[EquipmentSlot.WEAPON].durability, 50)

    def test_item_requirements(self):
        """Test item level requirements"""
        # Create high-level item
        high_level_sword = Item(
            id=5,
            name="Epic Sword",
            type=ItemType.WEAPON,
            rarity=ItemRarity.EPIC,
            level=50,
            stats=ItemStats(attack=100),
            slot=EquipmentSlot.WEAPON
        )
        
        # Add to inventory
        self.inventory_system.add_item(self.test_user_id, high_level_sword)
        
        # Try to equip (should fail due to level requirement)
        success = self.inventory_system.equip_item(self.test_user_id, 0)
        self.assertFalse(success)

    def test_item_effects(self):
        """Test item special effects"""
        # Create item with effects
        magic_sword = Item(
            id=6,
            name="Flaming Sword",
            type=ItemType.WEAPON,
            rarity=ItemRarity.RARE,
            level=10,
            stats=ItemStats(attack=20),
            slot=EquipmentSlot.WEAPON,
            effects=[
                {'type': 'fire_damage', 'value': 5},
                {'type': 'burn_chance', 'value': 0.1}
            ]
        )
        
        self.inventory_system.add_item(self.test_user_id, magic_sword)
        self.inventory_system.equip_item(self.test_user_id, 0)
        
        equipment = self.inventory_system.equipment[self.test_user_id]
        self.assertEqual(len(equipment[EquipmentSlot.WEAPON].effects), 2)

if __name__ == '__main__':
    unittest.main()
