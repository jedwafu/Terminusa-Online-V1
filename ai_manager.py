from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime, timedelta
import random
import math
import json

@dataclass
class PlayerProfile:
    user_id: int
    activities: Dict[str, float]  # Activity type -> frequency (0-1)
    success_rates: Dict[str, float]  # Activity type -> success rate (0-1)
    preferences: Dict[str, float]  # Feature -> preference score (0-1)
    risk_tolerance: float  # 0-1
    last_updated: datetime

class AISystem:
    def __init__(self):
        self.activity_types = [
            'gate_hunting',
            'gambling',
            'trading',
            'crafting',
            'party_play',
            'solo_play',
            'marketplace',
            'gacha'
        ]
        
        self.feature_types = [
            'combat',
            'economy',
            'social',
            'collection',
            'progression'
        ]

    def analyze_player_behavior(self, user_id: int, activity_history: List[Dict]) -> PlayerProfile:
        """Analyze player's behavior and create/update their profile"""
        activities = {activity: 0.0 for activity in self.activity_types}
        success_rates = {activity: 0.0 for activity in self.activity_types}
        preferences = {feature: 0.0 for feature in self.feature_types}
        
        # Count activities and successes
        activity_counts = {activity: 0 for activity in self.activity_types}
        success_counts = {activity: 0 for activity in self.activity_types}
        
        for entry in activity_history:
            activity_type = entry['type']
            if activity_type in activities:
                activity_counts[activity_type] += 1
                if entry.get('success', False):
                    success_counts[activity_type] += 1
        
        # Calculate frequencies and success rates
        total_activities = sum(activity_counts.values()) or 1
        for activity in self.activity_types:
            activities[activity] = activity_counts[activity] / total_activities
            if activity_counts[activity] > 0:
                success_rates[activity] = success_counts[activity] / activity_counts[activity]
        
        # Calculate preferences
        preferences['combat'] = (activities['gate_hunting'] + activities['solo_play']) / 2
        preferences['economy'] = (activities['trading'] + activities['marketplace']) / 2
        preferences['social'] = activities['party_play']
        preferences['collection'] = (activities['gacha'] + activities['crafting']) / 2
        preferences['progression'] = sum(success_rates.values()) / len(success_rates)
        
        # Calculate risk tolerance based on activity patterns
        risk_activities = ['gambling', 'gacha', 'solo_play']
        risk_tolerance = sum(activities[act] for act in risk_activities) / len(risk_activities)
        
        return PlayerProfile(
            user_id=user_id,
            activities=activities,
            success_rates=success_rates,
            preferences=preferences,
            risk_tolerance=risk_tolerance,
            last_updated=datetime.utcnow()
        )

    def generate_quest(self, player: PlayerProfile) -> Dict:
        """Generate a personalized quest based on player profile"""
        # Determine quest type based on player preferences
        quest_weights = {
            'combat': player.preferences['combat'] * 2 if player.success_rates['gate_hunting'] > 0.5 else player.preferences['combat'],
            'economy': player.preferences['economy'] * 1.5 if player.activities['trading'] > 0.3 else player.preferences['economy'],
            'social': player.preferences['social'] * 2 if player.activities['party_play'] > 0.4 else player.preferences['social'],
            'collection': player.preferences['collection']
        }
        
        quest_type = max(quest_weights.items(), key=lambda x: x[1])[0]
        
        # Generate quest parameters
        if quest_type == 'combat':
            if player.risk_tolerance > 0.7:
                return {
                    'type': 'combat',
                    'name': 'Elite Hunter',
                    'description': 'Defeat elite monsters in high-grade gates',
                    'target': max(3, int(player.success_rates['gate_hunting'] * 10)),
                    'reward_crystals': int(1000 * (1 + player.risk_tolerance))
                }
            else:
                return {
                    'type': 'combat',
                    'name': 'Gate Explorer',
                    'description': 'Complete gates of any grade',
                    'target': max(5, int(player.success_rates['gate_hunting'] * 15)),
                    'reward_crystals': 500
                }
        elif quest_type == 'economy':
            if player.activities['marketplace'] > 0.4:
                return {
                    'type': 'economy',
                    'name': 'Market Mogul',
                    'description': 'Complete marketplace transactions',
                    'target': max(5, int(player.activities['marketplace'] * 20)),
                    'reward_crystals': 800
                }
            else:
                return {
                    'type': 'economy',
                    'name': 'Crystal Collector',
                    'description': 'Collect crystals from any source',
                    'target': 1000,
                    'reward_crystals': 200
                }
        elif quest_type == 'social':
            return {
                'type': 'social',
                'name': 'Party Leader',
                'description': 'Complete gates with a party',
                'target': max(3, int(player.activities['party_play'] * 10)),
                'reward_crystals': 600
            }
        else:  # collection
            if player.activities['gacha'] > 0.3:
                return {
                    'type': 'collection',
                    'name': 'Lucky Collector',
                    'description': 'Obtain items from gacha',
                    'target': max(2, int(player.activities['gacha'] * 8)),
                    'reward_crystals': 1000
                }
            else:
                return {
                    'type': 'collection',
                    'name': 'Item Collector',
                    'description': 'Collect different items',
                    'target': 10,
                    'reward_crystals': 400
                }

    def adjust_gacha_rates(self, player: PlayerProfile, base_rates: Dict[str, float]) -> Dict[str, float]:
        """Adjust gacha rates based on player profile"""
        adjusted_rates = base_rates.copy()
        
        # Loyalty bonus (based on activity frequency)
        activity_bonus = sum(player.activities.values()) / len(player.activities)
        
        # Success bonus (based on overall success rate)
        success_bonus = sum(player.success_rates.values()) / len(player.success_rates)
        
        # Risk tolerance bonus
        risk_bonus = player.risk_tolerance
        
        # Calculate total bonus (max 20% increase to better rates)
        total_bonus = min(0.2, (activity_bonus + success_bonus + risk_bonus) / 3)
        
        # Apply bonus by slightly increasing better rates and decreasing lower rates
        for grade in adjusted_rates:
            if grade in ['Legendary', 'Immortal']:
                adjusted_rates[grade] *= (1 + total_bonus)
            elif grade in ['Basic', 'Intermediate']:
                adjusted_rates[grade] *= (1 - total_bonus)
        
        # Normalize rates to ensure they sum to 1
        total = sum(adjusted_rates.values())
        return {grade: rate/total for grade, rate in adjusted_rates.items()}

    def generate_gate_monsters(self, player: PlayerProfile, gate_grade: str, base_monsters: List[Dict]) -> List[Dict]:
        """Adjust gate monsters based on player profile"""
        adjusted_monsters = []
        
        # Calculate difficulty modifier
        difficulty_mod = 1.0
        if player.success_rates['gate_hunting'] > 0.7:
            difficulty_mod += 0.2  # Increase difficulty for successful players
        if player.risk_tolerance > 0.7:
            difficulty_mod += 0.1  # Increase difficulty for risk-takers
        
        for monster in base_monsters:
            adjusted_monster = monster.copy()
            
            # Adjust monster stats based on player profile
            adjusted_monster['hp'] = int(monster['hp'] * difficulty_mod)
            adjusted_monster['damage'] = int(monster['damage'] * difficulty_mod)
            
            # Adjust drop rates based on player luck and preferences
            if 'drop_table' in monster:
                drop_table = monster['drop_table'].copy()
                luck_bonus = player.preferences['collection'] * 0.1  # Up to 10% better drops
                drop_table = {
                    item: min(1.0, rate * (1 + luck_bonus))
                    for item, rate in drop_table.items()
                }
                adjusted_monster['drop_table'] = drop_table
            
            adjusted_monsters.append(adjusted_monster)
        
        return adjusted_monsters

    def calculate_rewards(self, player: PlayerProfile, base_rewards: Dict) -> Dict:
        """Adjust rewards based on player profile"""
        adjusted_rewards = base_rewards.copy()
        
        # Calculate reward modifier based on player performance
        reward_mod = 1.0
        if player.success_rates['gate_hunting'] > 0.6:
            reward_mod += 0.1  # 10% bonus for consistent performance
        if player.activities['party_play'] > 0.5:
            reward_mod += 0.05  # 5% bonus for team players
        
        # Apply modifiers to rewards
        for reward_type in adjusted_rewards:
            if isinstance(adjusted_rewards[reward_type], (int, float)):
                adjusted_rewards[reward_type] = int(adjusted_rewards[reward_type] * reward_mod)
        
        return adjusted_rewards

    def should_trigger_event(self, player: PlayerProfile, event_type: str) -> bool:
        """Determine if a special event should trigger for the player"""
        if event_type == 'bonus_gate':
            # Trigger bonus gates for active gate hunters
            return (
                player.activities['gate_hunting'] > 0.4 and
                player.success_rates['gate_hunting'] > 0.6 and
                random.random() < 0.2  # 20% chance
            )
        elif event_type == 'market_opportunity':
            # Trigger market opportunities for active traders
            return (
                player.activities['trading'] > 0.3 and
                player.success_rates['trading'] > 0.5 and
                random.random() < 0.15  # 15% chance
            )
        elif event_type == 'gacha_bonus':
            # Trigger gacha bonuses for consistent players
            return (
                player.activities['gacha'] > 0.2 and
                sum(player.success_rates.values()) / len(player.success_rates) > 0.7 and
                random.random() < 0.1  # 10% chance
            )
        return False
