"""
AI Agent for Terminusa Online that learns from player activities and adapts game content
"""
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import random
import logging
from collections import defaultdict

from models import db, User, Transaction, Gate, Quest, Achievement
from models.user import PlayerClass, JobType

logger = logging.getLogger(__name__)

class AIAgent:
    def __init__(self):
        self.logger = logger
        self.activity_weights = {
            'gate_hunting': 1.0,
            'trading': 1.0,
            'gambling': 1.0,
            'questing': 1.0,
            'crafting': 1.0,
            'pvp': 1.0
        }
        
        # Learning rate for activity weight adjustments
        self.learning_rate = 0.1
        
        # Thresholds for different content types
        self.content_thresholds = {
            'easy': 0.3,
            'medium': 0.6,
            'hard': 0.8,
            'extreme': 0.9
        }

    def analyze_player(self, user: User) -> Dict[str, Any]:
        """Analyze player's profile, activities, and preferences"""
        try:
            # Get recent activity data (last 7 days)
            cutoff_date = datetime.utcnow() - timedelta(days=7)
            
            # Analyze different aspects of player behavior
            activity_pattern = self._analyze_activity_pattern(user, cutoff_date)
            progression_data = self._analyze_progression(user)
            economic_data = self._analyze_economic_behavior(user, cutoff_date)
            combat_data = self._analyze_combat_behavior(user)
            social_data = self._analyze_social_behavior(user)
            
            # Combine analyses into player profile
            profile = {
                'user_id': user.id,
                'activity_pattern': activity_pattern,
                'progression': progression_data,
                'economic': economic_data,
                'combat': combat_data,
                'social': social_data,
                'preferred_content': self._determine_preferred_content(activity_pattern),
                'challenge_rating': self._calculate_challenge_rating(user),
                'reward_preferences': self._analyze_reward_preferences(user, cutoff_date),
                'timestamp': datetime.utcnow()
            }
            
            self.logger.info(f"Generated player profile for user {user.id}")
            return profile
            
        except Exception as e:
            self.logger.error(f"Error analyzing player {user.id}: {str(e)}", exc_info=True)
            return {}

    def _analyze_activity_pattern(self, user: User, cutoff_date: datetime) -> Dict[str, float]:
        """Analyze player's activity patterns and preferences"""
        try:
            # Get all relevant activity records
            activities = defaultdict(int)
            
            # Gate hunting activity
            gates_cleared = Gate.query.filter(
                Gate.cleared_by == user.id,
                Gate.cleared_at >= cutoff_date
            ).count()
            activities['gate_hunting'] = gates_cleared
            
            # Trading activity
            trades = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.type.in_(['buy', 'sell', 'trade']),
                Transaction.timestamp >= cutoff_date
            ).count()
            activities['trading'] = trades
            
            # Gambling activity (gacha pulls)
            gambles = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.type.in_(['mount_gacha', 'pet_gacha']),
                Transaction.timestamp >= cutoff_date
            ).count()
            activities['gambling'] = gambles
            
            # Quest activity
            quests = Quest.query.filter(
                Quest.user_id == user.id,
                Quest.completed_at >= cutoff_date
            ).count()
            activities['questing'] = quests
            
            # Normalize activities to percentages
            total_activities = sum(activities.values()) or 1  # Avoid division by zero
            activity_pattern = {
                activity: count / total_activities
                for activity, count in activities.items()
            }
            
            # Update activity weights based on observed patterns
            self._update_activity_weights(activity_pattern)
            
            return activity_pattern
            
        except Exception as e:
            self.logger.error(f"Error analyzing activity pattern: {str(e)}", exc_info=True)
            return defaultdict(float)

    def _analyze_progression(self, user: User) -> Dict[str, Any]:
        """Analyze player's progression and achievements"""
        try:
            # Get achievement completion rate
            total_achievements = Achievement.query.count()
            completed_achievements = Achievement.query.filter(
                Achievement.user_id == user.id,
                Achievement.completed_at.isnot(None)
            ).count()
            
            achievement_rate = completed_achievements / total_achievements if total_achievements > 0 else 0
            
            return {
                'level': user.level,
                'experience': user.experience,
                'achievement_rate': achievement_rate,
                'class_mastery': self._calculate_class_mastery(user),
                'job_proficiency': self._calculate_job_proficiency(user),
                'gear_score': self._calculate_gear_score(user)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing progression: {str(e)}", exc_info=True)
            return {}

    def _analyze_economic_behavior(self, user: User, cutoff_date: datetime) -> Dict[str, Any]:
        """Analyze player's economic behavior and preferences"""
        try:
            transactions = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.timestamp >= cutoff_date
            ).all()
            
            spending_pattern = defaultdict(float)
            income_pattern = defaultdict(float)
            
            for tx in transactions:
                if tx.amount < 0:
                    spending_pattern[tx.type] += abs(tx.amount)
                else:
                    income_pattern[tx.type] += tx.amount
            
            return {
                'spending_pattern': dict(spending_pattern),
                'income_pattern': dict(income_pattern),
                'net_worth': self._calculate_net_worth(user),
                'market_activity': self._analyze_market_activity(user, cutoff_date)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing economic behavior: {str(e)}", exc_info=True)
            return {}

    def _analyze_combat_behavior(self, user: User) -> Dict[str, Any]:
        """Analyze player's combat behavior and performance"""
        try:
            return {
                'preferred_class': user.player_class,
                'combat_style': self._determine_combat_style(user),
                'success_rate': self._calculate_combat_success_rate(user),
                'party_preference': self._analyze_party_preference(user),
                'difficulty_preference': self._determine_difficulty_preference(user)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing combat behavior: {str(e)}", exc_info=True)
            return {}

    def _analyze_social_behavior(self, user: User) -> Dict[str, Any]:
        """Analyze player's social interactions and preferences"""
        try:
            return {
                'guild_activity': self._analyze_guild_activity(user),
                'party_frequency': self._calculate_party_frequency(user),
                'trade_interactions': self._analyze_trade_interactions(user),
                'pvp_participation': self._analyze_pvp_participation(user)
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing social behavior: {str(e)}", exc_info=True)
            return {}

    def _determine_preferred_content(self, activity_pattern: Dict[str, float]) -> List[str]:
        """Determine player's preferred content types based on activity pattern"""
        preferred = []
        
        # Sort activities by frequency
        sorted_activities = sorted(
            activity_pattern.items(),
            key=lambda x: x[1],
            reverse=True
        )
        
        # Add top 3 activities to preferred content
        for activity, frequency in sorted_activities[:3]:
            if frequency > 0.2:  # Only include if significant participation
                preferred.append(activity)
        
        return preferred

    def _calculate_challenge_rating(self, user: User) -> float:
        """Calculate player's challenge rating for content difficulty scaling"""
        try:
            # Base rating from level and gear
            base_rating = (user.level / 100) * self._calculate_gear_score(user)
            
            # Adjust for success rate
            success_rate = self._calculate_combat_success_rate(user)
            rating = base_rating * (1 + (success_rate - 0.5))
            
            # Cap between 0 and 1
            return max(0, min(1, rating))
            
        except Exception as e:
            self.logger.error(f"Error calculating challenge rating: {str(e)}", exc_info=True)
            return 0.5

    def _analyze_reward_preferences(self, user: User, cutoff_date: datetime) -> Dict[str, float]:
        """Analyze player's reward preferences"""
        try:
            transactions = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.timestamp >= cutoff_date
            ).all()
            
            preferences = defaultdict(int)
            for tx in transactions:
                if 'reward_type' in tx.details:
                    preferences[tx.details['reward_type']] += 1
            
            # Normalize preferences
            total = sum(preferences.values()) or 1
            return {
                reward: count / total
                for reward, count in preferences.items()
            }
            
        except Exception as e:
            self.logger.error(f"Error analyzing reward preferences: {str(e)}", exc_info=True)
            return {}

    def _update_activity_weights(self, observed_pattern: Dict[str, float]) -> None:
        """Update activity weights based on observed patterns"""
        try:
            for activity, observed_weight in observed_pattern.items():
                if activity in self.activity_weights:
                    current_weight = self.activity_weights[activity]
                    # Apply gradual adjustment based on learning rate
                    self.activity_weights[activity] = current_weight + (
                        self.learning_rate * (observed_weight - current_weight)
                    )
                    
        except Exception as e:
            self.logger.error(f"Error updating activity weights: {str(e)}", exc_info=True)

    def generate_content(self, user: User) -> Dict[str, Any]:
        """Generate personalized content based on player analysis"""
        try:
            profile = self.analyze_player(user)
            
            # Determine content type based on preferences
            content_type = random.choices(
                profile.get('preferred_content', ['gate_hunting']),
                weights=[self.activity_weights[act] for act in profile.get('preferred_content', ['gate_hunting'])]
            )[0]
            
            # Generate appropriate content
            if content_type == 'gate_hunting':
                return self._generate_gate_content(user, profile)
            elif content_type == 'questing':
                return self._generate_quest_content(user, profile)
            else:
                return self._generate_default_content(user, profile)
                
        except Exception as e:
            self.logger.error(f"Error generating content: {str(e)}", exc_info=True)
            return {}

    def _generate_gate_content(self, user: User, profile: Dict) -> Dict[str, Any]:
        """Generate personalized gate content"""
        try:
            challenge_rating = profile.get('challenge_rating', 0.5)
            
            # Determine gate difficulty
            difficulty = 'medium'
            for level, threshold in sorted(
                self.content_thresholds.items(),
                key=lambda x: x[1],
                reverse=True
            ):
                if challenge_rating >= threshold:
                    difficulty = level
                    break
            
            # Generate gate parameters
            return {
                'type': 'gate',
                'difficulty': difficulty,
                'level_requirement': max(1, user.level - 5),
                'recommended_party_size': self._determine_party_size(user, profile),
                'rewards': self._generate_rewards(user, profile),
                'special_conditions': self._generate_special_conditions(user, profile)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating gate content: {str(e)}", exc_info=True)
            return {}

    def _generate_quest_content(self, user: User, profile: Dict) -> Dict[str, Any]:
        """Generate personalized quest content"""
        try:
            return {
                'type': 'quest',
                'difficulty': self._determine_quest_difficulty(user, profile),
                'objectives': self._generate_quest_objectives(user, profile),
                'rewards': self._generate_rewards(user, profile),
                'time_limit': self._determine_time_limit(user, profile)
            }
            
        except Exception as e:
            self.logger.error(f"Error generating quest content: {str(e)}", exc_info=True)
            return {}

    def _generate_default_content(self, user: User, profile: Dict) -> Dict[str, Any]:
        """Generate default content when no specific preference is found"""
        try:
            return {
                'type': 'mixed',
                'activities': [
                    {
                        'type': 'gate_hunting',
                        'difficulty': 'easy',
                        'rewards': self._generate_rewards(user, profile)
                    },
                    {
                        'type': 'questing',
                        'difficulty': 'easy',
                        'rewards': self._generate_rewards(user, profile)
                    }
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Error generating default content: {str(e)}", exc_info=True)
            return {}

    def calculate_gacha_odds(self, user: User, gacha_type: str) -> Dict[str, float]:
        """Calculate personalized gacha odds based on player profile"""
        try:
            profile = self.analyze_player(user)
            
            # Base rates
            base_rates = {
                'Basic': 0.50,
                'Intermediate': 0.30,
                'Excellent': 0.15,
                'Legendary': 0.04,
                'Immortal': 0.01
            }
            
            # Adjust rates based on player profile
            adjusted_rates = self._adjust_gacha_rates(base_rates, profile)
            
            return adjusted_rates
            
        except Exception as e:
            self.logger.error(f"Error calculating gacha odds: {str(e)}", exc_info=True)
            return {'Basic': 1.0}  # Default to basic rate on error

    def _adjust_gacha_rates(self, base_rates: Dict[str, float], profile: Dict) -> Dict[str, float]:
        """Adjust gacha rates based on player profile"""
        try:
            adjusted_rates = base_rates.copy()
            
            # Factors that could improve rates
            positive_factors = {
                'level': profile.get('progression', {}).get('level', 1) / 100,
                'achievement_rate': profile.get('progression', {}).get('achievement_rate', 0),
                'spending_rate': profile.get('economic', {}).get('spending_rate', 0)
            }
            
            # Calculate adjustment factor (0 to 0.2)
            adjustment = sum(positive_factors.values()) / len(positive_factors) * 0.2
            
            # Apply adjustments
            for rarity in adjusted_rates:
                if rarity in ['Legendary', 'Immortal']:
                    adjusted_rates[rarity] *= (1 + adjustment)
                elif rarity == 'Basic':
                    adjusted_rates[rarity] *= (1 - adjustment)
            
            # Normalize rates to ensure they sum to 1
            total = sum(adjusted_rates.values())
            return {k: v/total for k, v in adjusted_rates.items()}
            
        except Exception as e:
            self.logger.error(f"Error adjusting gacha rates: {str(e)}", exc_info=True)
            return base_rates
