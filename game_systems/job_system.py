"""
Job System for Terminusa Online
"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import random
import logging
from models import db, User, Job, JobQuest, Item
from game_systems.ai_agent import AIAgent
from game_config import (
    JOB_CLASSES,
    ELEMENTS,
    JOB_LICENSE_COST,
    JOB_RESET_COST
)

logger = logging.getLogger(__name__)

class JobSystem:
    """Handles job classes, progression, and job-specific quests"""
    
    def __init__(self):
        self.ai_agent = AIAgent()
        self._job_requirements = {
            # Base Classes
            'Fighter': {'level': 1},
            'Mage': {'level': 1},
            'Assassin': {'level': 1},
            'Archer': {'level': 1},
            'Healer': {'level': 1},
            
            # Advanced Classes
            'Berserker': {
                'base_class': 'Fighter',
                'level': 50,
                'requirements': {'strength': 80, 'vitality': 60}
            },
            'Paladin': {
                'base_class': 'Fighter',
                'level': 50,
                'requirements': {'vitality': 80, 'spirit': 60}
            },
            'Archmage': {
                'base_class': 'Mage',
                'level': 50,
                'requirements': {'intelligence': 80, 'wisdom': 60}
            },
            'Shadow Monarch': {
                'base_class': ['Fighter', 'Mage', 'Assassin'],
                'level': 100,
                'requirements': {
                    'shadow_affinity': 90,
                    'gate_completions': 100,
                    'boss_kills': 50
                }
            }
        }

    def change_job(self, user: User, new_job: str) -> Dict:
        """Change user's job class"""
        try:
            # Check if user has a job license
            if user.job_licenses <= 0:
                return {
                    "success": False,
                    "message": "Job license required"
                }

            # Validate job exists
            if new_job not in self._job_requirements:
                return {
                    "success": False,
                    "message": "Invalid job class"
                }

            # Check requirements
            requirements_met = self._check_job_requirements(user, new_job)
            if not requirements_met['success']:
                return requirements_met

            # Store old job for quest generation
            old_job = user.job_class

            # Update job
            user.job_class = new_job
            user.job_level = 1
            user.job_experience = 0
            user.job_licenses -= 1

            # Update stats based on new job
            self._update_job_stats(user)

            # Generate job change quest
            self._generate_job_change_quest(user, old_job, new_job)

            db.session.commit()

            return {
                "success": True,
                "message": f"Successfully changed job to {new_job}",
                "stats": self._get_job_stats(user)
            }

        except Exception as e:
            logger.error(f"Failed to change job: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to change job"
            }

    def reset_job(self, user: User) -> Dict:
        """Reset job and return to base class"""
        try:
            # Check if user has reset license
            if user.job_reset_licenses <= 0:
                return {
                    "success": False,
                    "message": "Job reset license required"
                }

            # Get base class
            base_class = self._get_base_class(user.job_class)
            if not base_class:
                return {
                    "success": False,
                    "message": "Cannot reset current job"
                }

            # Reset job
            user.job_class = base_class
            user.job_level = 1
            user.job_experience = 0
            user.job_reset_licenses -= 1

            # Reset stats to base values
            self._update_job_stats(user)

            db.session.commit()

            return {
                "success": True,
                "message": f"Successfully reset to {base_class}",
                "stats": self._get_job_stats(user)
            }

        except Exception as e:
            logger.error(f"Failed to reset job: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to reset job"
            }

    def gain_job_experience(self, user: User, amount: int) -> Dict:
        """Add job experience and handle level ups"""
        try:
            user.job_experience += amount
            
            # Check for level ups
            while self._check_job_level_up(user):
                user.job_level += 1
                self._apply_level_up_bonuses(user)
                
                # Generate job quest every 50 levels
                if user.job_level % 50 == 0:
                    self._generate_milestone_quest(user)

            db.session.commit()

            return {
                "success": True,
                "message": f"Gained {amount} job experience",
                "current_level": user.job_level,
                "current_exp": user.job_experience,
                "next_level_exp": self._get_next_level_exp(user)
            }

        except Exception as e:
            logger.error(f"Failed to gain job experience: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to gain job experience"
            }

    def get_available_jobs(self, user: User) -> Dict:
        """Get list of jobs available to user"""
        try:
            available_jobs = []
            for job, requirements in self._job_requirements.items():
                # Skip current job
                if job == user.job_class:
                    continue
                    
                # Check requirements
                meets_requirements = self._check_job_requirements(user, job)
                
                available_jobs.append({
                    'name': job,
                    'available': meets_requirements['success'],
                    'requirements': requirements,
                    'missing': meets_requirements.get('missing', [])
                })

            return {
                "success": True,
                "available_jobs": available_jobs
            }

        except Exception as e:
            logger.error(f"Failed to get available jobs: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get available jobs"
            }

    def get_job_skills(self, user: User) -> Dict:
        """Get skills available for user's job"""
        try:
            job_config = JOB_CLASSES.get(user.job_class)
            if not job_config:
                return {
                    "success": False,
                    "message": "Invalid job class"
                }

            # Get available skills based on level
            available_skills = []
            for skill in job_config.get('skills', []):
                if user.job_level >= skill['level_requirement']:
                    available_skills.append({
                        'name': skill['name'],
                        'description': skill['description'],
                        'damage': skill.get('damage'),
                        'mana_cost': skill.get('mana_cost'),
                        'cooldown': skill.get('cooldown'),
                        'element': skill.get('element'),
                        'status_effects': skill.get('status_effects', {})
                    })

            return {
                "success": True,
                "skills": available_skills
            }

        except Exception as e:
            logger.error(f"Failed to get job skills: {str(e)}")
            return {
                "success": False,
                "message": "Failed to get job skills"
            }

    def _check_job_requirements(self, user: User, job: str) -> Dict:
        """Check if user meets job requirements"""
        requirements = self._job_requirements.get(job)
        if not requirements:
            return {
                "success": False,
                "message": "Invalid job class"
            }

        missing = []

        # Check level requirement
        if user.level < requirements['level']:
            missing.append(f"Level {requirements['level']} required")

        # Check base class requirement
        if 'base_class' in requirements:
            base_classes = (
                [requirements['base_class']]
                if isinstance(requirements['base_class'], str)
                else requirements['base_class']
            )
            if user.job_class not in base_classes:
                missing.append(f"Must be one of: {', '.join(base_classes)}")

        # Check stat requirements
        for stat, value in requirements.get('requirements', {}).items():
            user_value = getattr(user, stat, 0)
            if user_value < value:
                missing.append(f"{stat.title()}: {user_value}/{value}")

        return {
            "success": len(missing) == 0,
            "message": "Requirements not met" if missing else "Requirements met",
            "missing": missing
        }

    def _get_base_class(self, job_class: str) -> Optional[str]:
        """Get base class for advanced job"""
        for job, requirements in self._job_requirements.items():
            base_class = requirements.get('base_class')
            if isinstance(base_class, str) and job == job_class:
                return base_class
            elif isinstance(base_class, list) and job == job_class:
                return base_class[0]  # Return first base class
        return None

    def _check_job_level_up(self, user: User) -> bool:
        """Check if user can level up job"""
        next_level_exp = self._get_next_level_exp(user)
        return user.job_experience >= next_level_exp

    def _get_next_level_exp(self, user: User) -> int:
        """Calculate experience needed for next job level"""
        return int(100 * (user.job_level ** 1.5))

    def _update_job_stats(self, user: User) -> None:
        """Update user stats based on job"""
        job_config = JOB_CLASSES[user.job_class]
        
        # Base stats
        user.max_hp = job_config['base_hp']
        user.max_mp = job_config['base_mp']
        user.attack = job_config['base_attack']
        user.defense = job_config['base_defense']
        
        # Level bonuses
        user.max_hp += int(job_config['hp_per_level'] * (user.job_level - 1))
        user.max_mp += int(job_config['mp_per_level'] * (user.job_level - 1))
        
        # Heal to full on job change
        user.hp = user.max_hp
        user.mp = user.max_mp

    def _apply_level_up_bonuses(self, user: User) -> None:
        """Apply bonuses on job level up"""
        job_config = JOB_CLASSES[user.job_class]
        
        user.max_hp += int(job_config['hp_per_level'])
        user.max_mp += int(job_config['mp_per_level'])
        
        # Heal percentage of HP/MP on level up
        user.hp += int(user.max_hp * 0.3)  # 30% heal
        user.mp += int(user.max_mp * 0.3)
        
        # Cap at max
        user.hp = min(user.hp, user.max_hp)
        user.mp = min(user.mp, user.max_mp)

    def _generate_job_change_quest(self, user: User, old_job: str, new_job: str) -> None:
        """Generate quest for job change"""
        try:
            # Use AI to generate appropriate quest
            quest_params = self.ai_agent.generate_quest(user)
            if not quest_params['success']:
                return

            quest = JobQuest(
                user_id=user.id,
                type='job_change',
                title=f"Master the Way of the {new_job}",
                description=f"Prove your worth as a {new_job} after leaving the path of {old_job}",
                parameters=quest_params['quest']['parameters'],
                rewards=quest_params['quest']['rewards'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            db.session.add(quest)
            db.session.commit()

        except Exception as e:
            logger.error(f"Failed to generate job change quest: {str(e)}")

    def _generate_milestone_quest(self, user: User) -> None:
        """Generate quest for job level milestone"""
        try:
            # Use AI to generate appropriate quest
            quest_params = self.ai_agent.generate_quest(user)
            if not quest_params['success']:
                return

            quest = JobQuest(
                user_id=user.id,
                type='job_milestone',
                title=f"Path of the {user.job_class} - Level {user.job_level}",
                description=f"Complete this trial to prove your mastery as a level {user.job_level} {user.job_class}",
                parameters=quest_params['quest']['parameters'],
                rewards=quest_params['quest']['rewards'],
                expires_at=datetime.utcnow() + timedelta(days=7)
            )
            
            db.session.add(quest)
            db.session.commit()

        except Exception as e:
            logger.error(f"Failed to generate milestone quest: {str(e)}")

    def _get_job_stats(self, user: User) -> Dict:
        """Get current job stats"""
        return {
            'job_class': user.job_class,
            'job_level': user.job_level,
            'job_experience': user.job_experience,
            'next_level_exp': self._get_next_level_exp(user),
            'hp': user.hp,
            'max_hp': user.max_hp,
            'mp': user.mp,
            'max_mp': user.max_mp,
            'attack': user.attack,
            'defense': user.defense
        }
