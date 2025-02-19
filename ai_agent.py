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
            'market_engagement': self._analyze_market_behavior(user, activity_history)
        }
        
        self.behavior_cache[user.id] = profile
        return profile

    def generate_quest(self, user, activity_history=None):
        """Generate an AI-powered quest based on player behavior"""
        profile = self.analyze_player(user, activity_history)
        
        quest_types = {
            'combat': 0.0,
            'gathering': 0.0,
            'exploration': 0.0,
            'social': 0.0,
            'market': 0.0
        }
        
        # Adjust quest type weights based on profile
        quest_types['combat'] += profile['combat_style'] * 0.3
        quest_types['gathering'] += (1 - profile['risk_level']) * 0.2
        quest_types['exploration'] += profile['risk_level'] * 0.2
        quest_types['social'] += profile['social_tendency'] * 0.15
        quest_types['market'] += profile['market_engagement'] * 0.15
        
        # Normalize weights
        total = sum(quest_types.values())
        quest_types = {k: v/total for k, v in quest_types.items()}
        
        # Select quest type
        quest_type = self._weighted_choice(quest_types)
        
        return self._create_quest(user, quest_type, profile)

    def orchestrate_gate(self, user, party=None):
        """Generate an appropriate gate encounter"""
        profile = self.get_or_analyze_player(user)
        
        # Determine appropriate gate rank
        available_ranks = self._get_available_ranks(user)
        rank_weights = self._calculate_rank_weights(user, profile, available_ranks)
        selected_rank = self._weighted_choice(rank_weights)
        
        # Generate gate content
        gate_data = {
            'rank': selected_rank,
            'magic_beasts': self._generate_magic_beasts(selected_rank, party),
            'crystal_rewards': self._calculate_rewards(selected_rank, profile, party),
            'difficulty_multiplier': self._calculate_difficulty(user, profile, party)
        }
        
        return gate_data

    def calculate_gacha_odds(self, user, gacha_type):
        """Calculate personalized gacha rates based on player behavior"""
        profile = self.get_or_analyze_player(user)
        
        base_rates = (
            MOUNT_PET_GACHA_RATES if gacha_type in ['mount', 'pet']
            else ITEM_RARITY_DROP_RATES
        )
        
        # Adjust rates based on profile
        adjusted_rates = {}
        for rarity, base_rate in base_rates.items():
            modifier = 1.0
            
            # Loyalty bonus (based on progression)
            modifier += profile['progression_rate'] * 0.1
            
            # Activity focus bonus
            if profile['activity_focus'] > 0.7:  # Highly focused player
                modifier += 0.05
                
            # Risk/reward adjustment
            if profile['risk_level'] > 0.8:  # High-risk player
                modifier += 0.03
                
            adjusted_rates[rarity] = base_rate * modifier
            
        # Normalize rates
        total = sum(adjusted_rates.values())
        adjusted_rates = {k: v/total for k, v in adjusted_rates.items()}
        
        return adjusted_rates

    def evaluate_class_upgrade(self, user):
        """Evaluate if a player should be allowed to upgrade their hunter class"""
        profile = self.get_or_analyze_player(user)
        current_class = user.hunter_class
        
        # Get requirements for next class
        if current_class.value not in CLASS_UPGRADE_REQUIREMENTS:
            return False, "Maximum class reached"
            
        requirements = CLASS_UPGRADE_REQUIREMENTS[current_class.value]
        
        # Basic requirement check
        if user.level < requirements['level']:
            return False, f"Level requirement not met. Need level {requirements['level']}"
            
        if user.gates_cleared < requirements['gates_cleared']:
            return False, f"Need to clear {requirements['gates_cleared']} gates"
        
        # Calculate confidence score
        confidence = self._calculate_upgrade_confidence(user, profile)
        
        # Decision threshold varies by class
        threshold = {
            'F': 0.5,  # Easier to upgrade from F
            'E': 0.6,
            'D': 0.65,
            'C': 0.7,
            'B': 0.75,
            'A': 0.8,  # Hardest to reach S class
        }
        
        current_threshold = threshold.get(current_class.value, 0.8)
        
        if confidence >= current_threshold:
            return True, f"Upgrade approved with {confidence:.2%} confidence"
        else:
            return False, f"Upgrade denied. Current confidence: {confidence:.2%}"

    def _analyze_activity_focus(self, activity_history):
        """Analyze player's focus on different activities"""
        if not activity_history:
            return 0.5
            
        activities = defaultdict(int)
        for activity in activity_history:
            activities[activity['type']] += 1
            
        # Calculate focus ratio
        total = sum(activities.values())
        max_activity = max(activities.values())
        
        return max_activity / total if total > 0 else 0.5

    def _analyze_combat_style(self, user):
        """Analyze player's combat behavior"""
        stats = {
            'strength': user.strength,
            'agility': user.agility,
            'intelligence': user.intelligence,
            'vitality': user.vitality
        }
        
        # Calculate combat style score (0 = defensive, 1 = aggressive)
        offensive_stats = stats['strength'] + stats['agility']
        defensive_stats = stats['vitality'] + stats['intelligence']
        total_stats = sum(stats.values())
        
        return offensive_stats / total_stats if total_stats > 0 else 0.5

    def _calculate_risk_level(self, user, activity_history):
        """Calculate player's risk-taking tendency"""
        risk_score = 0.5  # Default middle ground
        
        if activity_history:
            # Analyze gate choices
            gate_choices = [a for a in activity_history if a['type'] == 'gate_entry']
            if gate_choices:
                above_level = sum(1 for g in gate_choices if g['gate_level'] > user.level)
                risk_score = above_level / len(gate_choices)
                
        # Adjust based on current stats distribution
        stat_variance = np.std([
            user.strength,
            user.agility,
            user.intelligence,
            user.vitality
        ])
        risk_score += (stat_variance / 100) * 0.3  # Max 30% influence
        
        return min(max(risk_score, 0), 1)  # Ensure between 0 and 1

    def _calculate_progression_rate(self, user):
        """Calculate player's progression rate"""
        if not user.created_at:
            return 0.5
            
        days_active = (datetime.utcnow() - user.created_at).days + 1
        level_per_day = user.level / days_active
        
        # Normalize to 0-1 range (assuming average of 1 level per day)
        return min(level_per_day, 1)

    def _analyze_social_behavior(self, user, activity_history):
        """Analyze player's social interaction patterns"""
        social_score = 0.5
        
        if activity_history:
            social_activities = sum(1 for a in activity_history 
                                 if a['type'] in ['party_join', 'guild_activity', 'trade'])
            total_activities = len(activity_history)
            
            if total_activities > 0:
                social_score = social_activities / total_activities
                
        # Adjust based on current status
        if user.guild_id:
            social_score += 0.2
        if user.party_id:
            social_score += 0.1
            
        return min(social_score, 1)

    def _analyze_market_behavior(self, user, activity_history):
        """Analyze player's market participation"""
        if not activity_history:
            return 0.5
            
        market_activities = sum(1 for a in activity_history 
                              if a['type'] in ['market_buy', 'market_sell', 'trade'])
        total_activities = len(activity_history)
        
        return market_activities / total_activities if total_activities > 0 else 0.5

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
            # Add more templates for other quest types
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

    def _calculate_upgrade_confidence(self, user, profile):
        """Calculate confidence score for class upgrade"""
        confidence = 0.0
        weights = {
            'level_ratio': 0.3,
            'gates_ratio': 0.3,
            'activity_focus': 0.15,
            'risk_level': 0.15,
            'social_tendency': 0.1
        }
        
        # Level ratio
        req_level = CLASS_UPGRADE_REQUIREMENTS[user.hunter_class.value]['level']
        level_ratio = min(user.level / req_level, 1.5)  # Cap at 150%
        confidence += level_ratio * weights['level_ratio']
        
        # Gates cleared ratio
        req_gates = CLASS_UPGRADE_REQUIREMENTS[user.hunter_class.value]['gates_cleared']
        gates_ratio = min(user.gates_cleared / req_gates, 1.5)  # Cap at 150%
        confidence += gates_ratio * weights['gates_ratio']
        
        # Activity focus
        confidence += profile['activity_focus'] * weights['activity_focus']
        
        # Risk level (moderate risk is good)
        risk_modifier = 1 - abs(0.7 - profile['risk_level'])  # 0.7 is ideal risk level
        confidence += risk_modifier * weights['risk_level']
        
        # Social tendency
        confidence += profile['social_tendency'] * weights['social_tendency']
        
        return min(confidence, 1.0)  # Ensure between 0 and 1
