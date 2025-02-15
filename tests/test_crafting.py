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

from models import User, Item, Inventory

class CraftingSkill(Enum):
    """Crafting skill types"""
    BLACKSMITHING = auto()
    ALCHEMY = auto()
    ENCHANTING = auto()
    TAILORING = auto()
    COOKING = auto()
    JEWELCRAFTING = auto()

@dataclass
class CraftingMaterial:
    """Crafting material requirement"""
    item_id: int
    amount: int
    quality_min: int = 0
    returnable: bool = False

@dataclass
class CraftingRecipe:
    """Crafting recipe data"""
    id: int
    name: str
    skill: CraftingSkill
    skill_level: int
    materials: List[CraftingMaterial]
    result_item_id: int
    result_amount: int = 1
    success_chance: float = 1.0
    critical_chance: float = 0.1
    time_required: timedelta = timedelta(seconds=5)
    experience: int = 10

class CraftingSystem:
    """Manages crafting system"""
    def __init__(self):
        self.recipes: Dict[int, CraftingRecipe] = {}
        self.user_skills: Dict[int, Dict[CraftingSkill, int]] = {}
        self.active_crafts: Dict[int, List[Dict]] = {}  # user_id -> crafting sessions

    def register_recipe(self, recipe: CraftingRecipe):
        """Register a crafting recipe"""
        self.recipes[recipe.id] = recipe

    def get_available_recipes(self, user_id: int) -> List[CraftingRecipe]:
        """Get available recipes for user"""
        if user_id not in self.user_skills:
            return []
        
        available = []
        for recipe in self.recipes.values():
            skill_level = self.user_skills[user_id].get(recipe.skill, 0)
            if skill_level >= recipe.skill_level:
                available.append(recipe)
        
        return available

    def start_crafting(
        self,
        user_id: int,
        recipe_id: int,
        inventory: Inventory
    ) -> Optional[Dict]:
        """Start crafting process"""
        if recipe_id not in self.recipes:
            return None
        
        recipe = self.recipes[recipe_id]
        
        # Check skill requirement
        if user_id not in self.user_skills:
            self.user_skills[user_id] = {}
        
        skill_level = self.user_skills[user_id].get(recipe.skill, 0)
        if skill_level < recipe.skill_level:
            return None
        
        # Check materials
        for material in recipe.materials:
            if not self._has_materials(inventory, material):
                return None
        
        # Remove materials
        for material in recipe.materials:
            self._remove_materials(inventory, material)
        
        # Start crafting session
        session = {
            'recipe_id': recipe_id,
            'start_time': datetime.utcnow(),
            'end_time': datetime.utcnow() + recipe.time_required
        }
        
        if user_id not in self.active_crafts:
            self.active_crafts[user_id] = []
        self.active_crafts[user_id].append(session)
        
        return session

    def complete_crafting(
        self,
        user_id: int,
        session_index: int,
        inventory: Inventory
    ) -> Dict:
        """Complete crafting process"""
        if user_id not in self.active_crafts:
            return {'status': 'error', 'message': 'No active crafting session'}
        
        sessions = self.active_crafts[user_id]
        if session_index >= len(sessions):
            return {'status': 'error', 'message': 'Invalid session'}
        
        session = sessions[session_index]
        recipe = self.recipes[session['recipe_id']]
        
        # Check if crafting is complete
        if datetime.utcnow() < session['end_time']:
            return {'status': 'error', 'message': 'Crafting still in progress'}
        
        # Remove session
        sessions.pop(session_index)
        
        # Calculate success
        import random
        success = random.random() < recipe.success_chance
        critical = random.random() < recipe.critical_chance
        
        if success:
            # Add result item
            amount = recipe.result_amount * (2 if critical else 1)
            # Implementation would add items to inventory here
            
            # Grant experience
            exp = recipe.experience * (1.5 if critical else 1)
            self._grant_experience(user_id, recipe.skill, exp)
            
            return {
                'status': 'success',
                'critical': critical,
                'amount': amount,
                'experience': exp
            }
        else:
            # Return some materials
            for material in recipe.materials:
                if material.returnable:
                    # Implementation would return items to inventory here
                    pass
            
            return {
                'status': 'failed',
                'message': 'Crafting failed'
            }

    def _has_materials(self, inventory: Inventory, material: CraftingMaterial) -> bool:
        """Check if inventory has required materials"""
        # Implementation would check inventory here
        return True

    def _remove_materials(self, inventory: Inventory, material: CraftingMaterial):
        """Remove materials from inventory"""
        # Implementation would remove items from inventory here
        pass

    def _grant_experience(self, user_id: int, skill: CraftingSkill, amount: int):
        """Grant crafting experience"""
        if user_id not in self.user_skills:
            self.user_skills[user_id] = {}
        if skill not in self.user_skills[user_id]:
            self.user_skills[user_id][skill] = 0
        
        self.user_skills[user_id][skill] += amount

