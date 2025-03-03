"""
Achievement System for Terminusa Online
"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import json
import logging
from models import db, User, Achievement, Transaction, Gate
from game_systems.ai_agent import AIAgent

logger = logging.getLogger(__name__)

class AchievementSystem:
    """Handles achievements and milestone tracking"""
    
    def __init__(self):
        self.ai_agent = AIAgent()
        self.achievement_categories = {
            'combat': {
                'gate_completions': {
                    'title': 'Gate Hunter',
                    'tiers': [10, 50, 100, 500, 1000],
                    'rewards': {
                        'crystals': [100, 500, 1000, 5000, 10000],
                        'titles': [
                            'Novice Hunter',
                            'Experienced Hunter',
                            'Elite Hunter',
                            'Master Hunter',
                            'Legendary Hunter'
                        ]
                    }
                },
                'boss_kills': {
                    'title': 'Boss Slayer',
                    'tiers': [5, 25, 50, 100, 200],
                    'rewards': {
                        'crystals': [200, 1000, 2000, 4000, 8000],
                        'titles': [
                            'Boss Challenger',
                            'Boss Fighter',
                            'Boss Slayer',
                            'Boss Master',
                            'Boss Legend'
                        ]
                    }
                }
            },
            'progression': {
                'level_milestones': {
                    'title': 'Level Achiever',
                    'tiers': [10, 50, 100, 200, 500],
                    'rewards': {
                        'crystals': [100, 500, 1000, 2000, 5000],
                        'titles': [
                            'Adventurer',
                            'Veteran',
                            'Elite',
                            'Master',
                            'Legend'
                        ]
                    }
                },
                'equipment_upgrades': {
                    'title': 'Equipment Master',
                    'tiers': [10, 50, 100, 200, 500],
                    'rewards': {
                        'crystals': [100, 500, 1000, 2000, 5000],
                        'titles': [
                            'Apprentice Smith',
                            'Journeyman Smith',
                            'Expert Smith',
                            'Master Smith',
                            'Legendary Smith'
                        ]
                    }
                }
            },
            'social': {
                'party_activities': {
                    'title': 'Team Player',
                    'tiers': [10, 50, 100, 200, 500],
                    'rewards': {
                        'crystals': [100, 500, 1000, 2000, 5000],
                        'titles': [
                            'Party Member',
                            'Party Veteran',
                            'Party Expert',
                            'Party Master',
                            'Party Legend'
                        ]
                    }
                },
                'guild_contributions': {
                    'title': 'Guild Contributor',
                    'tiers': [10, 50, 100, 200, 500],
                    'rewards': {
                        'crystals': [100, 500, 1000, 2000, 5000],
                        'titles': [
                            'Guild Supporter',
                            'Guild Contributor',
                            'Guild Pillar',
                            'Guild Champion',
                            'Guild Legend'
                        ]
                    }
                }
            },
            'economy': {
                'market_trades': {
                    'title': 'Market Trader',
                    'tiers': [10, 50, 100, 200, 500],
                    'rewards': {
                        'crystals': [100, 500, 1000, 2000, 5000],
                        'titles': [
                            'Market Novice',
                            'Market Trader',
                            'Market Expert',
                            'Market Master',
                            'Market Mogul'
                        ]
                    }
                },
                'crystal_milestones': {
                    'title': 'Crystal Hoarder',
                    'tiers': [1000, 10000, 100000, 1000000, 10000000],
                    'rewards': {
                        'crystals': [100, 1000, 10000, 100000, 1000000],
                        'titles': [
                            'Crystal Collector',
                            'Crystal Accumulator',
                            'Crystal Magnate',
                            'Crystal Baron',
                            'Crystal Emperor'
                        ]
                    }
                }
            }
        }

    def check_achievements(self, user: User) -> Dict:
        """Check and update user achievements"""
        try:
            # Get AI insights
            profile = self.ai_agent.analyze_player(user)
            if not profile:
                return {
                    "success": False,
                    "message": "Failed to analyze player profile"
                }

            completed_achievements = []

            # Check each category
            for category, achievements in self.achievement_categories.items():
                for achievement_type, config in achievements.items():
                    result = self._check_achievement_progress(
                        user, category, achievement_type, config, profile
                    )
                    if result["completed"]:
                        completed_achievements.extend(result["achievements"])

            if completed_achievements:
                return {
                    "success": True,
                    "message": "New achievements completed!",
                    "achievements": completed_achievements
                }
            
            return {
                "success": True,
                "message": "No new achievements completed",
                "achievements": []
            }

        except Exception as e:
            logger.error(f"Failed to check achievements: {str(e)}")
            return {
                "success": False,
                "message": "Failed to check achievements"
            }

    def get_achievements(self, user: User) -> Dict:
        """Get user's achievement progress"""
        try:
            achievements = Achievement.query.filter_by(user_id=user.id).all()
            
            # Get AI evaluation for each achievement
            achievement_data = []
            for achievement in achievements:
                evaluation = self.ai_agent.evaluate_achievement_progress(
                    user, achievement.id
                )
                
                achievement_data.append({
                    "id": achievement.id,
                    "category": achievement.category,
                    "type": achievement.type,
                    "title": achievement.title,
                    "description": achievement.description,
                    "progress": evaluation["progress"],
                    "completed": achievement.completed_at is not None,
                    "completed_at": (
                        achievement.completed_at.isoformat()
                        if achievement.completed_at else None
                    ),
                    "rewards": achievement.rewards,
                    "insights": evaluation.get("insights", {}),
                    "estimated_completion": evaluation.get("estimated_completion")
                })

            return {
                "success": True,
                "achievements": achievement_data
            }

        except Exception as e:
            logger.error(f"Failed to get achievements: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get achievements"
            }

    def _check_achievement_progress(
        self, user: User, category: str, achievement_type: str,
        config: Dict, profile: Dict
    ) -> Dict:
        """Check progress for specific achievement type"""
        try:
            completed = []
            
            # Get current achievement progress
            current_value = self._get_achievement_value(
                user, category, achievement_type
            )
            
            # Get existing achievements
            existing = Achievement.query.filter_by(
                user_id=user.id,
                category=category,
                type=achievement_type
            ).all()
            completed_tiers = {a.tier for a in existing if a.completed_at}
            
            # Check each tier
            for i, threshold in enumerate(config['tiers']):
                if i in completed_tiers:
                    continue
                    
                if current_value >= threshold:
                    # Create achievement
                    achievement = Achievement(
                        user_id=user.id,
                        category=category,
                        type=achievement_type,
                        tier=i,
                        title=f"{config['title']} {i+1}",
                        description=f"Reach {threshold} {achievement_type}",
                        rewards={
                            'crystals': config['rewards']['crystals'][i],
                            'title': config['rewards']['titles'][i]
                        },
                        progress_data=json.dumps({
                            'current': current_value,
                            'required': threshold
                        }),
                        completed_at=datetime.utcnow()
                    )
                    db.session.add(achievement)
                    
                    # Grant rewards
                    self._grant_achievement_rewards(user, achievement)
                    
                    completed.append({
                        "title": achievement.title,
                        "description": achievement.description,
                        "rewards": achievement.rewards
                    })

            if completed:
                db.session.commit()

            return {
                "completed": bool(completed),
                "achievements": completed
            }

        except Exception as e:
            logger.error(f"Failed to check achievement progress: {str(e)}")
            db.session.rollback()
            return {
                "completed": False,
                "achievements": []
            }

    def _get_achievement_value(self, user: User, category: str, achievement_type: str) -> int:
        """Get current value for achievement type"""
        try:
            if category == 'combat':
                if achievement_type == 'gate_completions':
                    return Gate.query.filter_by(
                        status='completed'
                    ).filter(
                        Gate.current_players.contains(user)
                    ).count()
                elif achievement_type == 'boss_kills':
                    return Gate.query.filter_by(
                        status='completed',
                        is_boss=True
                    ).filter(
                        Gate.current_players.contains(user)
                    ).count()
                    
            elif category == 'progression':
                if achievement_type == 'level_milestones':
                    return user.level
                elif achievement_type == 'equipment_upgrades':
                    return Transaction.query.filter_by(
                        user_id=user.id,
                        type='equipment_upgrade',
                    ).filter(
                        Transaction.metadata['success'].as_boolean() == True
                    ).count()
                    
            elif category == 'social':
                if achievement_type == 'party_activities':
                    return Gate.query.filter(
                        Gate.status == 'completed',
                        Gate.current_players.contains(user),
                        Gate.party_id.isnot(None)
                    ).count()
                elif achievement_type == 'guild_contributions':
                    return Transaction.query.filter_by(
                        user_id=user.id,
                        type='guild_contribution'
                    ).count()
                    
            elif category == 'economy':
                if achievement_type == 'market_trades':
                    return Transaction.query.filter_by(
                        user_id=user.id,
                        type='market_trade'
                    ).count()
                elif achievement_type == 'crystal_milestones':
                    return user.crystals

            return 0

        except Exception as e:
            logger.error(f"Failed to get achievement value: {str(e)}")
            return 0

    def _grant_achievement_rewards(self, user: User, achievement: Achievement) -> None:
        """Grant rewards for completed achievement"""
        try:
            # Grant crystals
            if 'crystals' in achievement.rewards:
                user.crystals += achievement.rewards['crystals']
                
                # Record transaction
                transaction = Transaction(
                    user_id=user.id,
                    type='achievement_reward',
                    currency='crystals',
                    amount=achievement.rewards['crystals'],
                    metadata={
                        'achievement_id': achievement.id,
                        'achievement_title': achievement.title
                    }
                )
                db.session.add(transaction)

            # Grant title
            if 'title' in achievement.rewards:
                if not user.titles:
                    user.titles = []
                user.titles.append(achievement.rewards['title'])

        except Exception as e:
            logger.error(f"Failed to grant achievement rewards: {str(e)}")
            raise

    def generate_personal_achievements(self, user: User) -> Dict:
        """Generate AI-driven personal achievements"""
        try:
            # Get AI insights
            profile = self.ai_agent.analyze_player(user)
            if not profile:
                return {
                    "success": False,
                    "message": "Failed to analyze player profile"
                }

            # Generate achievements based on player behavior
            achievements = []
            
            # Activity-based achievements
            preferred_activity = profile['activity_patterns'].get('preferred_activity')
            if preferred_activity:
                achievements.append(self._create_activity_achievement(
                    user, preferred_activity, profile
                ))
            
            # Performance-based achievements
            if profile['performance_metrics']['efficiency_score'] > 0.8:
                achievements.append(self._create_performance_achievement(
                    user, profile
                ))
            
            # Risk-based achievements
            if profile['risk_profile']['risk_tolerance_score'] > 0.7:
                achievements.append(self._create_risk_achievement(
                    user, profile
                ))

            # Filter out None values and commit
            achievements = [a for a in achievements if a]
            if achievements:
                db.session.add_all(achievements)
                db.session.commit()

            return {
                "success": True,
                "message": "Personal achievements generated",
                "achievements": [
                    {
                        "title": a.title,
                        "description": a.description,
                        "rewards": a.rewards
                    }
                    for a in achievements
                ]
            }

        except Exception as e:
            logger.error(f"Failed to generate personal achievements: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to generate personal achievements"
            }

    def _create_activity_achievement(
        self, user: User, activity: str, profile: Dict
    ) -> Optional[Achievement]:
        """Create achievement based on preferred activity"""
        try:
            activity_count = profile['activity_patterns']['total_actions']
            if activity_count < 50:  # Minimum threshold
                return None

            return Achievement(
                user_id=user.id,
                category='personal',
                type='activity_specialist',
                tier=0,
                title=f"{activity.title()} Specialist",
                description=f"Complete {activity_count} {activity} activities",
                rewards={
                    'crystals': min(activity_count * 10, 5000),
                    'title': f"{activity.title()} Expert"
                },
                progress_data=json.dumps({
                    'current': activity_count,
                    'required': activity_count
                })
            )

        except Exception:
            return None

    def _create_performance_achievement(
        self, user: User, profile: Dict
    ) -> Optional[Achievement]:
        """Create achievement based on performance"""
        try:
            efficiency = profile['performance_metrics']['efficiency_score']
            completion_rate = profile['performance_metrics']['completion_rate']
            
            if efficiency < 0.8 or completion_rate < 0.8:
                return None

            return Achievement(
                user_id=user.id,
                category='personal',
                type='performance_master',
                tier=0,
                title="Performance Master",
                description=(
                    f"Maintain {int(efficiency*100)}% efficiency and "
                    f"{int(completion_rate*100)}% completion rate"
                ),
                rewards={
                    'crystals': 2000,
                    'title': "Efficiency Expert"
                },
                progress_data=json.dumps({
                    'efficiency': efficiency,
                    'completion_rate': completion_rate
                })
            )

        except Exception:
            return None

    def _create_risk_achievement(
        self, user: User, profile: Dict
    ) -> Optional[Achievement]:
        """Create achievement based on risk-taking"""
        try:
            risk_score = profile['risk_profile']['risk_tolerance_score']
            high_gates = profile['risk_profile']['high_grade_gate_frequency']
            
            if risk_score < 0.7 or high_gates < 10:
                return None

            return Achievement(
                user_id=user.id,
                category='personal',
                type='risk_taker',
                tier=0,
                title="Fearless Challenger",
                description=f"Complete {high_gates} high-grade gates",
                rewards={
                    'crystals': high_gates * 100,
                    'title': "Fearless"
                },
                progress_data=json.dumps({
                    'high_gates': high_gates,
                    'risk_score': risk_score
                })
            )

        except Exception:
            return None
