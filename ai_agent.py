import random
from datetime import datetime, timedelta
import numpy as np
from collections import defaultdict
from game_config import (
    AI_CONSIDERATION_FACTORS,
    GATE_RANKS,
    GATE_CRYSTAL_REWARDS,
    ITEM_RARITIES,
    ITEM_RARITY_DROP_RATES,
    STATUS_EFFECT_CHANCES,
    MOUNT_PET_GACHA_RATES,
    CLASS_UPGRADE_REQUIREMENTS
)

class AIAgent:
    def __init__(self):
        self.activity_weights = defaultdict(float)
        self.behavior_cache = {}
        
    def analyze_player(self, user, activity_history=None):
        """Analyze player behavior and characteristics"""
        profile = {
            'activity_focus': self._analyze_activity_focus(activity_history),
            'combat_style': self._analyze_combat_style(user),
            'risk_level': self._calculate_risk_level(user, activity_history),
            'progression_rate': self._calculate_progression_rate(user),
            'social_tendency': self._analyze_social_behavior(user, activity_history),
            'market_engagement': self._analyze_market_behavior(user, activity_history),
            'currency_balance': self._analyze_currency_balance(user),  # New metric for currency balance
            'gambling_tendency': self._analyze_gambling_behavior(user, activity_history)  # New metric for gambling
        }
        
        self.behavior_cache[user.id] = profile
        return profile

    def _analyze_currency_balance(self, user):
        """Analyze player's currency management"""
        # Calculate ratio of each currency to total wealth
        total_wealth = (
            user.solana_balance * 1000 +  # Convert to common scale
            user.exons_balance * 100 +
            user.crystals
        )
        
        if total_wealth == 0:
            return 0.5  # Default middle ground
            
        # Calculate diversity score (0 = single currency, 1 = balanced)
        currency_ratios = [
            (user.solana_balance * 1000) / total_wealth,
            (user.exons_balance * 100) / total_wealth,
            user.crystals / total_wealth
        ]
        
        diversity = 1 - np.std(currency_ratios)
        return min(max(diversity, 0), 1)

    def _analyze_gambling_behavior(self, user, activity_history):
        """Analyze player's gambling tendencies"""
        if not activity_history:
            return 0.5
            
        gambling_activities = sum(1 for a in activity_history if a['type'] == 'gambling')
        total_activities = len(activity_history)
        
        if total_activities == 0:
            return 0.5
            
        # Calculate gambling frequency
        gambling_ratio = gambling_activities / total_activities
        
        # Analyze win/loss ratio if available
        wins = sum(1 for a in activity_history if a['type'] == 'gambling' and a.get('result') == 'win')
        if gambling_activities > 0:
            win_ratio = wins / gambling_activities
        else:
            win_ratio = 0.5
            
        # Combine frequency and success rate
        return (gambling_ratio + win_ratio) / 2

    def generate_quest(self, user, activity_history=None):
        """Generate an AI-powered quest based on player behavior"""
        profile = self.analyze_player(user, activity_history)
        
        quest_types = {
            'combat': 0.0,
            'gathering': 0.0,
            'exploration': 0.0,
            'social': 0.0,
            'market': 0.0,
            'currency': 0.0,  # Currency management quests
            'gambling': 0.0   # Gambling-related quests
        }
        
        # Adjust quest type weights based on profile
        quest_types['combat'] += profile['combat_style'] * 0.3
        quest_types['gathering'] += (1 - profile['risk_level']) * 0.2
        quest_types['exploration'] += profile['risk_level'] * 0.2
        quest_types['social'] += profile['social_tendency'] * 0.15
        quest_types['market'] += profile['market_engagement'] * 0.15
        quest_types['currency'] += profile['currency_balance'] * 0.1
        quest_types['gambling'] += profile['gambling_tendency'] * 0.1
        
        # Normalize weights
        total = sum(quest_types.values())
        quest_types = {k: v/total for k, v in quest_types.items()}
        
        # Select quest type
        quest_type = self._weighted_choice(quest_types)
        
        return self._create_quest(user, quest_type, profile)

    def _create_quest(self, user, quest_type, profile):
        """Create a specific quest based on type and profile"""
        quest_templates = {
            'combat': [
                {
                    'title': 'Beast Hunter',
                    'description': 'Defeat specific magic beasts in gates',
                    'requirements': {'kills': {'min': 5, 'max': 20}},
                    'rewards': {'crystals': {'min': 100, 'max': 1000}}
                }
            ],
            'gathering': [
                {
                    'title': 'Resource Collector',
                    'description': 'Collect specific items from gates',
                    'requirements': {'items': {'min': 3, 'max': 10}},
                    'rewards': {'crystals': {'min': 50, 'max': 500}}
                }
            ],
            'currency': [
                {
                    'title': 'Currency Trader',
                    'description': 'Complete currency swaps between Solana, Exons, and Crystals',
                    'requirements': {'swaps': {'min': 1, 'max': 5}},
                    'rewards': {'exons': {'min': 10, 'max': 100}}
                }
            ],
            'gambling': [
                {
                    'title': 'Lucky Streak',
                    'description': 'Win consecutive flip coin games',
                    'requirements': {'wins': {'min': 3, 'max': 7}},
                    'rewards': {'crystals': {'min': 500, 'max': 2000}}
                }
            ]
        }
        
        # Select template
        templates = quest_templates.get(quest_type, quest_templates['combat'])
        template = random.choice(templates)
        
        # Scale requirements and rewards based on profile
        scale_factor = 1.0 + (profile['progression_rate'] * 0.5)
        
        requirements = {}
        for req_type, req_range in template['requirements'].items():
            requirements[req_type] = random.randint(
                int(req_range['min'] * scale_factor),
                int(req_range['max'] * scale_factor)
            )
            
        rewards = {}
        for reward_type, reward_range in template['rewards'].items():
            rewards[reward_type] = random.randint(
                int(reward_range['min'] * scale_factor),
                int(reward_range['max'] * scale_factor)
            )
        
        return {
            'title': template['title'],
            'description': template['description'],
            'requirements': requirements,
            'rewards': rewards,
            'expires_at': datetime.utcnow() + timedelta(days=1)
        }

    def adjust_gambling_odds(self, user, base_chance, profile):
        """Adjust gambling odds based on player behavior"""
        modifier = 1.0
        
        # Adjust based on gambling history
        if profile['gambling_tendency'] > 0.7:  # Frequent gambler
            modifier *= 0.95  # Slightly reduce chances
        elif profile['gambling_tendency'] < 0.3:  # Rare gambler
            modifier *= 1.05  # Slightly increase chances
            
        # Adjust based on currency balance
        if profile['currency_balance'] < 0.3:  # Low on currency
            modifier *= 1.1  # Increase chances to help recovery
        elif profile['currency_balance'] > 0.7:  # High on currency
            modifier *= 0.9  # Reduce chances
            
        # Apply modifier
        adjusted_chance = base_chance * modifier
        
        # Ensure chance stays within reasonable bounds
        return min(max(adjusted_chance, 0.4), 0.6)

    def calculate_gate_confidence(self, user, gate, profile):
        """Calculate confidence score for entering a gate"""
        confidence = 0.0
        weights = {
            'level': 0.3,
            'class': 0.2,
            'combat_style': 0.15,
            'risk_level': 0.15,
            'equipment': 0.1,
            'party': 0.1
        }
        
        # Level factor
        level_diff = user.level - gate.min_level
        level_confidence = min(max((level_diff + 5) / 10, 0), 1)
        confidence += level_confidence * weights['level']
        
        # Class factor
        class_confidence = min(user.hunter_class.value / gate.min_hunter_class.value, 1)
        confidence += class_confidence * weights['class']
        
        # Combat style factor
        if profile['combat_style'] > 0.7:  # Aggressive
            confidence += weights['combat_style']  # Full confidence for aggressive players
        else:
            confidence += profile['combat_style'] * weights['combat_style']
            
        # Risk level factor
        risk_confidence = 1 - abs(profile['risk_level'] - 0.7)  # 0.7 is ideal risk level
        confidence += risk_confidence * weights['risk_level']
        
        # Equipment factor
        equipment_condition = min(
            sum(item.durability for item in user.inventory_items if item.is_equipped) / 
            (len([item for item in user.inventory_items if item.is_equipped]) * 100),
            1
        )
        confidence += equipment_condition * weights['equipment']
        
        # Party factor
        if user.party_id:
            confidence += weights['party']  # Full confidence boost for party play
            
        return min(confidence, 1.0)  # Ensure between 0 and 1

    def _weighted_choice(self, weights):
        """Make a weighted random choice"""
        items = list(weights.keys())
        weights = list(weights.values())
        return random.choices(items, weights=weights, k=1)[0]

    def get_or_analyze_player(self, user, activity_history=None):
        """Get cached profile or generate new one"""
        if user.id in self.behavior_cache:
            return self.behavior_cache[user.id]
        return self.analyze_player(user, activity_history)
