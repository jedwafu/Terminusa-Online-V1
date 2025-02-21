from typing import Dict, List, Optional
from datetime import datetime
import math

from models import db, Guild, GuildMember, User
from game_systems.event_system import EventSystem, EventType, GameEvent

class ProgressionSystem:
    def __init__(self, websocket):
        self.event_system = EventSystem(websocket)
        
        # Level progression configuration
        self.base_exp = 1000  # Base experience needed for level 2
        self.exp_multiplier = 1.5  # Experience multiplier per level
        
        # Level benefits configuration
        self.level_benefits = {
            'member_cap': {
                'base': 50,
                'per_level': 2  # Additional member slots per level
            },
            'quest_slots': {
                'base': 3,
                'levels': {10: 4, 25: 5, 50: 6}  # Level thresholds for additional quest slots
            },
            'tax_rate_bonus': {
                'base': 0,
                'per_level': 0.5  # Additional tax rate % per level
            },
            'gate_rewards': {
                'base': 1.0,
                'per_level': 0.02  # Additional 2% reward multiplier per level
            }
        }

    def calculate_exp_requirement(self, level: int) -> int:
        """Calculate experience required for a given level"""
        return int(self.base_exp * (self.exp_multiplier ** (level - 1)))

    def calculate_total_exp_to_level(self, target_level: int) -> int:
        """Calculate total experience required to reach a target level"""
        total_exp = 0
        for level in range(1, target_level):
            total_exp += self.calculate_exp_requirement(level)
        return total_exp

    def add_experience(self, guild: Guild, amount: int, source: str) -> Dict:
        """Add experience to guild and handle level ups"""
        try:
            original_level = guild.level
            guild.experience += amount

            # Calculate new level based on total experience
            new_level = 1
            total_exp = 0
            while True:
                next_level_exp = self.calculate_exp_requirement(new_level)
                if total_exp + next_level_exp > guild.experience:
                    break
                total_exp += next_level_exp
                new_level += 1

            level_ups = []
            if new_level > original_level:
                # Process each level up
                for level in range(original_level + 1, new_level + 1):
                    benefits = self.get_level_benefits(level)
                    level_ups.append({
                        'level': level,
                        'benefits': benefits
                    })
                    self._apply_level_benefits(guild, level, benefits)

                guild.level = new_level
                db.session.commit()

                # Emit level up event
                self.event_system.emit_event(GameEvent(
                    type=EventType.GUILD_UPDATE,
                    guild_id=guild.id,
                    data={
                        'type': 'guild_level_up',
                        'old_level': original_level,
                        'new_level': new_level,
                        'level_ups': level_ups
                    }
                ))

            return {
                'success': True,
                'exp_gained': amount,
                'level_ups': level_ups,
                'current_level': new_level,
                'current_exp': guild.experience,
                'next_level_exp': self.calculate_exp_requirement(new_level)
            }

        except Exception as e:
            db.session.rollback()
            raise Exception(f"Failed to add experience: {str(e)}")

    def get_level_benefits(self, level: int) -> Dict:
        """Get benefits for a specific guild level"""
        benefits = {
            'member_cap': self._calculate_member_cap(level),
            'quest_slots': self._calculate_quest_slots(level),
            'tax_rate_bonus': self._calculate_tax_bonus(level),
            'gate_rewards_multiplier': self._calculate_reward_multiplier(level)
        }
        
        # Add special milestone benefits
        if level in [10, 25, 50, 75, 100]:
            benefits['special_rewards'] = self._get_milestone_rewards(level)
            
        return benefits

    def _calculate_member_cap(self, level: int) -> int:
        """Calculate maximum member capacity for guild level"""
        return self.level_benefits['member_cap']['base'] + \
               (level - 1) * self.level_benefits['member_cap']['per_level']

    def _calculate_quest_slots(self, level: int) -> int:
        """Calculate number of concurrent quest slots"""
        base_slots = self.level_benefits['quest_slots']['base']
        for req_level, slots in sorted(self.level_benefits['quest_slots']['levels'].items()):
            if level >= req_level:
                base_slots = slots
        return base_slots

    def _calculate_tax_bonus(self, level: int) -> float:
        """Calculate tax rate bonus percentage"""
        return self.level_benefits['tax_rate_bonus']['base'] + \
               (level - 1) * self.level_benefits['tax_rate_bonus']['per_level']

    def _calculate_reward_multiplier(self, level: int) -> float:
        """Calculate gate rewards multiplier"""
        return self.level_benefits['gate_rewards']['base'] + \
               (level - 1) * self.level_benefits['gate_rewards']['per_level']

    def _get_milestone_rewards(self, level: int) -> Dict:
        """Get special rewards for milestone levels"""
        milestone_rewards = {
            10: {
                'crystals': 10000,
                'exons': 100,
                'special_title': 'Rising Guild'
            },
            25: {
                'crystals': 25000,
                'exons': 250,
                'special_title': 'Established Guild'
            },
            50: {
                'crystals': 50000,
                'exons': 500,
                'special_title': 'Elite Guild'
            },
            75: {
                'crystals': 75000,
                'exons': 750,
                'special_title': 'Legendary Guild'
            },
            100: {
                'crystals': 100000,
                'exons': 1000,
                'special_title': 'Immortal Guild'
            }
        }
        return milestone_rewards.get(level, {})

    def _apply_level_benefits(self, guild: Guild, level: int, benefits: Dict) -> None:
        """Apply level up benefits to guild"""
        try:
            # Update member cap
            guild.max_members = benefits['member_cap']
            
            # Update quest slots in settings
            guild.settings['quest_slots'] = benefits['quest_slots']
            
            # Apply milestone rewards if any
            if 'special_rewards' in benefits:
                rewards = benefits['special_rewards']
                if 'crystals' in rewards:
                    guild.crystal_balance += rewards['crystals']
                if 'exons' in rewards:
                    guild.exon_balance += rewards['exons']
                if 'special_title' in rewards:
                    guild.settings['title'] = rewards['special_title']

            # Update other settings
            guild.settings['tax_rate_bonus'] = benefits['tax_rate_bonus']
            guild.settings['gate_rewards_multiplier'] = benefits['gate_rewards_multiplier']

        except Exception as e:
            raise Exception(f"Failed to apply level benefits: {str(e)}")

    def calculate_exp_reward(self, action: str, base_amount: int = 100) -> int:
        """Calculate experience reward for different actions"""
        exp_multipliers = {
            'gate_clear': {
                'F': 1.0,
                'E': 1.2,
                'D': 1.5,
                'C': 2.0,
                'B': 2.5,
                'A': 3.0,
                'S': 4.0
            },
            'quest_complete': {
                'normal': 1.0,
                'hard': 1.5,
                'extreme': 2.0
            },
            'member_join': 0.5,
            'achievement_complete': 2.0
        }

        if isinstance(action, dict):
            # Handle structured actions like gate clears and quests
            action_type = action.get('type')
            action_rank = action.get('rank', 'normal')
            multiplier = exp_multipliers.get(action_type, {}).get(action_rank, 1.0)
        else:
            # Handle simple actions
            multiplier = exp_multipliers.get(action, 1.0)

        return int(base_amount * multiplier)

    def get_progression_status(self, guild: Guild) -> Dict:
        """Get detailed progression status for guild"""
        current_level = guild.level
        current_exp = guild.experience
        next_level_exp = self.calculate_exp_requirement(current_level)
        exp_to_next = next_level_exp - (current_exp - self.calculate_total_exp_to_level(current_level))
        
        return {
            'level': current_level,
            'experience': current_exp,
            'next_level_exp': next_level_exp,
            'exp_to_next': exp_to_next,
            'progress_percent': ((next_level_exp - exp_to_next) / next_level_exp) * 100,
            'benefits': self.get_level_benefits(current_level),
            'next_level_benefits': self.get_level_benefits(current_level + 1)
        }
