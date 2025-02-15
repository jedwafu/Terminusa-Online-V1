from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from datetime import datetime
import math
import json

@dataclass
class LevelInfo:
    level: int
    experience_required: int
    stat_points: int
    skill_points: int

@dataclass
class Achievement:
    id: int
    name: str
    description: str
    requirements: Dict
    reward_crystals: int
    bonus_stats: Dict[str, int]
    tier: int  # 1-5, higher tier = harder to achieve

class ProgressionManager:
    def __init__(self):
        self.max_level = 999
        self.base_exp_required = 1000  # Base exp for level 1->2
        self.exp_scaling = 1.2  # Each level requires 20% more exp
        self.achievements = self._initialize_achievements()
        
    def _initialize_achievements(self) -> Dict[int, Achievement]:
        achievements = {}
        
        # Gate hunting achievements
        achievements[1] = Achievement(
            id=1,
            name="Gate Novice",
            description="Clear your first gate",
            requirements={'gates_cleared': 1},
            reward_crystals=100,
            bonus_stats={'strength': 1},
            tier=1
        )
        
        achievements[2] = Achievement(
            id=2,
            name="Gate Expert",
            description="Clear 100 gates",
            requirements={'gates_cleared': 100},
            reward_crystals=1000,
            bonus_stats={'strength': 5, 'agility': 5},
            tier=3
        )
        
        achievements[3] = Achievement(
            id=3,
            name="Gate Master",
            description="Clear 1000 gates",
            requirements={'gates_cleared': 1000},
            reward_crystals=10000,
            bonus_stats={'all': 10},
            tier=5
        )
        
        # Combat achievements
        achievements[4] = Achievement(
            id=4,
            name="Beast Hunter",
            description="Defeat 1000 magic beasts",
            requirements={'beasts_defeated': 1000},
            reward_crystals=500,
            bonus_stats={'strength': 3, 'agility': 3},
            tier=2
        )
        
        achievements[5] = Achievement(
            id=5,
            name="Boss Slayer",
            description="Defeat 100 boss monsters",
            requirements={'bosses_defeated': 100},
            reward_crystals=2000,
            bonus_stats={'strength': 7, 'hp': 100},
            tier=4
        )
        
        # Class achievements
        achievements[6] = Achievement(
            id=6,
            name="Class Master",
            description="Reach max level with any class",
            requirements={'class_level': 50},
            reward_crystals=1500,
            bonus_stats={'all': 5},
            tier=3
        )
        
        achievements[7] = Achievement(
            id=7,
            name="Shadow Monarch",
            description="Achieve the Shadow Monarch class",
            requirements={'class': 'Shadow Monarch'},
            reward_crystals=5000,
            bonus_stats={'all': 15},
            tier=5
        )
        
        # Economy achievements
        achievements[8] = Achievement(
            id=8,
            name="Merchant",
            description="Complete 100 marketplace transactions",
            requirements={'market_transactions': 100},
            reward_crystals=300,
            bonus_stats={'luck': 3},
            tier=2
        )
        
        achievements[9] = Achievement(
            id=9,
            name="Crystal Millionaire",
            description="Accumulate 1,000,000 crystals",
            requirements={'crystals_earned': 1000000},
            reward_crystals=10000,
            bonus_stats={'luck': 10},
            tier=4
        )
        
        return achievements

    def calculate_level_info(self, level: int) -> LevelInfo:
        """Calculate experience and points for a given level"""
        if level < 1 or level > self.max_level:
            raise ValueError(f"Level must be between 1 and {self.max_level}")
        
        # Calculate required experience
        exp_required = int(self.base_exp_required * (math.pow(self.exp_scaling, level - 1)))
        
        # Calculate stat points
        # Every level gives 3 points, every 10th level gives 5 bonus points
        stat_points = (level - 1) * 3
        bonus_levels = (level - 1) // 10
        stat_points += bonus_levels * 5
        
        # Calculate skill points
        # Every level gives 1 point, every 5th level gives 1 bonus point
        skill_points = (level - 1)
        bonus_skill_levels = (level - 1) // 5
        skill_points += bonus_skill_levels
        
        return LevelInfo(
            level=level,
            experience_required=exp_required,
            stat_points=stat_points,
            skill_points=skill_points
        )

    def calculate_level_from_exp(self, total_exp: int) -> Tuple[int, int]:
        """Calculate level and remaining exp from total exp"""
        level = 1
        exp_for_next = self.base_exp_required
        
        while total_exp >= exp_for_next and level < self.max_level:
            total_exp -= exp_for_next
            level += 1
            exp_for_next = int(self.base_exp_required * (math.pow(self.exp_scaling, level - 1)))
        
        return level, total_exp

    def check_achievements(self, user_stats: Dict) -> List[Achievement]:
        """Check which achievements a user has earned"""
        earned = []
        
        for achievement in self.achievements.values():
            achieved = True
            for req_key, req_value in achievement.requirements.items():
                if req_key not in user_stats or user_stats[req_key] < req_value:
                    achieved = False
                    break
            
            if achieved:
                earned.append(achievement)
        
        return earned

    def calculate_achievement_bonuses(self, completed_achievements: List[int]) -> Dict[str, int]:
        """Calculate total stat bonuses from achievements"""
        bonuses = {
            'strength': 0,
            'agility': 0,
            'intelligence': 0,
            'hp': 0,
            'mp': 0,
            'luck': 0
        }
        
        for achievement_id in completed_achievements:
            if achievement_id in self.achievements:
                achievement = self.achievements[achievement_id]
                for stat, value in achievement.bonus_stats.items():
                    if stat == 'all':
                        # Apply to all stats
                        for base_stat in bonuses:
                            bonuses[base_stat] += value
                    elif stat in bonuses:
                        bonuses[stat] += value
        
        return bonuses

    def apply_achievement_rewards(self, user_data: Dict, achievement: Achievement) -> Dict:
        """Apply achievement rewards to user data"""
        # Add crystals
        user_data['crystals'] = user_data.get('crystals', 0) + achievement.reward_crystals
        
        # Apply stat bonuses
        for stat, value in achievement.bonus_stats.items():
            if stat == 'all':
                # Apply to all base stats
                base_stats = ['strength', 'agility', 'intelligence', 'hp', 'mp', 'luck']
                for base_stat in base_stats:
                    user_data[base_stat] = user_data.get(base_stat, 0) + value
            else:
                user_data[stat] = user_data.get(stat, 0) + value
        
        # Add achievement to completed list
        if 'completed_achievements' not in user_data:
            user_data['completed_achievements'] = []
        user_data['completed_achievements'].append(achievement.id)
        
        return user_data

    def distribute_stat_points(self, current_stats: Dict[str, int], points: Dict[str, int]) -> Tuple[Dict[str, int], str]:
        """Distribute stat points and validate the distribution"""
        new_stats = current_stats.copy()
        total_points = sum(points.values())
        available_points = self.calculate_available_stat_points(current_stats['level'])
        
        if total_points > available_points:
            return current_stats, "Not enough stat points available"
        
        # Validate and apply each stat increase
        for stat, value in points.items():
            if value < 0:
                return current_stats, "Cannot decrease stats"
            if stat not in new_stats:
                return current_stats, f"Invalid stat: {stat}"
            new_stats[stat] += value
        
        return new_stats, "Stats distributed successfully"

    def calculate_available_stat_points(self, level: int) -> int:
        """Calculate total available stat points for a level"""
        level_info = self.calculate_level_info(level)
        return level_info.stat_points

    def calculate_combat_stats(self, base_stats: Dict[str, int], equipment_stats: Dict[str, int],
                             achievement_bonuses: Dict[str, int]) -> Dict[str, int]:
        """Calculate final combat stats including equipment and achievement bonuses"""
        combat_stats = {}
        
        # Combine all stat sources
        for stat in ['strength', 'agility', 'intelligence', 'hp', 'mp', 'luck']:
            combat_stats[stat] = (
                base_stats.get(stat, 0) +
                equipment_stats.get(stat, 0) +
                achievement_bonuses.get(stat, 0)
            )
        
        # Calculate derived stats
        combat_stats['attack'] = int(combat_stats['strength'] * 2.5)
        combat_stats['defense'] = int(combat_stats['strength'] * 1.5 + combat_stats['agility'] * 0.5)
        combat_stats['magic_attack'] = int(combat_stats['intelligence'] * 2.5)
        combat_stats['magic_defense'] = int(combat_stats['intelligence'] * 1.5 + combat_stats['agility'] * 0.5)
        combat_stats['evasion'] = int(combat_stats['agility'] * 0.5)
        combat_stats['critical_chance'] = min(50, int(combat_stats['luck'] * 0.2))  # Cap at 50%
        
        return combat_stats