class TestCrafting(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.crafting_system = CraftingSystem()
        
        # Create test recipes
        self.recipes = [
            CraftingRecipe(
                id=1,
                name="Iron Sword",
                skill=CraftingSkill.BLACKSMITHING,
                skill_level=1,
                materials=[
                    CraftingMaterial(item_id=1, amount=2),  # Iron Ingot
                    CraftingMaterial(item_id=2, amount=1)   # Wood
                ],
                result_item_id=3,  # Iron Sword
                result_amount=1,
                success_chance=0.9,
                critical_chance=0.1,
                time_required=timedelta(seconds=5),
                experience=10
            ),
            CraftingRecipe(
                id=2,
                name="Health Potion",
                skill=CraftingSkill.ALCHEMY,
                skill_level=1,
                materials=[
                    CraftingMaterial(item_id=4, amount=2),  # Herbs
                    CraftingMaterial(item_id=5, amount=1)   # Water
                ],
                result_item_id=6,  # Health Potion
                result_amount=1,
                success_chance=0.8,
                critical_chance=0.05,
                time_required=timedelta(seconds=3),
                experience=5
            )
        ]
        
        # Register recipes
        for recipe in self.recipes:
            self.crafting_system.register_recipe(recipe)
        
        # Create test user
        self.user_id = 1
        self.inventory = Mock(spec=Inventory)

    def test_recipe_registration(self):
        """Test recipe registration"""
        # Verify recipes registered
        self.assertEqual(len(self.crafting_system.recipes), 2)
        self.assertIn(1, self.crafting_system.recipes)
        self.assertIn(2, self.crafting_system.recipes)

    def test_recipe_availability(self):
        """Test recipe availability based on skill"""
        # Initially no recipes available (no skills)
        recipes = self.crafting_system.get_available_recipes(self.user_id)
        self.assertEqual(len(recipes), 0)
        
        # Add blacksmithing skill
        self.crafting_system.user_skills[self.user_id] = {
            CraftingSkill.BLACKSMITHING: 1
        }
        
        # Should now have access to iron sword recipe
        recipes = self.crafting_system.get_available_recipes(self.user_id)
        self.assertEqual(len(recipes), 1)
        self.assertEqual(recipes[0].name, "Iron Sword")

    def test_crafting_process(self):
        """Test complete crafting process"""
        # Set up skills
        self.crafting_system.user_skills[self.user_id] = {
            CraftingSkill.BLACKSMITHING: 1
        }
        
        # Start crafting
        session = self.crafting_system.start_crafting(
            self.user_id,
            1,  # Iron Sword
            self.inventory
        )
        
        self.assertIsNotNone(session)
        self.assertEqual(session['recipe_id'], 1)
        
        # Wait for completion
        import time
        time.sleep(5)
        
        # Complete crafting
        result = self.crafting_system.complete_crafting(
            self.user_id,
            0,  # First session
            self.inventory
        )
        
        self.assertEqual(result['status'], 'success')

    def test_crafting_failure(self):
        """Test crafting failure handling"""
        # Create recipe with low success chance
        failing_recipe = CraftingRecipe(
            id=3,
            name="Difficult Item",
            skill=CraftingSkill.BLACKSMITHING,
            skill_level=1,
            materials=[
                CraftingMaterial(item_id=1, amount=1, returnable=True)
            ],
            result_item_id=7,
            success_chance=0.0,  # Always fail
            experience=10
        )
        self.crafting_system.register_recipe(failing_recipe)
        
        # Set up skills
        self.crafting_system.user_skills[self.user_id] = {
            CraftingSkill.BLACKSMITHING: 1
        }
        
        # Attempt crafting
        session = self.crafting_system.start_crafting(
            self.user_id,
            3,
            self.inventory
        )
        
        time.sleep(1)
        
        result = self.crafting_system.complete_crafting(
            self.user_id,
            0,
            self.inventory
        )
        
        self.assertEqual(result['status'], 'failed')

    def test_critical_crafting(self):
        """Test critical success crafting"""
        # Create recipe with high critical chance
        critical_recipe = CraftingRecipe(
            id=4,
            name="Lucky Item",
            skill=CraftingSkill.BLACKSMITHING,
            skill_level=1,
            materials=[
                CraftingMaterial(item_id=1, amount=1)
            ],
            result_item_id=8,
            critical_chance=1.0,  # Always critical
            experience=10
        )
        self.crafting_system.register_recipe(critical_recipe)
        
        # Set up skills
        self.crafting_system.user_skills[self.user_id] = {
            CraftingSkill.BLACKSMITHING: 1
        }
        
        # Attempt crafting
        session = self.crafting_system.start_crafting(
            self.user_id,
            4,
            self.inventory
        )
        
        time.sleep(1)
        
        result = self.crafting_system.complete_crafting(
            self.user_id,
            0,
            self.inventory
        )
        
        self.assertTrue(result['critical'])
        self.assertEqual(result['amount'], 2)  # Double amount

    def test_experience_gain(self):
        """Test crafting experience gain"""
        # Set up initial skills
        self.crafting_system.user_skills[self.user_id] = {
            CraftingSkill.BLACKSMITHING: 1
        }
        
        initial_exp = self.crafting_system.user_skills[self.user_id][CraftingSkill.BLACKSMITHING]
        
        # Complete crafting
        session = self.crafting_system.start_crafting(
            self.user_id,
            1,
            self.inventory
        )
        
        time.sleep(5)
        
        result = self.crafting_system.complete_crafting(
            self.user_id,
            0,
            self.inventory
        )
        
        # Verify experience gain
        final_exp = self.crafting_system.user_skills[self.user_id][CraftingSkill.BLACKSMITHING]
        self.assertGreater(final_exp, initial_exp)

    def test_multiple_crafting_sessions(self):
        """Test multiple simultaneous crafting sessions"""
        # Set up skills
        self.crafting_system.user_skills[self.user_id] = {
            CraftingSkill.BLACKSMITHING: 1,
            CraftingSkill.ALCHEMY: 1
        }
        
        # Start multiple crafting sessions
        session1 = self.crafting_system.start_crafting(
            self.user_id,
            1,  # Iron Sword
            self.inventory
        )
        
        session2 = self.crafting_system.start_crafting(
            self.user_id,
            2,  # Health Potion
            self.inventory
        )
        
        self.assertEqual(len(self.crafting_system.active_crafts[self.user_id]), 2)

if __name__ == '__main__':
    unittest.main()
