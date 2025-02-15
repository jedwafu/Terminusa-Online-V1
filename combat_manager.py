from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import random
import math

@dataclass
class CombatStats:
    hp: int
    mp: int
    strength: int
    agility: int
    intelligence: int
    luck: int
    level: int
    job_class: str

@dataclass
class CombatResult:
    success: bool
    survivors: List[str]
    deaths: List[str]
    rewards: Dict
    experience: int
    duration: int  # in seconds
    damage_taken: Dict[str, int]
    mana_used: Dict[str, int]

class CombatSystem:
    def __init__(self, skill_system, durability_system):
        self.skill_system = skill_system
        self.durability_system = durability_system
        self.combat_modifiers = {
            'solo': {
                'damage': 1.5,      # Solo players deal 50% more damage
                'defense': 1.3,     # Solo players take 30% less damage
                'rewards': 2.0      # Solo players get double rewards
            },
            'party': {
                'damage': 1.0,
                'defense': 1.0,
                'rewards': 1.0
            }
        }

    def calculate_combat_power(self, stats: CombatStats) -> float:
        """Calculate combat power based on stats"""
        base_power = (
            stats.strength * 1.5 +
            stats.agility * 1.2 +
            stats.intelligence * 1.3 +
            stats.luck * 0.5
        )
        
        # Apply job class modifiers
        class_modifiers = {
            'Fighter': {'strength': 1.3, 'hp': 1.2},
            'Mage': {'intelligence': 1.3, 'mp': 1.2},
            'Assassin': {'agility': 1.3, 'luck': 1.2},
            'Archer': {'agility': 1.2, 'luck': 1.3},
            'Healer': {'intelligence': 1.2, 'mp': 1.3},
            'Shadow Monarch': {'all': 2.0}  # All stats doubled
        }
        
        if stats.job_class in class_modifiers:
            mods = class_modifiers[stats.job_class]
            if 'all' in mods:
                base_power *= mods['all']
            else:
                for stat, mod in mods.items():
                    if hasattr(stats, stat):
                        base_power += getattr(stats, stat) * (mod - 1)
        
        # Level scaling
        level_scaling = 1 + (stats.level * 0.1)
        
        return base_power * level_scaling

    def calculate_monster_power(self, monster: Dict) -> float:
        """Calculate monster combat power"""
        base_power = monster['level'] * 10
        
        # Apply type multipliers
        type_multipliers = {
            'normal': 1.0,
            'elite': 2.0,
            'boss': 5.0,
            'monarch': 10.0
        }
        
        power = base_power * type_multipliers[monster['type']]
        
        # Apply monster-specific multipliers
        power *= monster.get('hp_multiplier', 1.0)
        power *= monster.get('damage_multiplier', 1.0)
        
        return power

    def simulate_solo_combat(self, player_stats: CombatStats, monsters: List[Dict]) -> CombatResult:
        """Simulate solo combat in a gate"""
        start_time = datetime.utcnow()
        
        # Calculate initial combat powers
        player_power = self.calculate_combat_power(player_stats)
        player_power *= self.combat_modifiers['solo']['damage']
        
        total_monster_power = sum(self.calculate_monster_power(m) for m in monsters)
        
        # Track combat stats
        damage_taken = {'player': 0}
        mana_used = {'player': 0}
        player_hp = player_stats.hp
        player_mp = player_stats.mp
        
        # Simulate combat rounds
        round_count = 0
        max_rounds = 100  # Prevent infinite loops
        
        while round_count < max_rounds:
            round_count += 1
            
            # Player attacks
            damage_dealt = player_power * random.uniform(0.8, 1.2)
            total_monster_power -= damage_dealt
            
            # Monster attacks
            if total_monster_power > 0:
                monster_damage = (total_monster_power / len(monsters)) * random.uniform(0.8, 1.2)
                monster_damage /= self.combat_modifiers['solo']['defense']
                player_hp -= monster_damage
                damage_taken['player'] += monster_damage
            
            # Use MP for skills
            mp_cost = random.randint(10, 30)  # Simulate skill usage
            if player_mp >= mp_cost:
                player_mp -= mp_cost
                mana_used['player'] += mp_cost
            
            # Check win/loss conditions
            if total_monster_power <= 0:
                success = True
                break
            if player_hp <= 0:
                success = False
                break
        
        # Calculate rewards
        base_rewards = {
            'crystals': sum(random.randint(10, 50) for _ in monsters),
            'experience': sum(m['level'] * 100 for m in monsters)
        }
        
        # Apply solo modifier to rewards
        rewards = {
            'crystals': int(base_rewards['crystals'] * self.combat_modifiers['solo']['rewards']),
            'experience': int(base_rewards['experience'] * self.combat_modifiers['solo']['rewards'])
        }
        
        duration = (datetime.utcnow() - start_time).seconds
        
        return CombatResult(
            success=success,
            survivors=['player'] if player_hp > 0 else [],
            deaths=['player'] if player_hp <= 0 else [],
            rewards=rewards,
            experience=rewards['experience'],
            duration=duration,
            damage_taken=damage_taken,
            mana_used=mana_used
        )

    def simulate_party_combat(self, party_stats: List[CombatStats], monsters: List[Dict]) -> CombatResult:
        """Simulate party combat in a gate"""
        start_time = datetime.utcnow()
        
        # Calculate initial combat powers
        party_powers = {
            f'player_{i}': self.calculate_combat_power(stats)
            for i, stats in enumerate(party_stats)
        }
        
        total_monster_power = sum(self.calculate_monster_power(m) for m in monsters)
        
        # Track combat stats
        damage_taken = {f'player_{i}': 0 for i in range(len(party_stats))}
        mana_used = {f'player_{i}': 0 for i in range(len(party_stats))}
        player_hp = {f'player_{i}': stats.hp for i, stats in enumerate(party_stats)}
        player_mp = {f'player_{i}': stats.mp for i, stats in enumerate(party_stats)}
        
        # Track healers for party healing
        healers = [
            i for i, stats in enumerate(party_stats)
            if stats.job_class == 'Healer'
        ]
        
        # Simulate combat rounds
        round_count = 0
        max_rounds = 100  # Prevent infinite loops
        
        while round_count < max_rounds:
            round_count += 1
            
            # Party attacks
            for player_id, power in party_powers.items():
                if player_hp[player_id] > 0:  # Only alive players can attack
                    damage_dealt = power * random.uniform(0.8, 1.2)
                    total_monster_power -= damage_dealt
            
            # Monster attacks
            if total_monster_power > 0:
                # Distribute monster damage among living players
                living_players = [pid for pid, hp in player_hp.items() if hp > 0]
                if living_players:
                    monster_damage_per_player = (total_monster_power / len(monsters) / len(living_players))
                    for player_id in living_players:
                        damage = monster_damage_per_player * random.uniform(0.8, 1.2)
                        player_hp[player_id] -= damage
                        damage_taken[player_id] += damage
            
            # Healer actions
            for healer_idx in healers:
                healer_id = f'player_{healer_idx}'
                if player_hp[healer_id] > 0:  # Only alive healers can heal
                    if player_mp[healer_id] >= 50:  # Healing cost
                        # Heal most damaged player
                        most_damaged = max(
                            [(pid, 1 - hp/party_stats[int(pid.split('_')[1])].hp)
                             for pid, hp in player_hp.items() if hp > 0],
                            key=lambda x: x[1]
                        )[0]
                        
                        heal_amount = party_stats[healer_idx].intelligence * 2
                        player_hp[most_damaged] = min(
                            player_hp[most_damaged] + heal_amount,
                            party_stats[int(most_damaged.split('_')[1])].hp
                        )
                        player_mp[healer_id] -= 50
                        mana_used[healer_id] += 50
            
            # Use MP for skills
            for player_id, mp in player_mp.items():
                if player_hp[player_id] > 0:  # Only alive players use skills
                    mp_cost = random.randint(10, 30)  # Simulate skill usage
                    if mp >= mp_cost:
                        player_mp[player_id] -= mp_cost
                        mana_used[player_id] += mp_cost
            
            # Check win/loss conditions
            if total_monster_power <= 0:
                success = True
                break
            if all(hp <= 0 for hp in player_hp.values()):
                success = False
                break
        
        # Calculate rewards
        base_rewards = {
            'crystals': sum(random.randint(10, 50) for _ in monsters),
            'experience': sum(m['level'] * 100 for m in monsters)
        }
        
        # Distribute rewards among survivors
        survivors = [pid for pid, hp in player_hp.items() if hp > 0]
        if survivors:
            reward_per_player = {
                'crystals': int(base_rewards['crystals'] / len(survivors)),
                'experience': int(base_rewards['experience'] / len(survivors))
            }
        else:
            reward_per_player = {'crystals': 0, 'experience': 0}
        
        duration = (datetime.utcnow() - start_time).seconds
        
        return CombatResult(
            success=success,
            survivors=survivors,
            deaths=[pid for pid, hp in player_hp.items() if hp <= 0],
            rewards=reward_per_player,
            experience=reward_per_player['experience'],
            duration=duration,
            damage_taken=damage_taken,
            mana_used=mana_used
        )

    def process_combat_results(self, result: CombatResult, players: List[Dict], equipment: Dict[str, List[Dict]]) -> Dict:
        """Process combat results including durability loss and rewards distribution"""
        processed_results = {
            'success': result.success,
            'survivors': result.survivors,
            'deaths': result.deaths,
            'rewards': {},
            'equipment_updates': {},
            'status_updates': {}
        }
        
        # Process each player's results
        for i, player in enumerate(players):
            player_id = f'player_{i}'
            
            # Calculate durability loss for equipment
            if player_id in equipment:
                for item in equipment[player_id]:
                    updated_item = self.durability_system.apply_durability_loss(
                        item,
                        result.damage_taken.get(player_id, 0),
                        result.mana_used.get(player_id, 0),
                        result.duration // 60  # Convert seconds to minutes
                    )
                    if player_id not in processed_results['equipment_updates']:
                        processed_results['equipment_updates'][player_id] = []
                    processed_results['equipment_updates'][player_id].append(updated_item)
            
            # Distribute rewards to survivors
            if player_id in result.survivors:
                processed_results['rewards'][player_id] = {
                    'crystals': result.rewards['crystals'],
                    'experience': result.experience
                }
            else:
                processed_results['rewards'][player_id] = {
                    'crystals': 0,
                    'experience': 0
                }
            
            # Update player status
            processed_results['status_updates'][player_id] = {
                'is_dead': player_id in result.deaths,
                'damage_taken': result.damage_taken.get(player_id, 0),
                'mana_used': result.mana_used.get(player_id, 0)
            }
        
        return processed_results
