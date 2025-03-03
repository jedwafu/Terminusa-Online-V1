"""
Gate System for Terminusa Online
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import random
import logging
from models import db, User, Gate, Party, Equipment, Item
from game_systems.combat_manager import CombatManager
from game_config import (
    GATE_GRADES,
    ELEMENTS,
    CRYSTAL_TAX_RATE,
    GUILD_CRYSTAL_TAX_RATE,
    ADMIN_USERNAME
)

logger = logging.getLogger(__name__)

class GateSystem:
    def __init__(self):
        self.combat_manager = CombatManager()
        self._admin_user = None
        self.active_gates = {}  # Track active gate instances

    @property
    def admin_user(self):
        """Lazy load admin user"""
        if self._admin_user is None:
            from flask import current_app
            with current_app.app_context():
                self._admin_user = User.query.filter_by(username=ADMIN_USERNAME).first()
        return self._admin_user

    def generate_gate(self, grade: str, location: str) -> Dict:
        """Generate a new gate"""
        try:
            if grade not in GATE_GRADES:
                return {
                    "success": False,
                    "message": "Invalid gate grade"
                }

            gate_config = GATE_GRADES[grade]
            
            # Generate gate properties
            gate = Gate(
                grade=grade,
                location=location,
                level_requirement=gate_config["min_level"],
                element=random.choice(list(ELEMENTS.keys())),
                monster_count=self._calculate_monster_count(grade),
                reward_multiplier=self._calculate_reward_multiplier(grade),
                status="active",
                created_at=datetime.utcnow()
            )
            
            db.session.add(gate)
            db.session.commit()

            # Generate unique gate ID
            gate_instance_id = f"gate_{gate.id}_{datetime.utcnow().timestamp()}"
            
            # Initialize gate instance
            self.active_gates[gate_instance_id] = {
                "gate": gate,
                "current_players": set(),
                "current_parties": set(),
                "monster_kills": 0,
                "start_time": datetime.utcnow()
            }

            return {
                "success": True,
                "message": "Gate generated successfully",
                "gate_id": gate_instance_id,
                "gate_info": self._get_gate_info(gate)
            }

        except Exception as e:
            logger.error(f"Failed to generate gate: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to generate gate"
            }

    def enter_gate(self, user: User, gate_id: str, party: Optional[Party] = None) -> Dict:
        """Enter a gate solo or with party"""
        try:
            gate_instance = self.active_gates.get(gate_id)
            if not gate_instance:
                return {
                    "success": False,
                    "message": "Gate not found"
                }

            gate = gate_instance["gate"]

            # Check level requirement
            if user.level < gate.level_requirement:
                return {
                    "success": False,
                    "message": f"Level {gate.level_requirement} required to enter"
                }

            # Check if user is already in a gate
            if any(user.id in inst["current_players"] 
                  for inst in self.active_gates.values()):
                return {
                    "success": False,
                    "message": "Already in a gate"
                }

            # Check equipment durability
            if not self._check_equipment_durability(user):
                return {
                    "success": False,
                    "message": "Equipment durability too low"
                }

            if party:
                # Party entry checks
                if not self._validate_party_entry(party, gate):
                    return {
                        "success": False,
                        "message": "Party does not meet requirements"
                    }
                
                # Add all party members
                gate_instance["current_parties"].add(party.id)
                for member in party.members:
                    gate_instance["current_players"].add(member.id)
                
                # Start party battle
                battle_result = self.combat_manager.start_gate_battle(gate, party)
                
            else:
                # Solo entry
                gate_instance["current_players"].add(user.id)
                
                # Start solo battle
                battle_result = self.combat_manager.start_gate_battle(gate)

            return {
                "success": True,
                "message": "Entered gate successfully",
                "battle": battle_result
            }

        except Exception as e:
            logger.error(f"Failed to enter gate: {str(e)}")
            return {
                "success": False,
                "message": "Failed to enter gate"
            }

    def process_gate_combat(self, gate_id: str, battle_id: str) -> Dict:
        """Process combat within a gate"""
        try:
            gate_instance = self.active_gates.get(gate_id)
            if not gate_instance:
                return {
                    "success": False,
                    "message": "Gate not found"
                }

            # Process combat round
            combat_result = self.combat_manager.process_combat_round(battle_id)
            
            if not combat_result["success"]:
                return combat_result

            # Check if combat ended
            if "battle_end" in combat_result:
                if combat_result["success"]:
                    # Battle won
                    gate_instance["monster_kills"] += 1
                    
                    # Check if gate is cleared
                    if gate_instance["monster_kills"] >= gate_instance["gate"].monster_count:
                        return self._complete_gate(gate_id)
                else:
                    # Battle lost - handle player death
                    return self._handle_gate_failure(gate_id, combat_result)

            return combat_result

        except Exception as e:
            logger.error(f"Failed to process gate combat: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process gate combat"
            }

    def leave_gate(self, user: User, gate_id: str) -> Dict:
        """Leave a gate"""
        try:
            gate_instance = self.active_gates.get(gate_id)
            if not gate_instance:
                return {
                    "success": False,
                    "message": "Gate not found"
                }

            # Remove user from gate
            if user.id in gate_instance["current_players"]:
                gate_instance["current_players"].remove(user.id)
                
                # If in party, check if whole party should be removed
                for party_id in gate_instance["current_parties"]:
                    party = Party.query.get(party_id)
                    if party and user in party.members:
                        if all(m.id not in gate_instance["current_players"] 
                              for m in party.members):
                            gate_instance["current_parties"].remove(party_id)

            # Clean up empty gate
            if not gate_instance["current_players"]:
                del self.active_gates[gate_id]

            return {
                "success": True,
                "message": "Left gate successfully"
            }

        except Exception as e:
            logger.error(f"Failed to leave gate: {str(e)}")
            return {
                "success": False,
                "message": "Failed to leave gate"
            }

    def _complete_gate(self, gate_id: str) -> Dict:
        """Handle gate completion and rewards"""
        try:
            gate_instance = self.active_gates.get(gate_id)
            if not gate_instance:
                return {
                    "success": False,
                    "message": "Gate not found"
                }

            gate = gate_instance["gate"]
            
            # Calculate rewards
            rewards = self._calculate_gate_rewards(gate)
            
            # Distribute rewards
            if len(gate_instance["current_parties"]) > 0:
                # Party completion
                for party_id in gate_instance["current_parties"]:
                    party = Party.query.get(party_id)
                    if party:
                        self._distribute_party_rewards(party, rewards)
            else:
                # Solo completion
                player_id = next(iter(gate_instance["current_players"]))
                player = User.query.get(player_id)
                if player:
                    self._distribute_solo_rewards(player, rewards)

            # Update gate status
            gate.status = "completed"
            gate.completed_at = datetime.utcnow()
            db.session.commit()

            # Clean up
            del self.active_gates[gate_id]

            return {
                "success": True,
                "message": "Gate completed",
                "rewards": rewards
            }

        except Exception as e:
            logger.error(f"Failed to complete gate: {str(e)}")
            return {
                "success": False,
                "message": "Failed to complete gate"
            }

    def _handle_gate_failure(self, gate_id: str, combat_result: Dict) -> Dict:
        """Handle gate failure and consequences"""
        try:
            gate_instance = self.active_gates.get(gate_id)
            if not gate_instance:
                return {
                    "success": False,
                    "message": "Gate not found"
                }

            # Process player deaths and item drops
            dropped_items = []
            for player_id in gate_instance["current_players"]:
                player = User.query.get(player_id)
                if player:
                    dropped_items.extend(self._process_player_death(player))

            # Update gate status
            gate_instance["gate"].status = "failed"
            gate_instance["gate"].completed_at = datetime.utcnow()
            db.session.commit()

            # Clean up
            del self.active_gates[gate_id]

            return {
                "success": False,
                "message": "Gate failed",
                "dropped_items": dropped_items,
                "combat_result": combat_result
            }

        except Exception as e:
            logger.error(f"Failed to handle gate failure: {str(e)}")
            return {
                "success": False,
                "message": "Failed to handle gate failure"
            }

    def _calculate_monster_count(self, grade: str) -> int:
        """Calculate number of monsters based on gate grade"""
        base_count = {
            'F': 5,
            'E': 8,
            'D': 12,
            'C': 15,
            'B': 20,
            'A': 25,
            'S': 30
        }
        return base_count[grade] + random.randint(-2, 2)

    def _calculate_reward_multiplier(self, grade: str) -> float:
        """Calculate reward multiplier based on gate grade"""
        return 1.0 + (ord(grade) - ord('F')) * 0.5

    def _calculate_gate_rewards(self, gate: Gate) -> Dict:
        """Calculate rewards for gate completion"""
        grade_config = GATE_GRADES[gate.grade]
        
        # Base crystal reward
        base_crystals = random.randint(
            grade_config["crystal_reward_range"][0],
            grade_config["crystal_reward_range"][1]
        )
        crystals = int(base_crystals * gate.reward_multiplier)
        
        # Equipment drops
        equipment_drops = []
        for _ in range(self._calculate_equipment_drops(gate)):
            if random.random() < grade_config["equipment_drop_rate"]:
                equipment_drops.append(self._generate_equipment_drop(gate))

        return {
            "crystals": crystals,
            "equipment": equipment_drops
        }

    def _calculate_equipment_drops(self, gate: Gate) -> int:
        """Calculate number of equipment drops"""
        base_drops = {
            'F': 1,
            'E': 1,
            'D': 2,
            'C': 2,
            'B': 3,
            'A': 3,
            'S': 4
        }
        return base_drops[gate.grade]

    def _generate_equipment_drop(self, gate: Gate) -> Dict:
        """Generate equipment drop based on gate grade"""
        # This would be implemented based on your equipment system
        pass

    def _distribute_solo_rewards(self, player: User, rewards: Dict) -> None:
        """Distribute rewards to solo player"""
        try:
            # Calculate taxes
            tax_rate = CRYSTAL_TAX_RATE
            if player.guild_id:
                tax_rate += GUILD_CRYSTAL_TAX_RATE
            
            tax_amount = int(rewards["crystals"] * tax_rate)
            net_crystals = rewards["crystals"] - tax_amount

            # Add crystals
            player.crystals += net_crystals
            if self.admin_user:
                self.admin_user.crystals += tax_amount

            # Add equipment
            for equipment in rewards["equipment"]:
                self._add_equipment_to_inventory(player, equipment)

            db.session.commit()

        except Exception as e:
            logger.error(f"Failed to distribute solo rewards: {str(e)}")
            db.session.rollback()

    def _distribute_party_rewards(self, party: Party, rewards: Dict) -> None:
        """Distribute rewards to party members"""
        try:
            member_count = len(party.members)
            
            # Calculate individual shares
            crystal_share = rewards["crystals"] // member_count
            
            for member in party.members:
                # Calculate taxes
                tax_rate = CRYSTAL_TAX_RATE
                if member.guild_id:
                    tax_rate += GUILD_CRYSTAL_TAX_RATE
                
                tax_amount = int(crystal_share * tax_rate)
                net_crystals = crystal_share - tax_amount

                # Add crystals
                member.crystals += net_crystals
                if self.admin_user:
                    self.admin_user.crystals += tax_amount

            # Randomly distribute equipment
            for equipment in rewards["equipment"]:
                lucky_member = random.choice(party.members)
                self._add_equipment_to_inventory(lucky_member, equipment)

            db.session.commit()

        except Exception as e:
            logger.error(f"Failed to distribute party rewards: {str(e)}")
            db.session.rollback()

    def _process_player_death(self, player: User) -> List[Dict]:
        """Process player death and drop items"""
        dropped_items = []
        
        try:
            # Drop some crystals
            if player.crystals > 0:
                drop_amount = int(player.crystals * 0.1)  # Drop 10%
                player.crystals -= drop_amount
                dropped_items.append({
                    "type": "currency",
                    "currency": "crystals",
                    "amount": drop_amount
                })

            # Drop some inventory items
            inventory_items = Item.query.filter_by(user_id=player.id).all()
            for item in inventory_items:
                if random.random() < 0.1:  # 10% chance to drop each item
                    drop_quantity = random.randint(1, item.quantity)
                    item.quantity -= drop_quantity
                    
                    dropped_items.append({
                        "type": "item",
                        "item_id": item.id,
                        "quantity": drop_quantity
                    })
                    
                    if item.quantity <= 0:
                        db.session.delete(item)

            db.session.commit()
            return dropped_items

        except Exception as e:
            logger.error(f"Failed to process player death: {str(e)}")
            db.session.rollback()
            return []

    def _validate_party_entry(self, party: Party, gate: Gate) -> bool:
        """Validate if party can enter gate"""
        # Check if all members meet level requirement
        if not all(m.level >= gate.level_requirement for m in party.members):
            return False
            
        # Check if any member is already in a gate
        if any(any(m.id in inst["current_players"] 
                  for inst in self.active_gates.values())
               for m in party.members):
            return False
            
        # Check equipment durability for all members
        if not all(self._check_equipment_durability(m) for m in party.members):
            return False
            
        return True

    def _check_equipment_durability(self, user: User) -> bool:
        """Check if user's equipment has sufficient durability"""
        equipped_items = Equipment.query.filter_by(
            user_id=user.id,
            equipped=True
        ).all()
        
        return all(item.durability > 0 for item in equipped_items)

    def _add_equipment_to_inventory(self, player: User, equipment: Dict) -> None:
        """Add equipment to player's inventory"""
        # This would be implemented based on your equipment system
        pass

    def _get_gate_info(self, gate: Gate) -> Dict:
        """Get gate information"""
        return {
            "id": gate.id,
            "grade": gate.grade,
            "location": gate.location,
            "level_requirement": gate.level_requirement,
            "element": gate.element,
            "monster_count": gate.monster_count,
            "reward_multiplier": float(gate.reward_multiplier),
            "status": gate.status,
            "created_at": gate.created_at.isoformat(),
            "completed_at": gate.completed_at.isoformat() if gate.completed_at else None
        }
