"""
Equipment System for Terminusa Online
"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import random
import logging
from models import db, User, Equipment, Transaction
from game_systems.ai_agent import AIAgent
from game_config import (
    EQUIPMENT_GRADES,
    DURABILITY_CONFIG,
    ELEMENTS,
    ELEMENT_DAMAGE_BONUS,
    ELEMENT_DAMAGE_PENALTY
)

logger = logging.getLogger(__name__)

class EquipmentSystem:
    """Handles equipment management, durability, and upgrades"""
    
    def __init__(self):
        self.ai_agent = AIAgent()
        self.equipment_slots = {
            'weapon': ['sword', 'staff', 'bow', 'dagger'],
            'armor': ['light', 'medium', 'heavy'],
            'helmet': ['light', 'medium', 'heavy'],
            'gloves': ['light', 'medium', 'heavy'],
            'boots': ['light', 'medium', 'heavy'],
            'accessory': ['ring', 'necklace', 'earring']
        }

    def equip_item(self, user: User, equipment_id: int) -> Dict:
        """Equip an item"""
        try:
            equipment = Equipment.query.get(equipment_id)
            if not equipment or equipment.user_id != user.id:
                return {
                    "success": False,
                    "message": "Equipment not found"
                }

            # Check if broken
            if equipment.durability <= 0:
                return {
                    "success": False,
                    "message": "Equipment is broken and needs repair"
                }

            # Check level requirement
            if user.level < equipment.level_requirement:
                return {
                    "success": False,
                    "message": f"Level {equipment.level_requirement} required"
                }

            # Check job requirement
            if equipment.job_requirement and user.job_class not in equipment.job_requirement:
                return {
                    "success": False,
                    "message": f"Job {equipment.job_requirement} required"
                }

            # Unequip current item in slot
            current_equipped = Equipment.query.filter_by(
                user_id=user.id,
                slot=equipment.slot,
                equipped=True
            ).first()
            
            if current_equipped:
                current_equipped.equipped = False

            # Equip new item
            equipment.equipped = True
            
            # Update user stats
            self._update_user_stats(user)

            db.session.commit()

            return {
                "success": True,
                "message": "Equipment equipped successfully",
                "stats": self._get_equipment_stats(equipment)
            }

        except Exception as e:
            logger.error(f"Failed to equip item: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to equip item"
            }

    def unequip_item(self, user: User, equipment_id: int) -> Dict:
        """Unequip an item"""
        try:
            equipment = Equipment.query.get(equipment_id)
            if not equipment or equipment.user_id != user.id:
                return {
                    "success": False,
                    "message": "Equipment not found"
                }

            if not equipment.equipped:
                return {
                    "success": False,
                    "message": "Equipment not equipped"
                }

            equipment.equipped = False
            
            # Update user stats
            self._update_user_stats(user)

            db.session.commit()

            return {
                "success": True,
                "message": "Equipment unequipped successfully"
            }

        except Exception as e:
            logger.error(f"Failed to unequip item: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to unequip item"
            }

    def upgrade_equipment(self, user: User, equipment_id: int) -> Dict:
        """Upgrade equipment level"""
        try:
            equipment = Equipment.query.get(equipment_id)
            if not equipment or equipment.user_id != user.id:
                return {
                    "success": False,
                    "message": "Equipment not found"
                }

            # Check if broken
            if equipment.durability <= 0:
                return {
                    "success": False,
                    "message": "Equipment is broken and needs repair"
                }

            # Calculate upgrade cost
            grade_config = EQUIPMENT_GRADES[equipment.grade]
            base_cost = 100 * (equipment.level + 1)
            upgrade_cost = int(base_cost * grade_config['upgrade_cost_multiplier'])

            # Check if user has enough crystals
            if user.crystals < upgrade_cost:
                return {
                    "success": False,
                    "message": f"Insufficient crystals. Need {upgrade_cost}"
                }

            # Get AI-adjusted success rate
            success_rate = self._calculate_upgrade_success_rate(user, equipment)
            
            # Attempt upgrade
            success = random.random() < success_rate

            # Process result
            user.crystals -= upgrade_cost
            
            if success:
                old_stats = self._get_equipment_stats(equipment)
                equipment.level += 1
                self._update_equipment_stats(equipment)
                new_stats = self._get_equipment_stats(equipment)
                
                message = f"Upgrade successful! Level {equipment.level}"
                if equipment.equipped:
                    self._update_user_stats(user)
            else:
                message = "Upgrade failed"
                old_stats = new_stats = self._get_equipment_stats(equipment)

            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type='equipment_upgrade',
                currency='crystals',
                amount=upgrade_cost,
                metadata={
                    'equipment_id': equipment.id,
                    'success': success,
                    'grade': equipment.grade
                }
            )
            db.session.add(transaction)

            db.session.commit()

            return {
                "success": True,
                "message": message,
                "upgrade_success": success,
                "cost": upgrade_cost,
                "old_stats": old_stats,
                "new_stats": new_stats
            }

        except Exception as e:
            logger.error(f"Failed to upgrade equipment: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to upgrade equipment"
            }

    def repair_equipment(self, user: User, equipment_id: int) -> Dict:
        """Repair equipment durability"""
        try:
            equipment = Equipment.query.get(equipment_id)
            if not equipment or equipment.user_id != user.id:
                return {
                    "success": False,
                    "message": "Equipment not found"
                }

            # Calculate repair cost
            durability_loss = DURABILITY_CONFIG['max_durability'] - equipment.durability
            repair_cost = int(durability_loss * DURABILITY_CONFIG['repair_cost_rate'])

            # Check if repair needed
            if durability_loss <= 0:
                return {
                    "success": False,
                    "message": "Equipment doesn't need repair"
                }

            # Check if user has enough crystals
            if user.crystals < repair_cost:
                return {
                    "success": False,
                    "message": f"Insufficient crystals. Need {repair_cost}"
                }

            # Process repair
            user.crystals -= repair_cost
            equipment.durability = DURABILITY_CONFIG['max_durability']

            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type='equipment_repair',
                currency='crystals',
                amount=repair_cost,
                metadata={'equipment_id': equipment.id}
            )
            db.session.add(transaction)

            db.session.commit()

            return {
                "success": True,
                "message": "Equipment repaired successfully",
                "cost": repair_cost,
                "new_durability": equipment.durability
            }

        except Exception as e:
            logger.error(f"Failed to repair equipment: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to repair equipment"
            }

    def change_element(self, user: User, equipment_id: int, new_element: str) -> Dict:
        """Change equipment element"""
        try:
            if new_element not in ELEMENTS:
                return {
                    "success": False,
                    "message": "Invalid element"
                }

            equipment = Equipment.query.get(equipment_id)
            if not equipment or equipment.user_id != user.id:
                return {
                    "success": False,
                    "message": "Equipment not found"
                }

            # Calculate cost
            element_change_cost = 500  # Base cost in crystals

            # Check if user has enough crystals
            if user.crystals < element_change_cost:
                return {
                    "success": False,
                    "message": f"Insufficient crystals. Need {element_change_cost}"
                }

            # Process change
            old_element = equipment.element
            equipment.element = new_element
            user.crystals -= element_change_cost

            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type='element_change',
                currency='crystals',
                amount=element_change_cost,
                metadata={
                    'equipment_id': equipment.id,
                    'old_element': old_element,
                    'new_element': new_element
                }
            )
            db.session.add(transaction)

            db.session.commit()

            return {
                "success": True,
                "message": f"Element changed to {new_element}",
                "cost": element_change_cost,
                "old_element": old_element,
                "new_element": new_element
            }

        except Exception as e:
            logger.error(f"Failed to change element: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to change element"
            }

    def _calculate_upgrade_success_rate(self, user: User, equipment: Equipment) -> float:
        """Calculate AI-adjusted upgrade success rate"""
        try:
            # Get base success rate from equipment grade
            base_rate = EQUIPMENT_GRADES[equipment.grade]['upgrade_success_rate']
            
            # Get AI insights
            profile = self.ai_agent.analyze_player(user)
            if not profile:
                return base_rate

            # Calculate adjustments
            adjustments = {
                # Reward consistent players
                'progression': (
                    0.05 if profile['progression_rate']['progression_score'] > 0.7
                    else 0
                ),
                
                # Balance for unlucky players
                'luck': self._calculate_luck_adjustment(user),
                
                # Activity-based adjustment
                'activity': (
                    0.03 if profile['activity_patterns']['total_actions'] > 100
                    else 0
                )
            }
            
            # Apply adjustments
            final_rate = base_rate + sum(adjustments.values())
            
            # Ensure rate stays within reasonable bounds
            return max(0.01, min(0.99, final_rate))

        except Exception as e:
            logger.error(f"Failed to calculate upgrade rate: {str(e)}")
            return EQUIPMENT_GRADES[equipment.grade]['upgrade_success_rate']

    def _calculate_luck_adjustment(self, user: User) -> float:
        """Calculate luck-based adjustment for upgrades"""
        try:
            # Get recent upgrade attempts
            recent_upgrades = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.type == 'equipment_upgrade',
                Transaction.created_at >= datetime.utcnow() - timedelta(hours=1)
            ).all()

            if not recent_upgrades:
                return 0.0

            # Calculate recent success rate
            successes = sum(
                1 for t in recent_upgrades
                if t.metadata.get('success', False)
            )
            success_rate = successes / len(recent_upgrades)

            # Adjust for unlucky players
            if success_rate < 0.2:  # Very unlucky
                return 0.05  # +5%
            elif success_rate < 0.4:  # Somewhat unlucky
                return 0.03  # +3%
            return 0.0

        except Exception:
            return 0.0

    def _update_user_stats(self, user: User) -> None:
        """Update user stats based on equipped items"""
        try:
            # Reset to base stats
            base_stats = self._get_base_stats(user)
            for stat, value in base_stats.items():
                setattr(user, stat, value)

            # Add equipment bonuses
            equipped_items = Equipment.query.filter_by(
                user_id=user.id,
                equipped=True
            ).all()

            for item in equipped_items:
                user.attack += item.attack
                user.defense += item.defense
                user.magic_attack += item.magic_attack
                user.magic_defense += item.magic_defense
                user.max_hp += item.hp_bonus
                user.max_mp += item.mp_bonus

            # Ensure current HP/MP don't exceed new maximums
            user.hp = min(user.hp, user.max_hp)
            user.mp = min(user.mp, user.max_mp)

        except Exception as e:
            logger.error(f"Failed to update user stats: {str(e)}")
            raise

    def _get_base_stats(self, user: User) -> Dict:
        """Get user's base stats without equipment"""
        job_config = JOB_CLASSES[user.job_class]
        return {
            'max_hp': job_config['base_hp'] + (job_config['hp_per_level'] * (user.level - 1)),
            'max_mp': job_config['base_mp'] + (job_config['mp_per_level'] * (user.level - 1)),
            'attack': job_config['base_attack'],
            'defense': job_config['base_defense'],
            'magic_attack': job_config.get('base_magic_attack', 0),
            'magic_defense': job_config.get('base_magic_defense', 0)
        }

    def _update_equipment_stats(self, equipment: Equipment) -> None:
        """Update equipment stats based on level"""
        try:
            # Base stat increase per level
            level_bonus = equipment.level * 0.1  # 10% per level
            
            equipment.attack = int(equipment.base_attack * (1 + level_bonus))
            equipment.defense = int(equipment.base_defense * (1 + level_bonus))
            equipment.magic_attack = int(equipment.base_magic_attack * (1 + level_bonus))
            equipment.magic_defense = int(equipment.base_magic_defense * (1 + level_bonus))
            equipment.hp_bonus = int(equipment.base_hp_bonus * (1 + level_bonus))
            equipment.mp_bonus = int(equipment.base_mp_bonus * (1 + level_bonus))

        except Exception as e:
            logger.error(f"Failed to update equipment stats: {str(e)}")
            raise

    def _get_equipment_stats(self, equipment: Equipment) -> Dict:
        """Get equipment stats"""
        return {
            'id': equipment.id,
            'name': equipment.name,
            'grade': equipment.grade,
            'level': equipment.level,
            'durability': equipment.durability,
            'element': equipment.element,
            'attack': equipment.attack,
            'defense': equipment.defense,
            'magic_attack': equipment.magic_attack,
            'magic_defense': equipment.magic_defense,
            'hp_bonus': equipment.hp_bonus,
            'mp_bonus': equipment.mp_bonus,
            'slot': equipment.slot,
            'equipped': equipment.equipped
        }
