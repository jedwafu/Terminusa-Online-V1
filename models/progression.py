"""
Progression models for Terminusa Online
"""
from typing import Dict, List, Optional
from datetime import datetime
from sqlalchemy.dialects.postgresql import JSONB

from models import db
from models.player import PlayerClass, JobType

class PlayerProgress(db.Model):
    __tablename__ = 'player_progress'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Overall Progress
    total_experience = db.Column(db.BigInteger, default=0)
    total_playtime = db.Column(db.Integer, default=0)  # minutes
    
    # Combat Stats
    monsters_killed = db.Column(db.Integer, default=0)
    bosses_killed = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    pvp_wins = db.Column(db.Integer, default=0)
    pvp_losses = db.Column(db.Integer, default=0)
    
    # Gate Progress
    gates_attempted = db.Column(db.Integer, default=0)
    gates_cleared = db.Column(db.Integer, default=0)
    highest_gate_rank = db.Column(db.String(2), nullable=True)
    gate_records = db.Column(JSONB, nullable=False, default={})
    
    # Quest Progress
    quests_completed = db.Column(db.Integer, default=0)
    quest_chains_completed = db.Column(db.Integer, default=0)
    active_quests = db.Column(JSONB, nullable=False, default=[])
    completed_quests = db.Column(JSONB, nullable=False, default=[])
    
    # Achievement Progress
    achievement_points = db.Column(db.Integer, default=0)
    achievement_count = db.Column(db.Integer, default=0)
    rare_achievements = db.Column(db.Integer, default=0)
    
    # Social Progress
    guild_contributions = db.Column(db.BigInteger, default=0)
    party_activities = db.Column(db.Integer, default=0)
    trade_count = db.Column(db.Integer, default=0)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)

    def update_combat_stats(self, stats: Dict) -> None:
        """Update combat statistics"""
        if 'monsters_killed' in stats:
            self.monsters_killed += stats['monsters_killed']
        if 'bosses_killed' in stats:
            self.bosses_killed += stats['bosses_killed']
        if 'deaths' in stats:
            self.deaths += stats['deaths']
        if 'pvp_wins' in stats:
            self.pvp_wins += stats['pvp_wins']
        if 'pvp_losses' in stats:
            self.pvp_losses += stats['pvp_losses']

    def update_gate_progress(self, gate_data: Dict) -> None:
        """Update gate progress"""
        self.gates_attempted += 1
        
        if gate_data.get('cleared', False):
            self.gates_cleared += 1
            
            # Update highest rank
            gate_rank = gate_data.get('rank')
            if gate_rank:
                if not self.highest_gate_rank or gate_rank > self.highest_gate_rank:
                    self.highest_gate_rank = gate_rank
            
            # Update gate records
            gate_type = gate_data.get('type')
            if gate_type:
                if gate_type not in self.gate_records:
                    self.gate_records[gate_type] = {
                        'attempts': 1,
                        'clears': 1,
                        'best_time': gate_data.get('clear_time'),
                        'highest_score': gate_data.get('score', 0)
                    }
                else:
                    record = self.gate_records[gate_type]
                    record['attempts'] += 1
                    record['clears'] += 1
                    
                    clear_time = gate_data.get('clear_time')
                    if clear_time and (not record['best_time'] or clear_time < record['best_time']):
                        record['best_time'] = clear_time
                        
                    score = gate_data.get('score', 0)
                    if score > record['highest_score']:
                        record['highest_score'] = score

    def update_quest_progress(self, quest_data: Dict) -> None:
        """Update quest progress"""
        if quest_data.get('completed', False):
            self.quests_completed += 1
            
            quest_id = quest_data.get('id')
            if quest_id:
                if quest_id in self.active_quests:
                    self.active_quests.remove(quest_id)
                self.completed_quests.append(quest_id)
                
            if quest_data.get('is_chain_complete', False):
                self.quest_chains_completed += 1

    def update_achievement_progress(self, achievement_data: Dict) -> None:
        """Update achievement progress"""
        self.achievement_count += 1
        self.achievement_points += achievement_data.get('points', 0)
        
        if achievement_data.get('is_rare', False):
            self.rare_achievements += 1

    def update_social_progress(self, activity_data: Dict) -> None:
        """Update social activity progress"""
        if 'guild_contribution' in activity_data:
            self.guild_contributions += activity_data['guild_contribution']
        if 'party_activity' in activity_data:
            self.party_activities += 1
        if 'trade' in activity_data:
            self.trade_count += 1

    def calculate_completion_percentage(self) -> float:
        """Calculate overall completion percentage"""
        total_points = 0
        earned_points = 0
        
        # Combat progress (30%)
        combat_weight = 0.3
        combat_metrics = {
            'monsters_killed': (self.monsters_killed, 1000),
            'bosses_killed': (self.bosses_killed, 100),
            'pvp_wins': (self.pvp_wins, 100)
        }
        for value, target in combat_metrics.values():
            total_points += target * combat_weight
            earned_points += min(value, target) * combat_weight
        
        # Gate progress (25%)
        gate_weight = 0.25
        gate_metrics = {
            'gates_cleared': (self.gates_cleared, 100),
            'highest_rank': (self._rank_to_points(), 7)  # S rank = 7 points
        }
        for value, target in gate_metrics.values():
            total_points += target * gate_weight
            earned_points += min(value, target) * gate_weight
        
        # Quest progress (20%)
        quest_weight = 0.2
        quest_metrics = {
            'quests_completed': (self.quests_completed, 200),
            'quest_chains': (self.quest_chains_completed, 20)
        }
        for value, target in quest_metrics.values():
            total_points += target * quest_weight
            earned_points += min(value, target) * quest_weight
        
        # Achievement progress (15%)
        achievement_weight = 0.15
        achievement_metrics = {
            'achievements': (self.achievement_count, 100),
            'rare_achievements': (self.rare_achievements, 20)
        }
        for value, target in achievement_metrics.values():
            total_points += target * achievement_weight
            earned_points += min(value, target) * achievement_weight
        
        # Social progress (10%)
        social_weight = 0.1
        social_metrics = {
            'guild_contributions': (self.guild_contributions, 10000),
            'party_activities': (self.party_activities, 100),
            'trades': (self.trade_count, 100)
        }
        for value, target in social_metrics.values():
            total_points += target * social_weight
            earned_points += min(value, target) * social_weight
        
        return (earned_points / total_points) * 100 if total_points > 0 else 0

    def _rank_to_points(self) -> int:
        """Convert gate rank to points"""
        rank_points = {
            'E': 1,
            'D': 2,
            'C': 3,
            'B': 4,
            'A': 5,
            'S': 6,
            'SS': 7
        }
        return rank_points.get(self.highest_gate_rank, 0)

    def to_dict(self) -> Dict:
        """Convert progress data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'overall': {
                'total_experience': self.total_experience,
                'total_playtime': self.total_playtime,
                'completion_percentage': self.calculate_completion_percentage()
            },
            'combat': {
                'monsters_killed': self.monsters_killed,
                'bosses_killed': self.bosses_killed,
                'deaths': self.deaths,
                'pvp': {
                    'wins': self.pvp_wins,
                    'losses': self.pvp_losses,
                    'ratio': self.pvp_wins / max(1, self.pvp_wins + self.pvp_losses)
                }
            },
            'gates': {
                'attempted': self.gates_attempted,
                'cleared': self.gates_cleared,
                'highest_rank': self.highest_gate_rank,
                'clear_rate': self.gates_cleared / max(1, self.gates_attempted),
                'records': self.gate_records
            },
            'quests': {
                'completed': self.quests_completed,
                'chains_completed': self.quest_chains_completed,
                'active': self.active_quests,
                'completed_list': self.completed_quests
            },
            'achievements': {
                'points': self.achievement_points,
                'count': self.achievement_count,
                'rare_count': self.rare_achievements
            },
            'social': {
                'guild_contributions': self.guild_contributions,
                'party_activities': self.party_activities,
                'trades': self.trade_count
            }
        }

class ClassProgress(db.Model):
    __tablename__ = 'class_progress'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    class_type = db.Column(db.Enum(PlayerClass), nullable=False)
    
    # Class Progress
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    mastery_points = db.Column(db.Integer, default=0)
    
    # Class Skills
    skills_unlocked = db.Column(JSONB, nullable=False, default=[])
    skill_points = db.Column(db.Integer, default=0)
    skill_tree = db.Column(JSONB, nullable=False, default={})
    
    # Class Stats
    monsters_killed = db.Column(db.Integer, default=0)
    bosses_killed = db.Column(db.Integer, default=0)
    deaths = db.Column(db.Integer, default=0)
    
    # Class Achievements
    achievements = db.Column(JSONB, nullable=False, default=[])
    titles = db.Column(JSONB, nullable=False, default=[])
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

    def gain_experience(self, amount: int) -> Dict:
        """Grant experience points to class"""
        self.experience += amount
        
        level_ups = 0
        while self._check_level_up():
            self._level_up()
            level_ups += 1
            
        return {
            'gained_exp': amount,
            'level_ups': level_ups,
            'current_level': self.level,
            'skill_points_gained': level_ups,
            'mastery_points_gained': level_ups
        }

    def _check_level_up(self) -> bool:
        """Check if class has enough exp to level up"""
        required_exp = self._get_required_exp()
        return self.experience >= required_exp

    def _get_required_exp(self) -> int:
        """Calculate required exp for next level"""
        return int(1000 * (1.2 ** (self.level - 1)))

    def _level_up(self):
        """Process class level up"""
        self.level += 1
        self.skill_points += 1
        self.mastery_points += 1

    def unlock_skill(self, skill_id: str) -> Dict:
        """Unlock a new skill"""
        if skill_id in self.skills_unlocked:
            return {
                'success': False,
                'message': 'Skill already unlocked'
            }
            
        if self.skill_points <= 0:
            return {
                'success': False,
                'message': 'No skill points available'
            }
            
        self.skills_unlocked.append(skill_id)
        self.skill_points -= 1
        
        return {
            'success': True,
            'message': 'Skill unlocked successfully',
            'remaining_points': self.skill_points
        }

    def to_dict(self) -> Dict:
        """Convert class progress data to dictionary"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'class_type': self.class_type.value,
            'progress': {
                'level': self.level,
                'experience': self.experience,
                'mastery_points': self.mastery_points
            },
            'skills': {
                'unlocked': self.skills_unlocked,
                'points': self.skill_points,
                'tree': self.skill_tree
            },
            'stats': {
                'monsters_killed': self.monsters_killed,
                'bosses_killed': self.bosses_killed,
                'deaths': self.deaths
            },
            'achievements': self.achievements,
            'titles': self.titles
        }

