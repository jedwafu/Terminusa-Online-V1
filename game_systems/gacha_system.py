"""
Gacha System for Terminusa Online
"""
from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
import random
import logging
from models import db, User, Mount, Pet, Transaction
from game_systems.ai_agent import AIAgent

logger = logging.getLogger(__name__)

class GachaSystem:
    """Handles mount and pet gacha mechanics"""
    
    def __init__(self):
        self.ai_agent = AIAgent()
        self.mount_pool = {
            'Immortal': {
                'base_rate': 0.01,  # 1%
                'mounts': [
                    {
                        'id': 'shadow_dragon',
                        'name': 'Shadow Dragon',
                        'speed_bonus': 100,
                        'combat_bonus': 50,
                        'special_ability': 'shadow_flight'
                    },
                    {
                        'id': 'phoenix',
                        'name': 'Phoenix',
                        'speed_bonus': 90,
                        'combat_bonus': 60,
                        'special_ability': 'resurrection'
                    }
                ]
            },
            'Legendary': {
                'base_rate': 0.05,  # 5%
                'mounts': [
                    {
                        'id': 'griffin',
                        'name': 'Griffin',
                        'speed_bonus': 80,
                        'combat_bonus': 40,
                        'special_ability': 'aerial_combat'
                    },
                    {
                        'id': 'celestial_horse',
                        'name': 'Celestial Horse',
                        'speed_bonus': 85,
                        'combat_bonus': 35,
                        'special_ability': 'teleport'
                    }
                ]
            },
            'Epic': {
                'base_rate': 0.15,  # 15%
                'mounts': [
                    {
                        'id': 'dire_wolf',
                        'name': 'Dire Wolf',
                        'speed_bonus': 70,
                        'combat_bonus': 30,
                        'special_ability': 'pack_tactics'
                    },
                    {
                        'id': 'armored_bear',
                        'name': 'Armored Bear',
                        'speed_bonus': 60,
                        'combat_bonus': 40,
                        'special_ability': 'intimidate'
                    }
                ]
            },
            'Rare': {
                'base_rate': 0.30,  # 30%
                'mounts': [
                    {
                        'id': 'war_horse',
                        'name': 'War Horse',
                        'speed_bonus': 50,
                        'combat_bonus': 20,
                        'special_ability': 'charge'
                    },
                    {
                        'id': 'giant_elk',
                        'name': 'Giant Elk',
                        'speed_bonus': 55,
                        'combat_bonus': 15,
                        'special_ability': 'forest_stride'
                    }
                ]
            },
            'Common': {
                'base_rate': 0.49,  # 49%
                'mounts': [
                    {
                        'id': 'horse',
                        'name': 'Horse',
                        'speed_bonus': 40,
                        'combat_bonus': 10,
                        'special_ability': None
                    },
                    {
                        'id': 'mule',
                        'name': 'Mule',
                        'speed_bonus': 35,
                        'combat_bonus': 5,
                        'special_ability': None
                    }
                ]
            }
        }
        
        self.pet_pool = {
            'Immortal': {
                'base_rate': 0.01,  # 1%
                'pets': [
                    {
                        'id': 'baby_dragon',
                        'name': 'Baby Dragon',
                        'combat_bonus': 50,
                        'loot_bonus': 30,
                        'special_ability': 'elemental_breath'
                    },
                    {
                        'id': 'spirit_fox',
                        'name': 'Spirit Fox',
                        'combat_bonus': 45,
                        'loot_bonus': 35,
                        'special_ability': 'spirit_sight'
                    }
                ]
            },
            'Legendary': {
                'base_rate': 0.05,  # 5%
                'pets': [
                    {
                        'id': 'fairy',
                        'name': 'Fairy',
                        'combat_bonus': 40,
                        'loot_bonus': 25,
                        'special_ability': 'healing_light'
                    },
                    {
                        'id': 'shadow_cat',
                        'name': 'Shadow Cat',
                        'combat_bonus': 35,
                        'loot_bonus': 30,
                        'special_ability': 'stealth'
                    }
                ]
            },
            'Epic': {
                'base_rate': 0.15,  # 15%
                'pets': [
                    {
                        'id': 'battle_hawk',
                        'name': 'Battle Hawk',
                        'combat_bonus': 30,
                        'loot_bonus': 20,
                        'special_ability': 'scout'
                    },
                    {
                        'id': 'mystic_snake',
                        'name': 'Mystic Snake',
                        'combat_bonus': 25,
                        'loot_bonus': 25,
                        'special_ability': 'poison'
                    }
                ]
            },
            'Rare': {
                'base_rate': 0.30,  # 30%
                'pets': [
                    {
                        'id': 'hunting_dog',
                        'name': 'Hunting Dog',
                        'combat_bonus': 20,
                        'loot_bonus': 15,
                        'special_ability': 'track'
                    },
                    {
                        'id': 'magic_cat',
                        'name': 'Magic Cat',
                        'combat_bonus': 15,
                        'loot_bonus': 20,
                        'special_ability': 'luck'
                    }
                ]
            },
            'Common': {
                'base_rate': 0.49,  # 49%
                'pets': [
                    {
                        'id': 'dog',
                        'name': 'Dog',
                        'combat_bonus': 10,
                        'loot_bonus': 10,
                        'special_ability': None
                    },
                    {
                        'id': 'cat',
                        'name': 'Cat',
                        'combat_bonus': 5,
                        'loot_bonus': 15,
                        'special_ability': None
                    }
                ]
            }
        }

    def summon_mount(self, user: User) -> Dict:
        """Summon a mount using crystals"""
        try:
            cost = 1000  # Cost in crystals
            
            # Check if user has enough crystals
            if user.crystals < cost:
                return {
                    "success": False,
                    "message": f"Insufficient crystals. Need {cost}"
                }

            # Get AI-adjusted probabilities
            probabilities = self._calculate_mount_probabilities(user)
            
            # Determine grade
            grade = self._determine_grade(probabilities)
            
            # Select random mount from grade
            mount_data = random.choice(self.mount_pool[grade]['mounts'])
            
            # Create mount
            mount = Mount(
                user_id=user.id,
                mount_id=mount_data['id'],
                name=mount_data['name'],
                grade=grade,
                speed_bonus=mount_data['speed_bonus'],
                combat_bonus=mount_data['combat_bonus'],
                special_ability=mount_data['special_ability'],
                obtained_at=datetime.utcnow()
            )
            db.session.add(mount)
            
            # Deduct crystals
            user.crystals -= cost
            
            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type='mount_summon',
                currency='crystals',
                amount=cost,
                metadata={
                    'mount_id': mount_data['id'],
                    'grade': grade
                }
            )
            db.session.add(transaction)

            db.session.commit()

            return {
                "success": True,
                "message": f"Successfully summoned {grade} mount: {mount_data['name']}",
                "mount": {
                    "id": mount.id,
                    "name": mount.name,
                    "grade": mount.grade,
                    "speed_bonus": mount.speed_bonus,
                    "combat_bonus": mount.combat_bonus,
                    "special_ability": mount.special_ability
                }
            }

        except Exception as e:
            logger.error(f"Failed to summon mount: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to summon mount"
            }

    def summon_pet(self, user: User) -> Dict:
        """Summon a pet using crystals"""
        try:
            cost = 800  # Cost in crystals
            
            # Check if user has enough crystals
            if user.crystals < cost:
                return {
                    "success": False,
                    "message": f"Insufficient crystals. Need {cost}"
                }

            # Get AI-adjusted probabilities
            probabilities = self._calculate_pet_probabilities(user)
            
            # Determine grade
            grade = self._determine_grade(probabilities)
            
            # Select random pet from grade
            pet_data = random.choice(self.pet_pool[grade]['pets'])
            
            # Create pet
            pet = Pet(
                user_id=user.id,
                pet_id=pet_data['id'],
                name=pet_data['name'],
                grade=grade,
                combat_bonus=pet_data['combat_bonus'],
                loot_bonus=pet_data['loot_bonus'],
                special_ability=pet_data['special_ability'],
                obtained_at=datetime.utcnow()
            )
            db.session.add(pet)
            
            # Deduct crystals
            user.crystals -= cost
            
            # Record transaction
            transaction = Transaction(
                user_id=user.id,
                type='pet_summon',
                currency='crystals',
                amount=cost,
                metadata={
                    'pet_id': pet_data['id'],
                    'grade': grade
                }
            )
            db.session.add(transaction)

            db.session.commit()

            return {
                "success": True,
                "message": f"Successfully summoned {grade} pet: {pet_data['name']}",
                "pet": {
                    "id": pet.id,
                    "name": pet.name,
                    "grade": pet.grade,
                    "combat_bonus": pet.combat_bonus,
                    "loot_bonus": pet.loot_bonus,
                    "special_ability": pet.special_ability
                }
            }

        except Exception as e:
            logger.error(f"Failed to summon pet: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": "Failed to summon pet"
            }

    def _calculate_mount_probabilities(self, user: User) -> Dict[str, float]:
        """Calculate AI-adjusted mount probabilities"""
        try:
            # Get base probabilities
            probabilities = {
                grade: info['base_rate']
                for grade, info in self.mount_pool.items()
            }
            
            # Get AI insights
            profile = self.ai_agent.analyze_player(user)
            if not profile:
                return probabilities

            # Calculate adjustments
            adjustments = {
                # Reward progression
                'progression': self._calculate_progression_adjustment(profile),
                
                # Balance for unlucky players
                'pity': self._calculate_pity_adjustment(user, 'mount'),
                
                # Activity bonus
                'activity': self._calculate_activity_adjustment(profile),
                
                # Special class bonus
                'class': self._calculate_class_adjustment(user)
            }
            
            # Apply adjustments to higher grades
            for grade in ['Immortal', 'Legendary', 'Epic']:
                total_adjustment = sum(adjustments.values())
                probabilities[grade] += total_adjustment / (
                    3 if grade == 'Epic' else
                    6 if grade == 'Legendary' else
                    12  # Immortal gets smallest boost
                )
            
            # Ensure probabilities sum to 1
            total = sum(probabilities.values())
            return {
                grade: prob / total
                for grade, prob in probabilities.items()
            }

        except Exception as e:
            logger.error(f"Failed to calculate mount probabilities: {str(e)}")
            return {
                grade: info['base_rate']
                for grade, info in self.mount_pool.items()
            }

    def _calculate_pet_probabilities(self, user: User) -> Dict[str, float]:
        """Calculate AI-adjusted pet probabilities"""
        try:
            # Get base probabilities
            probabilities = {
                grade: info['base_rate']
                for grade, info in self.pet_pool.items()
            }
            
            # Get AI insights
            profile = self.ai_agent.analyze_player(user)
            if not profile:
                return probabilities

            # Calculate adjustments
            adjustments = {
                # Reward progression
                'progression': self._calculate_progression_adjustment(profile),
                
                # Balance for unlucky players
                'pity': self._calculate_pity_adjustment(user, 'pet'),
                
                # Activity bonus
                'activity': self._calculate_activity_adjustment(profile),
                
                # Special class bonus
                'class': self._calculate_class_adjustment(user)
            }
            
            # Apply adjustments to higher grades
            for grade in ['Immortal', 'Legendary', 'Epic']:
                total_adjustment = sum(adjustments.values())
                probabilities[grade] += total_adjustment / (
                    3 if grade == 'Epic' else
                    6 if grade == 'Legendary' else
                    12  # Immortal gets smallest boost
                )
            
            # Ensure probabilities sum to 1
            total = sum(probabilities.values())
            return {
                grade: prob / total
                for grade, prob in probabilities.items()
            }

        except Exception as e:
            logger.error(f"Failed to calculate pet probabilities: {str(e)}")
            return {
                grade: info['base_rate']
                for grade, info in self.pet_pool.items()
            }

    def _calculate_progression_adjustment(self, profile: Dict) -> float:
        """Calculate progression-based probability adjustment"""
        try:
            progression_score = profile['progression_rate']['progression_score']
            
            if progression_score > 0.8:
                return 0.05  # +5%
            elif progression_score > 0.6:
                return 0.03  # +3%
            return 0.0

        except Exception:
            return 0.0

    def _calculate_pity_adjustment(self, user: User, summon_type: str) -> float:
        """Calculate pity-based probability adjustment"""
        try:
            # Get recent summons
            recent_summons = Transaction.query.filter(
                Transaction.user_id == user.id,
                Transaction.type == f'{summon_type}_summon',
                Transaction.created_at >= datetime.utcnow() - timedelta(days=7)
            ).all()
            
            if not recent_summons:
                return 0.0

            # Count high-grade summons
            high_grades = sum(
                1 for s in recent_summons
                if s.metadata['grade'] in ['Immortal', 'Legendary']
            )
            
            # Increase rates for unlucky players
            if len(recent_summons) >= 10 and high_grades == 0:
                return 0.05  # +5%
            elif len(recent_summons) >= 5 and high_grades == 0:
                return 0.03  # +3%
            return 0.0

        except Exception:
            return 0.0

    def _calculate_activity_adjustment(self, profile: Dict) -> float:
        """Calculate activity-based probability adjustment"""
        try:
            total_actions = profile['activity_patterns']['total_actions']
            
            if total_actions > 1000:
                return 0.05  # +5%
            elif total_actions > 500:
                return 0.03  # +3%
            elif total_actions > 100:
                return 0.01  # +1%
            return 0.0

        except Exception:
            return 0.0

    def _calculate_class_adjustment(self, user: User) -> float:
        """Calculate class-based probability adjustment"""
        try:
            # Special bonus for certain classes
            if user.job_class in ['Shadow Monarch', 'S-Rank Hunter']:
                return 0.05  # +5%
            elif user.job_class in ['Beast Master', 'Monster Tamer']:
                return 0.03  # +3%
            return 0.0

        except Exception:
            return 0.0

    def _determine_grade(self, probabilities: Dict[str, float]) -> str:
        """Determine summon grade based on probabilities"""
        roll = random.random()
        cumulative = 0
        
        for grade, chance in probabilities.items():
            cumulative += chance
            if roll <= cumulative:
                return grade
        
        return 'Common'  # Fallback
