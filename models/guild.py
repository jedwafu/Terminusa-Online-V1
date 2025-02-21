"""
Guild models for Terminusa Online
"""
from typing import Dict, List, Optional
from datetime import datetime
from enum import Enum
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class GuildRank(Enum):
    LEADER = "leader"
    OFFICER = "officer"
    VETERAN = "veteran"
    MEMBER = "member"
    RECRUIT = "recruit"

class QuestDifficulty(Enum):
    EASY = "easy"
    NORMAL = "normal"
    HARD = "hard"
    EXTREME = "extreme"

class QuestStatus(Enum):
    ACTIVE = "active"
    COMPLETED = "completed"
    FAILED = "failed"
    EXPIRED = "expired"

class Guild(db.Model):
    __tablename__ = 'guilds'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(500))
    leader_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    
    # Guild Status
    level = db.Column(db.Integer, default=1)
    experience = db.Column(db.BigInteger, default=0)
    reputation = db.Column(db.Integer, default=0)
    
    # Guild Treasury
    crystal_balance = db.Column(db.BigInteger, default=0)
    exon_balance = db.Column(db.Numeric(precision=18, scale=9), default=0)
    crystal_tax_rate = db.Column(db.Integer, default=10)  # Percentage
    exon_tax_rate = db.Column(db.Integer, default=10)     # Percentage
    
    # Guild Limits
    max_members = db.Column(db.Integer, default=50)
    max_quests = db.Column(db.Integer, default=3)
    
    # Guild Stats
    total_members = db.Column(db.Integer, default=1)
    active_members = db.Column(db.Integer, default=1)
    total_gates_cleared = db.Column(db.Integer, default=0)
    total_quests_completed = db.Column(db.Integer, default=0)
    
    # Guild Settings
    recruitment_status = db.Column(db.String(20), default='open')
    min_level_requirement = db.Column(db.Integer, default=1)
    settings = db.Column(JSONB, nullable=False, default={
        'quest_difficulty': 'normal',
        'auto_accept_members': False,
        'share_exp': True,
        'share_loot': True
    })
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def gain_experience(self, amount: int) -> Dict:
        """Grant experience points to guild"""
        self.experience += amount
        
        level_ups = 0
        while self._check_level_up():
            self._level_up()
            level_ups += 1
            
        return {
            'gained_exp': amount,
            'level_ups': level_ups,
            'current_level': self.level,
            'unlocked_features': self._get_level_unlocks(level_ups)
        }

    def _check_level_up(self) -> bool:
        """Check if guild has enough exp to level up"""
        required_exp = self._get_required_exp()
        return self.experience >= required_exp

    def _get_required_exp(self) -> int:
        """Calculate required exp for next level"""
        return int(10000 * (1.5 ** (self.level - 1)))

    def _level_up(self):
        """Process guild level up"""
        self.level += 1
        
        # Update guild limits based on level
        self.max_members = min(200, 50 + (self.level * 5))
        self.max_quests = min(10, 3 + (self.level // 5))

    def _get_level_unlocks(self, levels: int) -> List[str]:
        """Get features unlocked by level ups"""
        unlocks = []
        start_level = self.level - levels
        
        for level in range(start_level + 1, self.level + 1):
            if level == 5:
                unlocks.append('Guild Bank Access')
            elif level == 10:
                unlocks.append('Guild Quest System')
            elif level == 15:
                unlocks.append('Guild Territory Access')
            elif level == 20:
                unlocks.append('Guild Raid Access')
            elif level == 25:
                unlocks.append('Guild Shop Access')
            elif level % 5 == 0:
                unlocks.append(f'Member Slot Increase (+5)')
                
        return unlocks

    def add_member(self, user_id: int, rank: GuildRank = GuildRank.RECRUIT) -> Dict:
        """Add a new member to the guild"""
        if self.total_members >= self.max_members:
            return {
                'success': False,
                'message': 'Guild is at maximum capacity'
            }
            
        member = GuildMember(
            user_id=user_id,
            guild_id=self.id,
            rank=rank
        )
        db.session.add(member)
        
        self.total_members += 1
        self.active_members += 1
        
        return {
            'success': True,
            'message': 'Member added successfully'
        }

    def remove_member(self, user_id: int) -> Dict:
        """Remove a member from the guild"""
        member = GuildMember.query.filter_by(
            guild_id=self.id,
            user_id=user_id
        ).first()
        
        if not member:
            return {
                'success': False,
                'message': 'Member not found'
            }
            
        if member.rank == GuildRank.LEADER:
            return {
                'success': False,
                'message': 'Cannot remove guild leader'
            }
            
        db.session.delete(member)
        self.total_members -= 1
        self.active_members -= 1
        
        return {
            'success': True,
            'message': 'Member removed successfully'
        }

    def update_member_rank(self, user_id: int, new_rank: GuildRank) -> Dict:
        """Update a member's rank"""
        member = GuildMember.query.filter_by(
            guild_id=self.id,
            user_id=user_id
        ).first()
        
        if not member:
            return {
                'success': False,
                'message': 'Member not found'
            }
            
        old_rank = member.rank
        member.rank = new_rank
        
        return {
            'success': True,
            'message': f'Rank updated from {old_rank.value} to {new_rank.value}'
        }

    def process_tax(self, amount: int, currency: str) -> int:
        """Process guild tax on currency transaction"""
        if currency == 'crystals':
            tax_amount = int(amount * (self.crystal_tax_rate / 100))
            self.crystal_balance += tax_amount
        elif currency == 'exons':
            tax_amount = int(amount * (self.exon_tax_rate / 100))
            self.exon_balance += tax_amount
        else:
            tax_amount = 0
            
        return tax_amount

    def to_dict(self) -> Dict:
        """Convert guild data to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'leader_id': self.leader_id,
            'status': {
                'level': self.level,
                'experience': self.experience,
                'reputation': self.reputation
            },
            'treasury': {
                'crystal_balance': self.crystal_balance,
                'exon_balance': str(self.exon_balance),
                'tax_rates': {
                    'crystal': self.crystal_tax_rate,
                    'exon': self.exon_tax_rate
                }
            },
            'limits': {
                'max_members': self.max_members,
                'max_quests': self.max_quests
            },
            'stats': {
                'total_members': self.total_members,
                'active_members': self.active_members,
                'gates_cleared': self.total_gates_cleared,
                'quests_completed': self.total_quests_completed
            },
            'settings': {
                'recruitment_status': self.recruitment_status,
                'min_level': self.min_level_requirement,
                **self.settings
            }
        }

class GuildMember(db.Model):
    __tablename__ = 'guild_members'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    
    # Member Status
    rank = db.Column(db.Enum(GuildRank), nullable=False, default=GuildRank.RECRUIT)
    contribution_points = db.Column(db.Integer, default=0)
    weekly_contribution = db.Column(db.Integer, default=0)
    
    # Member Activity
    quests_completed = db.Column(db.Integer, default=0)
    gates_cleared = db.Column(db.Integer, default=0)
    last_active = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Timestamps
    joined_at = db.Column(db.DateTime, default=datetime.utcnow)
    rank_updated_at = db.Column(db.DateTime, default=datetime.utcnow)

    def contribute(self, amount: int) -> Dict:
        """Record member contribution"""
        self.contribution_points += amount
        self.weekly_contribution += amount
        
        return {
            'total_contribution': self.contribution_points,
            'weekly_contribution': self.weekly_contribution,
            'amount_added': amount
        }

    def reset_weekly_contribution(self):
        """Reset weekly contribution counter"""
        self.weekly_contribution = 0

    def update_activity(self):
        """Update member's last active timestamp"""
        self.last_active = datetime.utcnow()

    def to_dict(self) -> Dict:
        """Convert member data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'guild_id': self.guild_id,
            'rank': self.rank.value,
            'contributions': {
                'total': self.contribution_points,
                'weekly': self.weekly_contribution
            },
            'activity': {
                'quests_completed': self.quests_completed,
                'gates_cleared': self.gates_cleared,
                'last_active': self.last_active.isoformat()
            },
            'joined_at': self.joined_at.isoformat(),
            'rank_updated_at': self.rank_updated_at.isoformat()
        }

class GuildQuest(db.Model):
    __tablename__ = 'guild_quests'

    id = db.Column(db.Integer, primary_key=True)
    guild_id = db.Column(db.Integer, db.ForeignKey('guilds.id'), nullable=False)
    
    # Quest Info
    title = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(500), nullable=False)
    difficulty = db.Column(db.Enum(QuestDifficulty), nullable=False)
    
    # Quest Progress
    status = db.Column(db.Enum(QuestStatus), nullable=False, default=QuestStatus.ACTIVE)
    progress = db.Column(db.Integer, default=0)
    target = db.Column(db.Integer, nullable=False)
    
    # Quest Rewards
    rewards = db.Column(JSONB, nullable=False, default={})
    bonus_conditions = db.Column(JSONB, nullable=False, default=[])
    
    # Quest Participation
    participants = db.Column(JSONB, nullable=False, default={})
    completed_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)

    def update_progress(self, user_id: int, amount: int = 1) -> Dict:
        """Update quest progress"""
        if self.status != QuestStatus.ACTIVE:
            return {
                'success': False,
                'message': f'Quest is {self.status.value}'
            }
            
        if str(user_id) not in self.participants:
            self.participants[str(user_id)] = 0
            
        self.participants[str(user_id)] += amount
        self.progress = sum(self.participants.values())
        
        if self.progress >= self.target:
            return self.complete_quest(user_id)
            
        return {
            'success': True,
            'message': 'Progress updated',
            'current_progress': self.progress,
            'target': self.target
        }

    def complete_quest(self, completed_by: int) -> Dict:
        """Complete the quest"""
        self.status = QuestStatus.COMPLETED
        self.completed_by = completed_by
        self.completed_at = datetime.utcnow()
        
        return {
            'success': True,
            'message': 'Quest completed',
            'rewards': self.rewards,
            'bonus_rewards': self._check_bonus_conditions()
        }

    def _check_bonus_conditions(self) -> Dict:
        """Check and return achieved bonus conditions"""
        achieved_bonuses = {}
        
        for condition in self.bonus_conditions:
            if self._check_condition(condition):
                achieved_bonuses[condition['name']] = condition['rewards']
                
        return achieved_bonuses

    def _check_condition(self, condition: Dict) -> bool:
        """Check if a bonus condition is met"""
        condition_type = condition['type']
        
        if condition_type == 'time':
            if self.completed_at:
                time_taken = (self.completed_at - self.started_at).total_seconds()
                return time_taken <= condition['requirement']
                
        elif condition_type == 'participants':
            return len(self.participants) >= condition['requirement']
            
        elif condition_type == 'no_deaths':
            return not any(p.get('deaths', 0) > 0 for p in self.participants.values())
            
        return False

    def to_dict(self) -> Dict:
        """Convert quest data to dictionary"""
        return {
            'id': self.id,
            'guild_id': self.guild_id,
            'info': {
                'title': self.title,
                'description': self.description,
                'difficulty': self.difficulty.value
            },
            'progress': {
                'status': self.status.value,
                'current': self.progress,
                'target': self.target,
                'percentage': (self.progress / self.target) * 100
            },
            'rewards': {
                'base': self.rewards,
                'bonus_conditions': self.bonus_conditions
            },
            'participation': {
                'participants': self.participants,
                'completed_by': self.completed_by
            },
            'timestamps': {
                'created': self.created_at.isoformat(),
                'started': self.started_at.isoformat(),
                'completed': self.completed_at.isoformat() if self.completed_at else None,
                'expires': self.expires_at.isoformat() if self.expires_at else None
            }
        }