class JobProgress(db.Model):
    __tablename__ = 'job_progress'

    id = db.Column(db.Integer, primary_key=True)
    player_id = db.Column(db.Integer, db.ForeignKey('players.id'), nullable=False)
    job_type = db.Column(db.Enum(JobType), nullable=False)
    
    # Job Progress
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    mastery_points = db.Column(db.Integer, default=0)
    
    # Job Skills
    skills_unlocked = db.Column(JSONB, nullable=False, default=[])
    skill_points = db.Column(db.Integer, default=0)
    recipes_unlocked = db.Column(JSONB, nullable=False, default=[])
    
    # Job Stats
    items_crafted = db.Column(db.Integer, default=0)
    quality_crafts = db.Column(db.Integer, default=0)
    failed_crafts = db.Column(db.Integer, default=0)
    
    # Job Achievements
    achievements = db.Column(JSONB, nullable=False, default=[])
    titles = db.Column(JSONB, nullable=False, default=[])
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used = db.Column(db.DateTime, default=datetime.utcnow)

    def gain_experience(self, amount: int) -> Dict:
        """Grant experience points to job"""
        self.experience += amount
        
        level_ups = 0
        while self._check_level_up():
            self._level_up()
            level_ups += 1
            
        return {
            'gained_exp': amount,
            'level_ups': level_ups,
            'current_level': self.level,
            'skill_points_gained': level_ups,
            'mastery_points_gained': level_ups
        }

    def _check_level_up(self) -> bool:
        """Check if job has enough exp to level up"""
        required_exp = self._get_required_exp()
        return self.experience >= required_exp

    def _get_required_exp(self) -> int:
        """Calculate required exp for next level"""
        return int(800 * (1.2 ** (self.level - 1)))

    def _level_up(self):
        """Process job level up"""
        self.level += 1
        self.skill_points += 1
        self.mastery_points += 1

    def unlock_recipe(self, recipe_id: str) -> Dict:
        """Unlock a new recipe"""
        if recipe_id in self.recipes_unlocked:
            return {
                'success': False,
                'message': 'Recipe already unlocked'
            }
            
        if self.skill_points <= 0:
            return {
                'success': False,
                'message': 'No skill points available'
            }
            
        self.recipes_unlocked.append(recipe_id)
        self.skill_points -= 1
        
        return {
            'success': True,
            'message': 'Recipe unlocked successfully',
            'remaining_points': self.skill_points
        }

    def record_craft(self, quality: int) -> None:
        """Record crafting attempt"""
        self.items_crafted += 1
        
        if quality >= 80:  # Example threshold for quality crafts
            self.quality_crafts += 1
        elif quality < 20:  # Example threshold for failed crafts
            self.failed_crafts += 1

    def to_dict(self) -> Dict:
        """Convert job progress data to dictionary"""
        return {
            'id': self.id,
            'player_id': self.player_id,
            'job_type': self.job_type.value,
            'progress': {
                'level': self.level,
                'experience': self.experience,
                'mastery_points': self.mastery_points
            },
            'skills': {
                'unlocked': self.skills_unlocked,
                'points': self.skill_points,
                'recipes': self.recipes_unlocked
            },
            'stats': {
                'items_crafted': self.items_crafted,
                'quality_crafts': self.quality_crafts,
                'failed_crafts': self.failed_crafts,
                'success_rate': (self.items_crafted - self.failed_crafts) / max(1, self.items_crafted)
            },
            'achievements': self.achievements,
            'titles': self.titles
        }
