"""
AI Agent System for Terminusa Online
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
import random
import logging
import json
from collections import defaultdict
from models import db, User, Transaction, Gate, Quest, Achievement
from game_config import (
    GATE_GRADES,
    JOB_CLASSES,
    GAMBLING_CONFIG,
    ELEMENTS,
    AI_CONFIDENCE_THRESHOLD
)

logger = logging.getLogger(__name__)

class AIAgent:
    """AI Agent that learns from player behavior and influences game mechanics"""
    
    def __init__(self):
        self.player_profiles = {}  # Cache of player behavior profiles
        self.activity_weights = {
            'gate_hunting': 0.3,
            'gambling': 0.2,
            'trading': 0.15,
            'questing': 0.2,
            'social': 0.15
        }
        self.last_update = datetime.utcnow()
        self.update_interval = timedelta(hours=1)

    def analyze_player(self, user: User) -> Dict:
        """Analyze player behavior and update profile"""
        try:
            # Check if we need to update the profile
            if (user.id in self.player_profiles and 
                datetime.utcnow() - self.player_profiles[user.id]['last_update'] < self.update_interval):
                return self.player_profiles[user.id]

            # Collect player data
            profile = {
                'user_id': user.id,
                'level': user.level,
                'job_class': user.job_class,
                'hunter_class': user.hunter_class,
                'activity_patterns': self._analyze_activity_patterns(user),
                'performance_metrics': self._analyze_performance_metrics(user),
                'social_behavior': self._analyze_social_behavior(user),
                'risk_profile': self._analyze_risk_profile(user),
                'progression_rate': self._analyze_progression_rate(user),
                'last_update': datetime.utcnow()
            }

            # Cache the profile
            self.player_profiles[user.id] = profile

            return profile

        except Exception as e:
            logger.error(f"Failed to analyze player {user.id}: {str(e)}")
            return None

    def generate_quest(self, user: User) -> Dict:
        """Generate AI-tailored quest for player"""
        try:
            profile = self.analyze_player(user)
            if not profile:
                return self._generate_fallback_quest(user)

            # Determine quest type based on player profile
            quest_type = self._determine_quest_type(profile)
            
            # Generate quest parameters
            quest_params = self._generate_quest_parameters(profile, quest_type)
            
            # Create quest
            quest = Quest(
                user_id=user.id,
                type=quest_type,
                parameters=quest_params,
                difficulty=self._calculate_quest_difficulty(profile),
                rewards=self._calculate_quest_rewards(profile, quest_type),
                expires_at=datetime.utcnow() + timedelta(days=1)
            )
            
            db.session.add(quest)
            db.session.commit()

            return {
                "success": True,
                "message": "Quest generated successfully",
                "quest": quest.to_dict()
            }

        except Exception as e:
            logger.error(f"Failed to generate quest: {str(e)}")
            return {
                "success": False,
                "message": "Failed to generate quest"
            }

    def evaluate_gacha_probability(self, user: User, gacha_type: str) -> float:
        """Calculate gacha probability based on player profile"""
        try:
            profile = self.analyze_player(user)
            if not profile:
                return self._get_default_gacha_rate(gacha_type)

            # Base probability
            base_prob = self._get_default_gacha_rate(gacha_type)
            
            # Adjust based on player profile
            adjustments = {
                # Reward consistent players
                'progression_rate': 0.05 if profile['progression_rate'] > 0.7 else 0,
                
                # Balance for unlucky players
                'recent_failures': self._calculate_pity_rate(user, gacha_type),
                
                # Reward active players
                'activity_bonus': 0.02 if profile['activity_patterns']['total_actions'] > 100 else 0,
                
                # Special job class bonus
                'job_bonus': 0.03 if profile['job_class'] in ['Shadow Monarch', 'S-Rank Hunter'] else 0
            }
            
            # Apply adjustments
            final_prob = base_prob + sum(adjustments.values())
            
            # Ensure within reasonable bounds
            return max(0.001, min(0.999, final_prob))

        except Exception as e:
            logger.error(f"Failed to evaluate gacha probability: {str(e)}")
            return self._get_default_gacha_rate(gacha_type)

    def evaluate_achievement_progress(self, user: User, achievement_id: int) -> Dict:
        """Evaluate achievement progress with AI insights"""
        try:
            profile = self.analyze_player(user)
            if not profile:
                return {
                    "success": False,
                    "message": "Could not analyze player profile"
                }

            achievement = Achievement.query.get(achievement_id)
            if not achievement:
                return {
                    "success": False,
                    "message": "Achievement not found"
                }

            # Calculate base progress
            base_progress = self._calculate_achievement_progress(user, achievement)
            
            # AI adjustments based on player profile
            adjustments = self._calculate_achievement_adjustments(profile, achievement)
            
            # Combine base progress with AI insights
            final_progress = self._apply_achievement_adjustments(base_progress, adjustments)
            
            return {
                "success": True,
                "progress": final_progress,
                "insights": adjustments,
                "estimated_completion": self._estimate_completion_time(profile, achievement)
            }

        except Exception as e:
            logger.error(f"Failed to evaluate achievement progress: {str(e)}")
            return {
                "success": False,
                "message": "Failed to evaluate achievement progress"
            }

    def predict_gate_outcome(self, user: User, gate: Gate, party: Optional[List[User]] = None) -> Dict:
        """Predict gate raid outcome based on player/party capabilities"""
        try:
            # Analyze all participants
            profiles = [self.analyze_player(user)]
            if party:
                profiles.extend([self.analyze_player(member) for member in party])

            # Calculate success probability
            success_prob = self._calculate_gate_success_probability(profiles, gate)
            
            # Generate tactical insights
            tactics = self._generate_tactical_insights(profiles, gate)
            
            # Predict rewards and risks
            rewards_prediction = self._predict_gate_rewards(profiles, gate)
            risk_assessment = self._assess_gate_risks(profiles, gate)
            
            return {
                "success": True,
                "success_probability": success_prob,
                "tactical_insights": tactics,
                "predicted_rewards": rewards_prediction,
                "risk_assessment": risk_assessment,
                "confidence_level": self._calculate_prediction_confidence(profiles, gate)
            }

        except Exception as e:
            logger.error(f"Failed to predict gate outcome: {str(e)}")
            return {
                "success": False,
                "message": "Failed to predict gate outcome"
            }

    def _analyze_activity_patterns(self, user: User) -> Dict:
        """Analyze player's activity patterns"""
        try:
            # Get recent activity data (last 7 days)
            cutoff = datetime.utcnow() - timedelta(days=7)
            
            # Analyze different types of actions
            activities = defaultdict(int)
            
            # Gate activities
            gates = Gate.query.filter(
                Gate.created_at >= cutoff,
                Gate.current_players.contains(user)
            ).all()
            activities['gate_hunting'] = len(gates)
            
            # Trading activities
            trades = Transaction.query.filter(
                Transaction.created_at >= cutoff,
                Transaction.user_id == user.id,
                Transaction.type.in_(['trade', 'market_purchase'])
            ).count()
            activities['trading'] = trades
            
            # Gambling activities
            gambles = Transaction.query.filter(
                Transaction.created_at >= cutoff,
                Transaction.user_id == user.id,
                Transaction.type == 'gamble'
            ).count()
            activities['gambling'] = gambles
            
            # Quest activities
            quests = Quest.query.filter(
                Quest.created_at >= cutoff,
                Quest.user_id == user.id,
                Quest.completed_at.isnot(None)
            ).count()
            activities['questing'] = quests
            
            # Calculate activity distribution
            total_actions = sum(activities.values())
            if total_actions > 0:
                distribution = {
                    k: v / total_actions 
                    for k, v in activities.items()
                }
            else:
                distribution = {k: 0 for k in activities}
            
            return {
                'total_actions': total_actions,
                'distribution': distribution,
                'preferred_activity': max(distribution.items(), key=lambda x: x[1])[0]
                if total_actions > 0 else None
            }

        except Exception as e:
            logger.error(f"Failed to analyze activity patterns: {str(e)}")
            return {
                'total_actions': 0,
                'distribution': {},
                'preferred_activity': None
            }

    def _analyze_performance_metrics(self, user: User) -> Dict:
        """Analyze player's performance metrics"""
        try:
            # Get recent performance data (last 7 days)
            cutoff = datetime.utcnow() - timedelta(days=7)
            
            # Gate completion rate
            gates_attempted = Gate.query.filter(
                Gate.created_at >= cutoff,
                Gate.current_players.contains(user)
            ).count()
            
            gates_completed = Gate.query.filter(
                Gate.created_at >= cutoff,
                Gate.current_players.contains(user),
                Gate.status == 'completed'
            ).count()
            
            completion_rate = (
                gates_completed / gates_attempted 
                if gates_attempted > 0 else 0
            )
            
            # Average gate clear time
            clear_times = [
                (gate.completed_at - gate.created_at).total_seconds()
                for gate in Gate.query.filter(
                    Gate.created_at >= cutoff,
                    Gate.current_players.contains(user),
                    Gate.status == 'completed'
                ).all()
            ]
            
            avg_clear_time = (
                sum(clear_times) / len(clear_times)
                if clear_times else 0
            )
            
            return {
                'completion_rate': completion_rate,
                'avg_clear_time': avg_clear_time,
                'gates_attempted': gates_attempted,
                'gates_completed': gates_completed,
                'efficiency_score': self._calculate_efficiency_score(
                    completion_rate, avg_clear_time
                )
            }

        except Exception as e:
            logger.error(f"Failed to analyze performance metrics: {str(e)}")
            return {
                'completion_rate': 0,
                'avg_clear_time': 0,
                'gates_attempted': 0,
                'gates_completed': 0,
                'efficiency_score': 0
            }

    def _analyze_social_behavior(self, user: User) -> Dict:
        """Analyze player's social interactions"""
        try:
            # Get recent social data (last 7 days)
            cutoff = datetime.utcnow() - timedelta(days=7)
            
            # Party participation
            party_activities = Gate.query.filter(
                Gate.created_at >= cutoff,
                Gate.current_players.contains(user),
                Gate.party_id.isnot(None)
            ).count()
            
            # Trading interactions
            trade_partners = Transaction.query.filter(
                Transaction.created_at >= cutoff,
                Transaction.user_id == user.id,
                Transaction.type == 'trade'
            ).with_entities(Transaction.recipient_id).distinct().count()
            
            # Guild participation (if in guild)
            guild_activities = 0
            if user.guild_id:
                guild_activities = Quest.query.filter(
                    Quest.created_at >= cutoff,
                    Quest.user_id == user.id,
                    Quest.type == 'guild'
                ).count()
            
            return {
                'party_participation_rate': party_activities,
                'trade_network_size': trade_partners,
                'guild_participation_rate': guild_activities,
                'sociability_score': self._calculate_sociability_score(
                    party_activities, trade_partners, guild_activities
                )
            }

        except Exception as e:
            logger.error(f"Failed to analyze social behavior: {str(e)}")
            return {
                'party_participation_rate': 0,
                'trade_network_size': 0,
                'guild_participation_rate': 0,
                'sociability_score': 0
            }

    def _analyze_risk_profile(self, user: User) -> Dict:
        """Analyze player's risk-taking behavior"""
        try:
            # Get recent risk data (last 7 days)
            cutoff = datetime.utcnow() - timedelta(days=7)
            
            # Gambling behavior
            gambles = Transaction.query.filter(
                Transaction.created_at >= cutoff,
                Transaction.user_id == user.id,
                Transaction.type == 'gamble'
            ).all()
            
            total_gambled = sum(t.amount for t in gambles)
            gambling_frequency = len(gambles)
            
            # High-grade gate attempts
            high_grade_attempts = Gate.query.filter(
                Gate.created_at >= cutoff,
                Gate.current_players.contains(user),
                Gate.grade.in_(['A', 'S'])
            ).count()
            
            # Equipment upgrade attempts
            risky_upgrades = Transaction.query.filter(
                Transaction.created_at >= cutoff,
                Transaction.user_id == user.id,
                Transaction.type == 'equipment_upgrade',
                Transaction.metadata['grade'].in_(['Legendary', 'Immortal'])
            ).count()
            
            return {
                'gambling_intensity': {
                    'frequency': gambling_frequency,
                    'total_amount': total_gambled
                },
                'high_grade_gate_frequency': high_grade_attempts,
                'risky_upgrade_attempts': risky_upgrades,
                'risk_tolerance_score': self._calculate_risk_score(
                    gambling_frequency, high_grade_attempts, risky_upgrades
                )
            }

        except Exception as e:
            logger.error(f"Failed to analyze risk profile: {str(e)}")
            return {
                'gambling_intensity': {
                    'frequency': 0,
                    'total_amount': 0
                },
                'high_grade_gate_frequency': 0,
                'risky_upgrade_attempts': 0,
                'risk_tolerance_score': 0
            }

    def _analyze_progression_rate(self, user: User) -> Dict:
        """Analyze player's progression rate"""
        try:
            # Get progression data (last 30 days)
            cutoff = datetime.utcnow() - timedelta(days=30)
            
            # Level progression
            level_history = json.loads(user.level_history or '[]')
            recent_levels = [
                level for level in level_history
                if datetime.fromisoformat(level['date']) >= cutoff
            ]
            
            level_progression = (
                recent_levels[-1]['level'] - recent_levels[0]['level']
                if len(recent_levels) > 1 else 0
            )
            
            # Equipment progression
            equipment_upgrades = Transaction.query.filter(
                Transaction.created_at >= cutoff,
                Transaction.user_id == user.id,
                Transaction.type == 'equipment_upgrade'
            ).count()
            
            # Achievement progression
            achievements_completed = Achievement.query.filter(
                Achievement.user_id == user.id,
                Achievement.completed_at >= cutoff
            ).count()
            
            return {
                'level_progression': level_progression,
                'equipment_progression': equipment_upgrades,
                'achievement_progression': achievements_completed,
                'progression_score': self._calculate_progression_score(
                    level_progression, equipment_upgrades, achievements_completed
                )
            }

        except Exception as e:
            logger.error(f"Failed to analyze progression rate: {str(e)}")
            return {
                'level_progression': 0,
                'equipment_progression': 0,
                'achievement_progression': 0,
                'progression_score': 0
            }

    def _determine_quest_type(self, profile: Dict) -> str:
        """Determine appropriate quest type based on player profile"""
        activity_prefs = profile['activity_patterns']['distribution']
        
        # Weight quest types based on player preferences
        weights = {
            'combat': activity_prefs.get('gate_hunting', 0) * 100,
            'gathering': activity_prefs.get('trading', 0) * 100,
            'exploration': activity_prefs.get('questing', 0) * 100,
            'social': activity_prefs.get('social', 0) * 100
        }
        
        # Add randomness to prevent predictability
        for quest_type in weights:
            weights[quest_type] += random.uniform(0, 20)
        
        return max(weights.items(), key=lambda x: x[1])[0]

    def _calculate_quest_difficulty(self, profile: Dict) -> int:
        """Calculate appropriate quest difficulty"""
        base_difficulty = profile['level'] // 10
        performance_mod = int(profile['performance_metrics']['efficiency_score'] * 5)
        risk_mod = int(profile['risk_profile']['risk_tolerance_score'] * 3)
        
        return max(1, min(10, base_difficulty + performance_mod + risk_mod))

    def _calculate_quest_rewards(self, profile: Dict, quest_type: str) -> Dict:
        """Calculate appropriate quest rewards"""
        base_crystals = 100 * profile['level']
        difficulty_mult = self._calculate_quest_difficulty(profile) * 0.2
        
        return {
            'crystals': int(base_crystals * (1 + difficulty_mult)),
            'experience': int(base_crystals * 2 * (1 + difficulty_mult)),
            'items': self._generate_quest_items(profile, quest_type)
        }

    def _get_default_gacha_rate(self, gacha_type: str) -> float:
        """Get default gacha rate for type"""
        return {
            'mount': 0.01,    # 1%
            'pet': 0.05,      # 5%
            'equipment': 0.1  # 10%
        }.get(gacha_type, 0.01)

    def _calculate_pity_rate(self, user: User, gacha_type: str) -> float:
        """Calculate pity rate based on previous pulls"""
        try:
            # Get recent failed pulls
            cutoff = datetime.utcnow() - timedelta(days=7)
            failed_pulls = Transaction.query.filter(
                Transaction.created_at >= cutoff,
                Transaction.user_id == user.id,
                Transaction.type == f'gacha_{gacha_type}',
                Transaction.metadata['result'] == 'failure'
            ).count()
            
            # Increase rate based on failures
            return min(0.1, failed_pulls * 0.005)  # Max 10% bonus
            
        except Exception:
            return 0.0

    def _calculate_achievement_progress(self, user: User, achievement: Achievement) -> float:
        """Calculate raw achievement progress"""
        try:
            progress_data = json.loads(achievement.progress_data or '{}')
            current = progress_data.get('current', 0)
            required = progress_data.get('required', 100)
            
            return current / required if required > 0 else 0
            
        except Exception:
            return 0.0

    def _calculate_achievement_adjustments(self, profile: Dict, achievement: Achievement) -> Dict:
        """Calculate AI-driven achievement adjustments"""
        return {
            'activity_bonus': 0.1 if profile['activity_patterns']['total_actions'] > 100 else 0,
            'performance_bonus': 0.1 if profile['performance_metrics']['efficiency_score'] > 0.7 else 0,
            'progression_bonus': 0.1 if profile['progression_rate']['progression_score'] > 0.7 else 0
        }

    def _apply_achievement_adjustments(self, base_progress: float, adjustments: Dict) -> float:
        """Apply AI adjustments to achievement progress"""
        total_adjustment = sum(adjustments.values())
        return min(1.0, base_progress * (1 + total_adjustment))

    def _estimate_completion_time(self, profile: Dict, achievement: Achievement) -> Optional[datetime]:
        """Estimate achievement completion time"""
        try:
            progress = self._calculate_achievement_progress(profile['user_id'], achievement)
            if progress >= 1:
                return None  # Already completed
                
            # Calculate rate of progress
            progress_data = json.loads(achievement.progress_data or '{}')
            progress_history = progress_data.get('history', [])
            
            if len(progress_history) < 2:
                return None  # Not enough data
                
            # Calculate average daily progress
            daily_progress = (
                (progress_history[-1]['progress'] - progress_history[0]['progress']) /
                (datetime.fromisoformat(progress_history[-1]['date']) - 
                 datetime.fromisoformat(progress_history[0]['date'])).days
            )
            
            if daily_progress <= 0:
                return None  # No progress being made
                
            # Estimate days remaining
            days_remaining = (1 - progress) / daily_progress
            
            return datetime.utcnow() + timedelta(days=days_remaining)
            
        except Exception:
            return None

    def _calculate_gate_success_probability(self, profiles: List[Dict], gate: Gate) -> float:
        """Calculate probability of gate success"""
        try:
            # Base probability from performance metrics
            avg_completion_rate = sum(
                p['performance_metrics']['completion_rate']
                for p in profiles
            ) / len(profiles)
            
            # Adjust for gate grade
            grade_modifier = 1 - (ord(gate.grade) - ord('F')) * 0.1
            
            # Adjust for party size and composition
            party_modifier = self._calculate_party_modifier(profiles)
            
            # Calculate final probability
            probability = avg_completion_rate * grade_modifier * party_modifier
            
            return max(0.01, min(0.99, probability))
            
        except Exception:
            return 0.5  # Default 50% chance

    def _calculate_party_modifier(self, profiles: List[Dict]) -> float:
        """Calculate party composition modifier"""
        try:
            if len(profiles) == 1:
                return 1.0  # Solo player
                
            # Check for role diversity
            roles = [p['job_class'] for p in profiles]
            has_tank = any(role in ['Fighter', 'Paladin'] for role in roles)
            has_healer = any(role in ['Healer', 'Priest'] for role in roles)
            has_dps = any(role in ['Assassin', 'Archer', 'Mage'] for role in roles)
            
            # Calculate modifier
            modifier = 1.0
            if has_tank:
                modifier += 0.1
            if has_healer:
                modifier += 0.1
            if has_dps:
                modifier += 0.1
                
            # Adjust for party size
            size_modifier = min(1.5, 1 + (len(profiles) - 1) * 0.1)
            
            return modifier * size_modifier
            
        except Exception:
            return 1.0

    def _generate_tactical_insights(self, profiles: List[Dict], gate: Gate) -> List[str]:
        """Generate tactical insights for gate raid"""
        insights = []
        try:
            # Party composition insights
            roles = [p['job_class'] for p in profiles]
            if not any(role in ['Fighter', 'Paladin'] for role in roles):
                insights.append("Consider adding a tank for better survival")
            if not any(role in ['Healer', 'Priest'] for role in roles):
                insights.append("A healer would improve party sustainability")
                
            # Element matching
            if gate.element in ELEMENTS:
                counter_elements = ELEMENTS[gate.element]['weaknesses']
                if not any(p.get('element') in counter_elements for p in profiles):
                    insights.append(f"Consider bringing {counter_elements[0]} element for advantage")
                    
            # Performance-based insights
            avg_clear_time = sum(
                p['performance_metrics'].get('avg_clear_time', 0)
                for p in profiles
            ) / len(profiles)
            
            if avg_clear_time > 600:  # 10 minutes
                insights.append("Focus on improving clear speed for better rewards")
                
            return insights
            
        except Exception:
            return ["Unable to generate tactical insights"]

    def _predict_gate_rewards(self, profiles: List[Dict], gate: Gate) -> Dict:
        """Predict potential gate rewards"""
        try:
            grade_config = GATE_GRADES[gate.grade]
            
            # Base crystal reward
            min_crystals, max_crystals = grade_config['crystal_reward_range']
            predicted_crystals = (min_crystals + max_crystals) // 2
            
            # Adjust for party size
            party_size = len(profiles)
            if party_size > 1:
                predicted_crystals = int(predicted_crystals * 0.8)  # 20% reduction for party
                
            # Predict equipment drops
            equipment_chance = grade_config['equipment_drop_rate']
            predicted_equipment = int(equipment_chance * 100)  # Percentage chance
            
            return {
                'crystals': {
                    'min': predicted_crystals * 0.8,
                    'max': predicted_crystals * 1.2,
                    'expected': predicted_crystals
                },
                'equipment': {
                    'drop_chance': f"{predicted_equipment}%",
                    'potential_grades': self._predict_equipment_grades(gate.grade)
                }
            }
            
        except Exception:
            return {
                'crystals': {'min': 0, 'max': 0, 'expected': 0},
                'equipment': {'drop_chance': "0%", 'potential_grades': []}
            }

    def _predict_equipment_grades(self, gate_grade: str) -> List[str]:
        """Predict potential equipment grades"""
        grade_mapping = {
            'F': ['Basic'],
            'E': ['Basic', 'Intermediate'],
            'D': ['Basic', 'Intermediate'],
            'C': ['Intermediate', 'Excellent'],
            'B': ['Intermediate', 'Excellent', 'Legendary'],
            'A': ['Excellent', 'Legendary'],
            'S': ['Excellent', 'Legendary', 'Immortal']
        }
        return grade_mapping.get(gate_grade, ['Basic'])

    def _assess_gate_risks(self, profiles: List[Dict], gate: Gate) -> Dict:
        """Assess potential risks in gate raid"""
        try:
            # Calculate average risk tolerance
            avg_risk_tolerance = sum(
                p['risk_profile']['risk_tolerance_score']
                for p in profiles
            ) / len(profiles)
            
            # Calculate average level vs gate requirement
            avg_level = sum(p['level'] for p in profiles) / len(profiles)
            level_difference = avg_level - gate.level_requirement
            
            # Generate risk assessment
            risks = {
                'difficulty_risk': self._calculate_difficulty_risk(level_difference),
                'equipment_loss_risk': self._calculate_equipment_risk(profiles),
                'party_coordination_risk': self._calculate_coordination_risk(profiles)
                if len(profiles) > 1 else 0
            }
            
            # Overall risk score
            overall_risk = sum(risks.values()) / len(risks)
            
            return {
                'risk_factors': risks,
                'overall_risk': overall_risk,
                'risk_level': self._get_risk_level(overall_risk),
                'recommendations': self._generate_risk_recommendations(risks)
            }
            
        except Exception:
            return {
                'risk_factors': {},
                'overall_risk': 1.0,
                'risk_level': 'high',
                'recommendations': ["Unable to assess risks"]
            }

    def _calculate_difficulty_risk(self, level_difference: float) -> float:
        """Calculate risk based on level difference"""
        if level_difference >= 20:
            return 0.1  # Very low risk
        elif level_difference >= 10:
            return 0.3  # Low risk
        elif level_difference >= 0:
            return 0.5  # Moderate risk
        else:
            return min(1.0, 0.7 + abs(level_difference) * 0.02)  # High risk

    def _calculate_equipment_risk(self, profiles: List[Dict]) -> float:
        """Calculate risk of equipment damage/loss"""
        try:
            # Check average equipment durability
            avg_durability = sum(
                sum(eq.get('durability', 100) for eq in p.get('equipment', {}).values())
                for p in profiles
            ) / sum(len(p.get('equipment', {})) for p in profiles)
            
            return max(0.1, 1 - (avg_durability / 100))
            
        except Exception:
            return 0.5

    def _calculate_coordination_risk(self, profiles: List[Dict]) -> float:
        """Calculate risk from party coordination"""
        try:
            # Check party experience
            avg_party_rate = sum(
                p['social_behavior']['party_participation_rate']
                for p in profiles
            ) / len(profiles)
            
            return max(0.1, 1 - (avg_party_rate / 100))
            
        except Exception:
            return 0.5

    def _get_risk_level(self, risk_score: float) -> str:
        """Convert risk score to level"""
        if risk_score < 0.3:
            return 'low'
        elif risk_score < 0.6:
            return 'moderate'
        else:
            return 'high'

    def _generate_risk_recommendations(self, risks: Dict) -> List[str]:
        """Generate recommendations based on risks"""
        recommendations = []
        
        if risks['difficulty_risk'] > 0.6:
            recommendations.append("Consider leveling up before attempting this gate")
            
        if risks['equipment_loss_risk'] > 0.6:
            recommendations.append("Repair equipment before entering")
            
        if risks['party_coordination_risk'] > 0.6:
            recommendations.append("Practice party coordination in lower-grade gates first")
            
        return recommendations

    def _calculate_prediction_confidence(self, profiles: List[Dict], gate: Gate) -> float:
        """Calculate confidence level in predictions"""
        try:
            # Factors affecting confidence
            factors = {
                # Data quality
                'profile_completeness': self._calculate_profile_completeness(profiles),
                
                # Historical accuracy
                'historical_accuracy': self._calculate_historical_accuracy(profiles, gate),
                
                # Sample size
                'data_points': self._calculate_data_points_confidence(profiles),
                
                # Consistency
                'behavior_consistency': self._calculate_behavior_consistency(profiles)
            }
            
            # Weight the factors
            weights = {
                'profile_completeness': 0.3,
                'historical_accuracy': 0.3,
                'data_points': 0.2,
                'behavior_consistency': 0.2
            }
            
            # Calculate weighted average
            confidence = sum(
                score * weights[factor]
                for factor, score in factors.items()
            )
            
            return min(1.0, max(0.1, confidence))
            
        except Exception as e:
            logger.error(f"Failed to calculate prediction confidence: {str(e)}")
            return 0.5  # Default to moderate confidence

    def _calculate_profile_completeness(self, profiles: List[Dict]) -> float:
        """Calculate how complete the profile data is"""
        try:
            required_fields = [
                'activity_patterns',
                'performance_metrics',
                'social_behavior',
                'risk_profile',
                'progression_rate'
            ]
            
            completeness_scores = []
            for profile in profiles:
                fields_present = sum(
                    1 for field in required_fields
                    if field in profile and profile[field]
                )
                completeness_scores.append(fields_present / len(required_fields))
            
            return sum(completeness_scores) / len(completeness_scores)
            
        except Exception:
            return 0.5

    def _calculate_historical_accuracy(self, profiles: List[Dict], gate: Gate) -> float:
        """Calculate historical prediction accuracy"""
        try:
            # Get recent predictions and outcomes
            cutoff = datetime.utcnow() - timedelta(days=30)
            
            total_predictions = 0
            correct_predictions = 0
            
            for profile in profiles:
                user = User.query.get(profile['user_id'])
                if not user:
                    continue
                    
                # Get similar grade gates
                similar_gates = Gate.query.filter(
                    Gate.created_at >= cutoff,
                    Gate.grade == gate.grade,
                    Gate.current_players.contains(user),
                    Gate.status.in_(['completed', 'failed'])
                ).all()
                
                for past_gate in similar_gates:
                    predicted_success = self._calculate_gate_success_probability(
                        [profile], past_gate
                    ) >= 0.5
                    actual_success = past_gate.status == 'completed'
                    
                    total_predictions += 1
                    if predicted_success == actual_success:
                        correct_predictions += 1
            
            return (
                correct_predictions / total_predictions
                if total_predictions > 0 else 0.5
            )
            
        except Exception:
            return 0.5

    def _calculate_data_points_confidence(self, profiles: List[Dict]) -> float:
        """Calculate confidence based on amount of data"""
        try:
            min_data_points = 50  # Threshold for high confidence
            
            avg_actions = sum(
                p['activity_patterns']['total_actions']
                for p in profiles
            ) / len(profiles)
            
            return min(1.0, avg_actions / min_data_points)
            
        except Exception:
            return 0.5

    def _calculate_behavior_consistency(self, profiles: List[Dict]) -> float:
        """Calculate player behavior consistency"""
        try:
            consistency_scores = []
            
            for profile in profiles:
                # Check activity pattern consistency
                activities = profile['activity_patterns']['distribution']
                std_dev = self._calculate_standard_deviation(activities.values())
                
                # Lower std dev means more consistent behavior
                consistency = 1 - min(1.0, std_dev)
                consistency_scores.append(consistency)
            
            return sum(consistency_scores) / len(consistency_scores)
            
        except Exception:
            return 0.5

    def _calculate_standard_deviation(self, values: List[float]) -> float:
        """Calculate standard deviation"""
        try:
            n = len(values)
            if n < 2:
                return 0
                
            mean = sum(values) / n
            variance = sum((x - mean) ** 2 for x in values) / (n - 1)
            return variance ** 0.5
            
        except Exception:
            return 0

    def _calculate_efficiency_score(self, completion_rate: float, avg_clear_time: float) -> float:
        """Calculate efficiency score from performance metrics"""
        try:
            # Normalize clear time (assume 600 seconds is optimal)
            time_score = max(0, min(1, 600 / avg_clear_time)) if avg_clear_time > 0 else 0
            
            # Combine with completion rate
            return (completion_rate * 0.7 + time_score * 0.3)
            
        except Exception:
            return 0

    def _calculate_sociability_score(self, party_rate: int, trade_size: int, guild_rate: int) -> float:
        """Calculate sociability score from social metrics"""
        try:
            # Normalize metrics
            party_score = min(1.0, party_rate / 50)  # 50 party activities for max score
            trade_score = min(1.0, trade_size / 20)  # 20 trade partners for max score
            guild_score = min(1.0, guild_rate / 30)  # 30 guild activities for max score
            
            # Weighted combination
            return (party_score * 0.4 + trade_score * 0.3 + guild_score * 0.3)
            
        except Exception:
            return 0

    def _calculate_risk_score(self, gambling: int, high_gates: int, risky_upgrades: int) -> float:
        """Calculate risk tolerance score"""
        try:
            # Normalize metrics
            gamble_score = min(1.0, gambling / 100)      # 100 gambles for max score
            gate_score = min(1.0, high_gates / 20)       # 20 high-grade gates for max score
            upgrade_score = min(1.0, risky_upgrades / 10) # 10 risky upgrades for max score
            
            # Weighted combination
            return (gamble_score * 0.3 + gate_score * 0.4 + upgrade_score * 0.3)
            
        except Exception:
            return 0

    def _calculate_progression_score(self, level_prog: int, equip_prog: int, achieve_prog: int) -> float:
        """Calculate progression score"""
        try:
            # Normalize metrics
            level_score = min(1.0, level_prog / 10)     # 10 levels for max score
            equip_score = min(1.0, equip_prog / 20)     # 20 upgrades for max score
            achieve_score = min(1.0, achieve_prog / 5)   # 5 achievements for max score
            
            # Weighted combination
            return (level_score * 0.4 + equip_score * 0.3 + achieve_score * 0.3)
            
        except Exception:
            return 0

    def _generate_quest_items(self, profile: Dict, quest_type: str) -> List[Dict]:
        """Generate appropriate quest reward items"""
        items = []
        try:
            # Base number of items based on quest type
            num_items = {
                'combat': 2,
                'gathering': 3,
                'exploration': 2,
                'social': 1
            }.get(quest_type, 1)
            
            # Adjust based on player level and performance
            level_bonus = profile['level'] // 20  # Extra item every 20 levels
            performance_bonus = int(profile['performance_metrics']['efficiency_score'] * 2)
            
            total_items = num_items + level_bonus + performance_bonus
            
            # Generate items (implementation would depend on your item system)
            for _ in range(total_items):
                items.append({
                    'type': 'random_appropriate_item',
                    'quality': self._determine_item_quality(profile)
                })
            
            return items
            
        except Exception:
            return []

    def _determine_item_quality(self, profile: Dict) -> str:
        """Determine appropriate item quality based on player profile"""
        try:
            # Base quality chances
            qualities = {
                'Common': 0.4,
                'Uncommon': 0.3,
                'Rare': 0.2,
                'Epic': 0.08,
                'Legendary': 0.02
            }
            
            # Adjust based on player metrics
            if profile['performance_metrics']['efficiency_score'] > 0.8:
                qualities['Epic'] += 0.05
                qualities['Legendary'] += 0.03
                
            if profile['progression_rate']['progression_score'] > 0.7:
                qualities['Rare'] += 0.1
                qualities['Epic'] += 0.02
                
            # Roll for quality
            roll = random.random()
            cumulative = 0
            for quality, chance in qualities.items():
                cumulative += chance
                if roll <= cumulative:
                    return quality
                    
            return 'Common'
            
        except Exception:
            return 'Common'
