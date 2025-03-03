"""
Combat Manager for Terminusa Online
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime
import random
import logging
from models import db, User, Item, Gate, Party, Equipment
from game_config import (
    ELEMENTS, ELEMENT_DAMAGE_BONUS, ELEMENT_DAMAGE_PENALTY,
    STATUS_EFFECTS, GATE_GRADES, PARTY_CONFIG, DURABILITY_CONFIG
)

logger = logging.getLogger(__name__)

class CombatManager:
    def __init__(self):
        self.active_battles = {}  # Track ongoing battles

    def start_gate_battle(self, gate: Gate, party: Optional[Party] = None) -> Dict:
        """Start a battle in a gate"""
        try:
            if party:
                return self._start_party_battle(gate, party)
            else:
                return self._start_solo_battle(gate)
        except Exception as e:
            logger.error(f"Failed to start battle: {str(e)}")
            return {
                "success": False,
                "message": "Failed to start battle"
            }

    def _start_solo_battle(self, gate: Gate) -> Dict:
        """Initialize a solo battle"""
        try:
            player = gate.current_players[0]
            battle_id = f"solo_{gate.id}_{datetime.utcnow().timestamp()}"
            
            # Initialize battle state
            battle_state = {
                "id": battle_id,
                "gate": gate,
                "player": player,
                "start_time": datetime.utcnow(),
                "round": 0,
                "player_state": self._initialize_player_state(player),
                "monster_state": self._generate_monster_state(gate),
                "status_effects": {},
                "combat_log": []
            }
            
            self.active_battles[battle_id] = battle_state
            
            return {
                "success": True,
                "message": "Solo battle started",
                "battle_id": battle_id,
                "initial_state": self._get_battle_state(battle_id)
            }
        except Exception as e:
            logger.error(f"Failed to start solo battle: {str(e)}")
            return {
                "success": False,
                "message": "Failed to start solo battle"
            }

    def _start_party_battle(self, gate: Gate, party: Party) -> Dict:
        """Initialize a party battle"""
        try:
            battle_id = f"party_{gate.id}_{datetime.utcnow().timestamp()}"
            
            # Initialize battle state
            battle_state = {
                "id": battle_id,
                "gate": gate,
                "party": party,
                "start_time": datetime.utcnow(),
                "round": 0,
                "player_states": {
                    player.id: self._initialize_player_state(player)
                    for player in party.members
                },
                "monster_state": self._generate_monster_state(gate),
                "status_effects": {},
                "combat_log": []
            }
            
            self.active_battles[battle_id] = battle_state
            
            return {
                "success": True,
                "message": "Party battle started",
                "battle_id": battle_id,
                "initial_state": self._get_battle_state(battle_id)
            }
        except Exception as e:
            logger.error(f"Failed to start party battle: {str(e)}")
            return {
                "success": False,
                "message": "Failed to start party battle"
            }

    def process_combat_round(self, battle_id: str) -> Dict:
        """Process one round of combat"""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return {
                "success": False,
                "message": "Battle not found"
            }

        try:
            # Process status effects
            self._process_status_effects(battle)
            
            # Process player/party actions
            if "party" in battle:
                combat_results = self._process_party_round(battle)
            else:
                combat_results = self._process_solo_round(battle)
            
            # Update equipment durability
            self._update_equipment_durability(battle)
            
            # Check battle end conditions
            if self._check_battle_end(battle):
                return self._end_battle(battle)
            
            battle["round"] += 1
            
            return {
                "success": True,
                "message": "Combat round processed",
                "results": combat_results,
                "state": self._get_battle_state(battle_id)
            }
        except Exception as e:
            logger.error(f"Failed to process combat round: {str(e)}")
            return {
                "success": False,
                "message": "Failed to process combat round"
            }

    def _process_solo_round(self, battle: Dict) -> Dict:
        """Process a round of solo combat"""
        player_state = battle["player_state"]
        monster_state = battle["monster_state"]
        
        # Player turn
        if not self._is_player_incapacitated(player_state):
            damage, effects = self._calculate_damage(player_state, monster_state)
            monster_state["hp"] -= damage
            self._apply_status_effects(monster_state, effects)
            
            battle["combat_log"].append({
                "round": battle["round"],
                "actor": "player",
                "action": "attack",
                "damage": damage,
                "effects": effects
            })
        
        # Monster turn
        if monster_state["hp"] > 0:
            damage, effects = self._calculate_damage(monster_state, player_state)
            player_state["hp"] -= damage
            self._apply_status_effects(player_state, effects)
            
            battle["combat_log"].append({
                "round": battle["round"],
                "actor": "monster",
                "action": "attack",
                "damage": damage,
                "effects": effects
            })
        
        return {
            "player_damage_dealt": damage,
            "player_damage_taken": damage,
            "effects_applied": effects
        }

    def _process_party_round(self, battle: Dict) -> Dict:
        """Process a round of party combat"""
        results = {
            "damages_dealt": {},
            "damages_taken": {},
            "effects_applied": {}
        }
        
        # Party members' turns
        for player_id, player_state in battle["player_states"].items():
            if not self._is_player_incapacitated(player_state):
                # Handle different actions based on role
                if player_state["job_class"] == "Healer":
                    healing = self._process_healer_action(player_state, battle["player_states"])
                    results["healing"] = healing
                else:
                    damage, effects = self._calculate_damage(player_state, battle["monster_state"])
                    battle["monster_state"]["hp"] -= damage
                    self._apply_status_effects(battle["monster_state"], effects)
                    
                    results["damages_dealt"][player_id] = damage
                    results["effects_applied"][player_id] = effects
                    
                    battle["combat_log"].append({
                        "round": battle["round"],
                        "actor": f"player_{player_id}",
                        "action": "attack",
                        "damage": damage,
                        "effects": effects
                    })
        
        # Monster turn
        if battle["monster_state"]["hp"] > 0:
            # Monster targets random non-incapacitated player
            valid_targets = [
                pid for pid, pstate in battle["player_states"].items()
                if not self._is_player_incapacitated(pstate)
            ]
            
            if valid_targets:
                target_id = random.choice(valid_targets)
                damage, effects = self._calculate_damage(
                    battle["monster_state"],
                    battle["player_states"][target_id]
                )
                battle["player_states"][target_id]["hp"] -= damage
                self._apply_status_effects(battle["player_states"][target_id], effects)
                
                results["damages_taken"][target_id] = damage
                results["effects_applied"][target_id].update(effects)
                
                battle["combat_log"].append({
                    "round": battle["round"],
                    "actor": "monster",
                    "action": "attack",
                    "target": target_id,
                    "damage": damage,
                    "effects": effects
                })
        
        return results

    def _process_healer_action(self, healer_state: Dict, party_states: Dict) -> Dict:
        """Process healer's action - healing or MP restoration"""
        healing_results = {}
        
        # Find most damaged party member
        most_damaged = min(
            party_states.items(),
            key=lambda x: x[1]["hp"] / x[1]["max_hp"]
        )
        
        # Calculate healing amount (based on healer's stats)
        heal_amount = (
            healer_state["magic_attack"] * 1.5 +
            random.randint(10, 20)
        )
        
        # Apply healing
        target_state = party_states[most_damaged[0]]
        old_hp = target_state["hp"]
        target_state["hp"] = min(
            target_state["hp"] + heal_amount,
            target_state["max_hp"]
        )
        actual_healing = target_state["hp"] - old_hp
        
        healing_results[most_damaged[0]] = actual_healing
        
        # Consume MP
        healer_state["mp"] -= 20  # Example MP cost
        
        return healing_results

    def _calculate_damage(self, attacker: Dict, defender: Dict) -> Tuple[int, Dict]:
        """Calculate damage and status effects"""
        # Base damage calculation
        base_damage = (
            attacker.get("attack", 10) * 
            (1 - (defender.get("defense", 0) / 100))
        )
        
        # Element modification
        element_mod = self._calculate_element_modifier(
            attacker.get("element", "neutral"),
            defender.get("element", "neutral")
        )
        
        # Status effects chance
        effects = {}
        for effect, chance in attacker.get("status_effects", {}).items():
            if random.random() < chance:
                effects[effect] = STATUS_EFFECTS[effect].copy()
        
        # Critical hit chance (20% chance for 1.5x damage)
        crit_multiplier = 1.5 if random.random() < 0.2 else 1.0
        
        final_damage = int(base_damage * element_mod * crit_multiplier)
        
        return final_damage, effects

    def _calculate_element_modifier(self, attacker_element: str, defender_element: str) -> float:
        """Calculate elemental damage modifier"""
        if attacker_element == "neutral" or defender_element == "neutral":
            return 1.0
            
        element_info = ELEMENTS[attacker_element]
        
        if defender_element in element_info["strengths"]:
            return 1 + float(ELEMENT_DAMAGE_BONUS)
        elif defender_element in element_info["weaknesses"]:
            return 1 - float(ELEMENT_DAMAGE_PENALTY)
            
        return 1.0

    def _process_status_effects(self, battle: Dict) -> None:
        """Process ongoing status effects"""
        states_to_process = (
            [battle["player_state"]]
            if "player_state" in battle
            else list(battle["player_states"].values())
        )
        states_to_process.append(battle["monster_state"])
        
        for state in states_to_process:
            effects_to_remove = []
            
            for effect, data in state.get("status_effects", {}).items():
                # Apply effect
                if effect == "burn":
                    state["hp"] -= data["damage_per_turn"]
                elif effect == "poisoned":
                    state["hp"] -= data["damage_per_turn"]
                
                # Reduce duration
                if data["duration"] > 0:
                    data["duration"] -= 1
                    if data["duration"] == 0:
                        effects_to_remove.append(effect)
            
            # Remove expired effects
            for effect in effects_to_remove:
                del state["status_effects"][effect]

    def _update_equipment_durability(self, battle: Dict) -> None:
        """Update equipment durability based on battle actions"""
        if "party" in battle:
            players = battle["party"].members
        else:
            players = [battle["player"]]
        
        for player in players:
            equipped_items = Equipment.query.filter_by(user_id=player.id, equipped=True).all()
            
            for item in equipped_items:
                # Calculate durability loss
                hp_loss = (
                    (player.max_hp - player.hp) / player.max_hp *
                    DURABILITY_CONFIG["damage_loss_rate"]
                )
                mp_loss = (
                    (player.max_mp - player.mp) / player.max_mp *
                    DURABILITY_CONFIG["mana_loss_rate"]
                )
                time_loss = (
                    (datetime.utcnow() - battle["start_time"]).seconds / 60 *
                    DURABILITY_CONFIG["time_loss_rate"]
                )
                
                total_loss = hp_loss + mp_loss + time_loss
                
                # Update durability
                item.durability = max(0, item.durability - total_loss)
                
                # Break item if durability reaches 0
                if item.durability == 0:
                    item.equipped = False
                    
            db.session.commit()

    def _check_battle_end(self, battle: Dict) -> bool:
        """Check if battle should end"""
        # Check monster defeat
        if battle["monster_state"]["hp"] <= 0:
            return True
            
        # Check player/party defeat
        if "party" in battle:
            return all(
                self._is_player_defeated(pstate)
                for pstate in battle["player_states"].values()
            )
        else:
            return self._is_player_defeated(battle["player_state"])

    def _end_battle(self, battle: Dict) -> Dict:
        """Handle battle end and rewards"""
        try:
            monster_defeated = battle["monster_state"]["hp"] <= 0
            
            if monster_defeated:
                rewards = self._calculate_rewards(battle)
                self._distribute_rewards(battle, rewards)
                
                result = {
                    "success": True,
                    "message": "Battle won",
                    "rewards": rewards
                }
            else:
                result = {
                    "success": False,
                    "message": "Battle lost",
                    "rewards": None
                }
            
            # Cleanup
            battle_id = battle["id"]
            del self.active_battles[battle_id]
            
            return result
            
        except Exception as e:
            logger.error(f"Failed to end battle: {str(e)}")
            return {
                "success": False,
                "message": "Failed to end battle"
            }

    def _calculate_rewards(self, battle: Dict) -> Dict:
        """Calculate battle rewards"""
        gate_grade = battle["gate"].grade
        grade_config = GATE_GRADES[gate_grade]
        
        # Base crystal reward
        crystal_reward = random.randint(
            grade_config["crystal_reward_range"][0],
            grade_config["crystal_reward_range"][1]
        )
        
        # Equipment drops
        equipment_drops = []
        if random.random() < grade_config["equipment_drop_rate"]:
            # Generate equipment drop based on gate grade
            equipment_drops.append(self._generate_equipment_drop(gate_grade))
        
        return {
            "crystals": crystal_reward,
            "equipment": equipment_drops
        }

    def _distribute_rewards(self, battle: Dict, rewards: Dict) -> None:
        """Distribute rewards to players"""
        if "party" in battle:
            # Calculate individual shares
            member_count = len(battle["party"].members)
            share_multiplier = PARTY_CONFIG["reward_scaling"].get(
                member_count,
                PARTY_CONFIG["reward_scaling"][10]  # Use 10+ scaling for larger parties
            )
            
            crystal_share = int(rewards["crystals"] * share_multiplier)
            
            # Distribute to each member
            for player in battle["party"].members:
                player.crystals += crystal_share
                
            # Randomly distribute equipment to party members
            for equipment in rewards["equipment"]:
                lucky_player = random.choice(battle["party"].members)
                self._add_equipment_to_inventory(lucky_player, equipment)
        else:
            # Solo player gets full rewards
            player = battle["player"]
            player.crystals += rewards["crystals"]
            
            for equipment in rewards["equipment"]:
                self._add_equipment_to_inventory(player, equipment)
        
        db.session.commit()

    def _generate_equipment_drop(self, gate_grade: str) -> Dict:
        """Generate equipment drop based on gate grade"""
        # Implementation would generate appropriate level/quality equipment
        # based on the gate grade
        pass

    def _add_equipment_to_inventory(self, player: User, equipment: Dict) -> None:
        """Add equipment to player's inventory"""
        # Implementation would create and add the equipment to inventory
        pass

    def _initialize_player_state(self, player: User) -> Dict:
        """Initialize player state for battle"""
        return {
            "hp": player.hp,
            "max_hp": player.max_hp,
            "mp": player.mp,
            "max_mp": player.max_mp,
            "attack": player.attack,
            "defense": player.defense,
            "magic_attack": player.magic_attack,
            "magic_defense": player.magic_defense,
            "job_class": player.job_class,
            "element": player.element,
            "status_effects": {},
            "equipment": self._get_player_equipment(player)
        }

    def _generate_monster_state(self, gate: Gate) -> Dict:
        """Generate monster state based on gate grade"""
        grade_config = GATE_GRADES[gate.grade]
        level_range = (grade_config["min_level"], grade_config["max_level"])
        
        level = random.randint(level_range[0], level_range[1])
        
        # Scale monster stats based on level and grade
        return {
            "hp": 100 * level * (ord(gate.grade) - ord('F') + 1),
            "max_hp": 100 * level * (ord(gate.grade) - ord('F') + 1),
            "attack": 10 * level * (ord(gate.grade) - ord('F') + 1),
            "defense": 5 * level * (ord(gate.grade) - ord('F') + 1),
            "element": random.choice(list(ELEMENTS.keys())),
            "status_effects": {},
            "level": level
        }

    def _get_player_equipment(self, player: User) -> Dict:
        """Get player's equipped items"""
        equipped_items = Equipment.query.filter_by(
            user_id=player.id,
            equipped=True
        ).all()
        
        return {
            item.slot: {
                "id": item.id,
                "name": item.name,
                "durability": item.durability,
                "element": item.element
            }
            for item in equipped_items
        }

    def _is_player_incapacitated(self, player_state: Dict) -> bool:
        """Check if player is incapacitated by status effects"""
        status_effects = player_state.get("status_effects", {})
        return (
            "shadow" in status_effects or
            "decapitated" in status_effects or
            player_state["hp"] <= 0
        )

    def _is_player_defeated(self, player_state: Dict) -> bool:
        """Check if player is defeated"""
        return player_state["hp"] <= 0

    def _get_battle_state(self, battle_id: str) -> Dict:
        """Get current battle state"""
        battle = self.active_battles.get(battle_id)
        if not battle:
            return None
            
        return {
            "id": battle["id"],
            "round": battle["round"],
            "monster_state": battle["monster_state"],
            "player_states": (
                battle["player_states"]
                if "party" in battle
                else {"solo": battle["player_state"]}
            ),
            "combat_log": battle["combat_log"][-5:]  # Last 5 rounds
        }
