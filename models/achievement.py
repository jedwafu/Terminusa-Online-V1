"""
Achievement model for Terminusa Online
"""
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class AchievementType(Enum):
    COMBAT = "combat"
    EXPLORATION = "exploration"
    SOCIAL = "social"
    CRAFTING = "crafting"
    COLLECTION = "collection"
    PROGRESSION = "progression"
    SPECIAL = "special"

class AchievementTier(Enum):
    BRONZE = "bronze"
    SILVER = "silver"
    GOLD = "gold"
    PLATINUM = "platinum"
    DIAMOND = "diamond"

class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Achievement Info
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255), nullable=False)
    type = db.Column(db.Enum(AchievementType), nullable=False)
    tier = db.Column(db.Enum(AchievementTier), nullable=False)
    
    # Progress Tracking
    current_progress = db.Column(db.Integer, default=0)
    target_progress = db.Column(db.Integer, nullable=False)
    completed = db.Column(db.Boolean, default=False)
    
    # Rewards
    rewards = db.Column(JSONB, nullable=False, default={})
    rewards_claimed = db.Column(db.Boolean, default=False)
    
    # Achievement Chain
    part_of_series = db.Column(db.Boolean, default=False)
    series_id = db.Column(db.String(50), nullable=True)
    series_order = db.Column(db.Integer, nullable=True)
    next_achievement_id = db.Column(db.Integer, nullable=True)
    
    # Metadata
    hidden = db.Column(db.Boolean, default=False)
    legacy = db.Column(db.Boolean, default=False)
    limited_time = db.Column(db.Boolean, default=False)
    expiry_date = db.Column(db.DateTime, nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, user_id: int, name: str, description: str, 
                 type: AchievementType, tier: AchievementTier, 
                 target_progress: int, rewards: Dict):
        self.user_id = user_id
        self.name = name
        self.description = description
        self.type = type
        self.tier = tier
        self.target_progress = target_progress
        self.rewards = rewards

    def update_progress(self, amount: int = 1) -> Dict:
        """Update achievement progress"""
        if self.completed:
            return {
                'success': False,
                'message': 'Achievement already completed'
            }
            
        if self.limited_time and self.expiry_date and datetime.utcnow() > self.expiry_date:
            return {
                'success': False,
                'message': 'Achievement expired'
            }
            
        old_progress = self.current_progress
        self.current_progress = min(self.current_progress + amount, self.target_progress)
        
        # Check if achievement completed
        if self.current_progress >= self.target_progress:
            self.completed = True
            self.completed_at = datetime.utcnow()
            
            return {
                'success': True,
                'message': 'Achievement completed!',
                'completed': True,
                'rewards': self.rewards
            }
            
        return {
            'success': True,
            'message': 'Progress updated',
            'completed': False,
            'old_progress': old_progress,
            'new_progress': self.current_progress
        }

    def claim_rewards(self) -> Dict:
        """Claim achievement rewards"""
        if not self.completed:
            return {
                'success': False,
                'message': 'Achievement not completed'
            }
            
        if self.rewards_claimed:
            return {
                'success': False,
                'message': 'Rewards already claimed'
            }
            
        self.rewards_claimed = True
        
        return {
            'success': True,
            'message': 'Rewards claimed successfully',
            'rewards': self.rewards
        }

    def is_available(self) -> bool:
        """Check if achievement is available"""
        if self.completed:
            return False
            
        if self.limited_time and self.expiry_date and datetime.utcnow() > self.expiry_date:
            return False
            
        if self.legacy:
            return False
            
        return True

    def get_progress_percentage(self) -> float:
        """Get achievement progress as percentage"""
        if self.target_progress == 0:
            return 0
        return (self.current_progress / self.target_progress) * 100

    def get_next_in_series(self) -> Optional['Achievement']:
        """Get next achievement in series"""
        if not self.part_of_series or not self.next_achievement_id:
            return None
            
        return Achievement.query.get(self.next_achievement_id)

    def to_dict(self) -> Dict:
        """Convert achievement data to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'type': self.type.value,
            'tier': self.tier.value,
            'progress': {
                'current': self.current_progress,
                'target': self.target_progress,
                'percentage': self.get_progress_percentage()
            },
            'completed': self.completed,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'rewards': self.rewards,
            'rewards_claimed': self.rewards_claimed,
            'series_info': {
                'part_of_series': self.part_of_series,
                'series_id': self.series_id,
                'series_order': self.series_order,
                'has_next': bool(self.next_achievement_id)
            } if self.part_of_series else None,
            'metadata': {
                'hidden': self.hidden,
                'legacy': self.legacy,
                'limited_time': self.limited_time,
                'expiry_date': self.expiry_date.isoformat() if self.expiry_date else None
            }
        }

    @classmethod
    def create_series(cls, user_id: int, series_id: str, 
                     achievements: List[Dict]) -> List['Achievement']:
        """Create a series of related achievements"""
        created = []
        previous_id = None
        
        for i, achievement_data in enumerate(achievements, 1):
            achievement = cls(
                user_id=user_id,
                name=achievement_data['name'],
                description=achievement_data['description'],
                type=achievement_data['type'],
                tier=achievement_data['tier'],
                target_progress=achievement_data['target_progress'],
                rewards=achievement_data['rewards']
            )
            
            achievement.part_of_series = True
            achievement.series_id = series_id
            achievement.series_order = i
            
            if previous_id:
                achievement.previous_achievement_id = previous_id
                
            db.session.add(achievement)
            db.session.flush()  # Get achievement.id
            
            if previous_id:
                # Link previous achievement to this one
                previous_achievement = cls.query.get(previous_id)
                previous_achievement.next_achievement_id = achievement.id
                
            previous_id = achievement.id
            created.append(achievement)
            
        db.session.commit()
        return created
