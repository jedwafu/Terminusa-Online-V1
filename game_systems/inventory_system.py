from typing import Dict, List, Optional
from datetime import datetime
from models import db, User, Mount, Pet, Item

class InventorySystem:
    def __init__(self):
        pass

    def equip_mount(self, user: User, mount_id: int) -> Dict:
        """Equip a mount for the user"""
        try:
            # Get the mount
            mount = Mount.query.get(mount_id)
            if not mount:
                return {
                    "success": False,
                    "message": "Mount not found"
                }

            # Verify ownership
            if mount.user_id != user.id:
                return {
                    "success": False,
                    "message": "You don't own this mount"
                }

            # Check level requirement
            if user.level < mount.level_requirement:
                return {
                    "success": False,
                    "message": f"Requires level {mount.level_requirement}"
                }

            # Unequip current mount if any
            current_mount = Mount.query.filter_by(
                user_id=user.id,
                is_equipped=True
            ).first()
            
            if current_mount:
                current_mount.is_equipped = False

            # Equip new mount
            mount.is_equipped = True
            db.session.commit()

            return {
                "success": True,
                "message": f"Equipped {mount.name}",
                "mount": mount.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to equip mount: {str(e)}"
            }

    def activate_pet(self, user: User, pet_id: int) -> Dict:
        """Activate a pet for the user"""
        try:
            # Get the pet
            pet = Pet.query.get(pet_id)
            if not pet:
                return {
                    "success": False,
                    "message": "Pet not found"
                }

            # Verify ownership
            if pet.user_id != user.id:
                return {
                    "success": False,
                    "message": "You don't own this pet"
                }

            # Check level requirement
            if user.level < pet.level_requirement:
                return {
                    "success": False,
                    "message": f"Requires level {pet.level_requirement}"
                }

            # Deactivate current pet if any
            current_pet = Pet.query.filter_by(
                user_id=user.id,
                is_active=True
            ).first()
            
            if current_pet:
                current_pet.is_active = False

            # Activate new pet
            pet.is_active = True
            db.session.commit()

            return {
                "success": True,
                "message": f"Activated {pet.name}",
                "pet": pet.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to activate pet: {str(e)}"
            }

    def get_inventory(self, user: User) -> Dict:
        """Get user's complete inventory"""
        try:
            # Get mounts
            mounts = Mount.query.filter_by(user_id=user.id).all()
            equipped_mount = next((m for m in mounts if m.is_equipped), None)

            # Get pets
            pets = Pet.query.filter_by(user_id=user.id).all()
            active_pet = next((p for p in pets if p.is_active), None)

            # Get items
            items = Item.query.filter_by(user_id=user.id).all()

            return {
                "success": True,
                "inventory": {
                    "mounts": [m.to_dict() for m in mounts],
                    "pets": [p.to_dict() for p in pets],
                    "items": [i.to_dict() for i in items],
                    "equipped_mount": equipped_mount.to_dict() if equipped_mount else None,
                    "active_pet": active_pet.to_dict() if active_pet else None
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get inventory: {str(e)}"
            }

    def expand_inventory(self, user: User, amount: int = 10) -> Dict:
        """Expand inventory slots using crystals"""
        try:
            COST_PER_SLOT = 100  # Crystals per slot
            total_cost = COST_PER_SLOT * amount

            if user.crystals < total_cost:
                return {
                    "success": False,
                    "message": f"Insufficient crystals. Need {total_cost} crystals."
                }

            # Deduct crystals
            user.crystals -= total_cost
            
            # Increase inventory slots
            user.inventory_slots += amount
            
            db.session.commit()

            return {
                "success": True,
                "message": f"Added {amount} inventory slots",
                "new_total_slots": user.inventory_slots,
                "crystals_spent": total_cost
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to expand inventory: {str(e)}"
            }

    def get_mount_stats(self, user: User) -> Dict:
        """Get current mount stats and bonuses"""
        try:
            equipped_mount = Mount.query.filter_by(
                user_id=user.id,
                is_equipped=True
            ).first()

            if not equipped_mount:
                return {
                    "success": True,
                    "has_mount": False,
                    "stats": None
                }

            # Calculate effective stats based on mount level and user level
            level_factor = min(user.level / equipped_mount.level_requirement, 2)
            effective_stats = {
                key: int(value * level_factor)
                for key, value in equipped_mount.stats.items()
            }

            return {
                "success": True,
                "has_mount": True,
                "mount": equipped_mount.to_dict(),
                "effective_stats": effective_stats,
                "bonuses": {
                    "damage": effective_stats["speed"] * 0.1,  # 10% of speed adds to damage
                    "hp": effective_stats["stamina"] * 0.1,    # 10% of stamina adds to HP
                    "loot": effective_stats["carrying_capacity"] * 0.001  # 0.1% per point
                }
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get mount stats: {str(e)}"
            }

    def get_pet_abilities(self, user: User) -> Dict:
        """Get current pet abilities and cooldowns"""
        try:
            active_pet = Pet.query.filter_by(
                user_id=user.id,
                is_active=True
            ).first()

            if not active_pet:
                return {
                    "success": True,
                    "has_pet": False,
                    "abilities": None
                }

            # Get ability cooldowns and effects
            abilities = {}
            for ability in active_pet.abilities:
                abilities[ability] = {
                    "ready": active_pet.can_use_ability(ability),
                    "cooldown": active_pet.ability_cooldowns.get(ability),
                    "last_use": active_pet.last_ability_use.get(ability),
                    "effect": active_pet.get_ability_effects(ability)
                }

            return {
                "success": True,
                "has_pet": True,
                "pet": active_pet.to_dict(),
                "abilities": abilities
            }

        except Exception as e:
            return {
                "success": False,
                "message": f"Failed to get pet abilities: {str(e)}"
            }

    def repair_equipment(self, user: User, item_id: int) -> Dict:
        """Repair equipment using crystals"""
        try:
            item = Item.query.get(item_id)
            if not item:
                return {
                    "success": False,
                    "message": "Item not found"
                }

            if item.user_id != user.id:
                return {
                    "success": False,
                    "message": "You don't own this item"
                }

            if item.durability >= 100:
                return {
                    "success": False,
                    "message": "Item doesn't need repair"
                }

            # Calculate repair cost
            durability_loss = 100 - item.durability
            COST_PER_POINT = 10  # Crystals per durability point
            repair_cost = durability_loss * COST_PER_POINT

            if user.crystals < repair_cost:
                return {
                    "success": False,
                    "message": f"Insufficient crystals. Need {repair_cost} crystals."
                }

            # Process repair
            user.crystals -= repair_cost
            item.durability = 100
            db.session.commit()

            return {
                "success": True,
                "message": f"Repaired {item.name}",
                "crystals_spent": repair_cost,
                "item": item.to_dict()
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to repair item: {str(e)}"
            }
