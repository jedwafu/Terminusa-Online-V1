from database import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, JSON
import enum

class AchievementType(enum.Enum):
    COMBAT = "Combat"
    EXPLORATION = "Exploration"
    SOCIAL = "Social"
    COLLECTION = "Collection"
    PROGRESSION = "Progression"
    SPECIAL = "Special"
    EVENT = "Event"

class QuestType(enum.Enum):
    MAIN = "Main"
    SIDE = "Side"
    DAILY = "Daily"
    WEEKLY = "Weekly"
    GUILD = "Guild"
    EVENT = "Event"
    JOB = "Job"
    CLASS = "Class"

class QuestStatus(enum.Enum):
    AVAILABLE = "Available"
    ACCEPTED = "Accepted"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"
    FAILED = "Failed"
    EXPIRED = "Expired"

class MilestoneType(enum.Enum):
    LEVEL = "Level"
    GATE = "Gate"
    QUEST = "Quest"
    ACHIEVEMENT = "Achievement"
    COLLECTION = "Collection"
    SOCIAL = "Social"

class Achievement(db.Model):
    __tablename__ = 'achievements'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    type = Column(Enum(AchievementType), nullable=False)
    icon = Column(String(100))
    points = Column(Integer, default=0)
    is_hidden = Column(Boolean, default=False)
    requirements = Column(JSON)  # JSON object defining completion requirements
    rewards = Column(JSON)  # JSON object defining rewards (stats, items, currency)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_achievements = relationship('UserAchievement', back_populates='achievement')

    def __repr__(self):
        return f'<Achievement {self.name} ({self.type.value})>'

    def check_completion(self, user):
        """Check if user meets achievement requirements"""
        user_achievement = UserAchievement.query.filter_by(
            user_id=user.id,
            achievement_id=self.id
        ).first()

        if user_achievement and user_achievement.completed:
            return False

        # Get AI agent's evaluation of user's progress
        from .ai import AIModel
        ai_model = AIModel.get_achievement_model()
        completion_chance = ai_model.evaluate_achievement_completion(
            user=user,
            achievement=self,
            requirements=self.requirements
        )

        if completion_chance > 0.95:  # 95% confidence threshold
            if not user_achievement:
                user_achievement = UserAchievement(
                    user_id=user.id,
                    achievement_id=self.id
                )
            user_achievement.completed = True
            user_achievement.completed_at = datetime.utcnow()
            db.session.add(user_achievement)
            db.session.commit()
            return True

        return False

class UserAchievement(db.Model):
    __tablename__ = 'user_achievements'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    achievement_id = Column(Integer, ForeignKey('achievements.id'), nullable=False)
    progress = Column(JSON)  # JSON object tracking progress
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='achievements')
    achievement = relationship('Achievement', back_populates='user_achievements')

    def __repr__(self):
        return f'<UserAchievement {self.user.username} - {self.achievement.name}>'

class Quest(db.Model):
    __tablename__ = 'quests'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    type = Column(Enum(QuestType), nullable=False)
    level_requirement = Column(Integer, default=1)
    prerequisites = Column(JSON)  # JSON array of required quest IDs
    objectives = Column(JSON)  # JSON object defining quest objectives
    time_limit = Column(Integer)  # Time limit in seconds, null for no limit
    is_repeatable = Column(Boolean, default=False)
    cooldown = Column(Integer)  # Cooldown in seconds for repeatable quests
    guild_id = Column(Integer, ForeignKey('guilds.id'))  # For guild quests
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    guild = relationship('Guild', back_populates='quests')
    user_quests = relationship('QuestProgress', back_populates='quest')
    rewards = relationship('QuestReward', back_populates='quest')

    def __repr__(self):
        return f'<Quest {self.name} ({self.type.value})>'

    def generate_for_user(self, user):
        """Generate quest instance for user using AI agent"""
        from .ai import AIModel
        ai_model = AIModel.get_quest_model()
        
        # Get quest parameters based on user's profile
        quest_params = ai_model.generate_quest_parameters(
            user=user,
            quest_type=self.type,
            level_requirement=self.level_requirement
        )
        
        # Create quest progress instance
        progress = QuestProgress(
            user_id=user.id,
            quest_id=self.id,
            status=QuestStatus.AVAILABLE,
            objectives=quest_params['objectives'],
            time_limit=quest_params['time_limit']
        )
        
        # Create quest rewards
        for reward_data in quest_params['rewards']:
            reward = QuestReward(
                quest_id=self.id,
                reward_type=reward_data['type'],
                reward_value=reward_data['value']
            )
            progress.rewards.append(reward)
        
        db.session.add(progress)
        db.session.commit()
        return progress

class QuestProgress(db.Model):
    __tablename__ = 'quest_progress'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    quest_id = Column(Integer, ForeignKey('quests.id'), nullable=False)
    status = Column(Enum(QuestStatus), default=QuestStatus.AVAILABLE)
    progress = Column(JSON)  # JSON object tracking objective progress
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='quests')
    quest = relationship('Quest', back_populates='user_quests')
    rewards = relationship('QuestReward', back_populates='progress')

    def __repr__(self):
        return f'<QuestProgress {self.user.username} - {self.quest.name} ({self.status.value})>'

class QuestReward(db.Model):
    __tablename__ = 'quest_rewards'

    id = Column(Integer, primary_key=True)
    quest_id = Column(Integer, ForeignKey('quests.id'), nullable=False)
    progress_id = Column(Integer, ForeignKey('quest_progress.id'))
    reward_type = Column(String(50), nullable=False)  # currency, item, exp, etc.
    reward_value = Column(JSON)  # JSON object with reward details
    claimed = Column(Boolean, default=False)
    claimed_at = Column(DateTime)

    # Relationships
    quest = relationship('Quest', back_populates='rewards')
    progress = relationship('QuestProgress', back_populates='rewards')

    def __repr__(self):
        return f'<QuestReward {self.reward_type} for {self.quest.name}>'

class Milestone(db.Model):
    __tablename__ = 'milestones'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    type = Column(Enum(MilestoneType), nullable=False)
    threshold = Column(Integer, nullable=False)  # Value required to reach milestone
    rewards = Column(JSON)  # JSON object defining rewards
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user_milestones = relationship('UserMilestone', back_populates='milestone')

    def __repr__(self):
        return f'<Milestone {self.name} ({self.type.value})>'

class UserMilestone(db.Model):
    __tablename__ = 'user_milestones'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    milestone_id = Column(Integer, ForeignKey('milestones.id'), nullable=False)
    current_value = Column(Integer, default=0)
    completed = Column(Boolean, default=False)
    completed_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='milestones')
    milestone = relationship('Milestone', back_populates='user_milestones')

    def __repr__(self):
        return f'<UserMilestone {self.user.username} - {self.milestone.name}>'

# Initialize default achievements and milestones
def init_progression():
    """Initialize default achievements and milestones"""
    # Add default achievements
    achievements = [
        {
            'name': 'First Steps',
            'description': 'Complete your first gate',
            'type': AchievementType.PROGRESSION,
            'points': 10,
            'requirements': {'gates_completed': 1}
        },
        {
            'name': 'Social Butterfly',
            'description': 'Join a guild',
            'type': AchievementType.SOCIAL,
            'points': 20,
            'requirements': {'guild_joined': True}
        }
        # Add more achievements...
    ]
    
    # Add default milestones
    milestones = [
        {
            'name': 'Level 50',
            'description': 'Reach level 50',
            'type': MilestoneType.LEVEL,
            'threshold': 50,
            'rewards': {
                'crystals': 1000,
                'stats': {'strength': 5, 'agility': 5}
            }
        },
        {
            'name': 'Gate Master',
            'description': 'Clear 100 gates',
            'type': MilestoneType.GATE,
            'threshold': 100,
            'rewards': {
                'exons': 5000,
                'title': 'Gate Master'
            }
        }
        # Add more milestones...
    ]
    
    # Add to database
    for achievement_data in achievements:
        achievement = Achievement.query.filter_by(name=achievement_data['name']).first()
        if not achievement:
            achievement = Achievement(**achievement_data)
            db.session.add(achievement)
    
    for milestone_data in milestones:
        milestone = Milestone.query.filter_by(name=milestone_data['name']).first()
        if not milestone:
            milestone = Milestone(**milestone_data)
            db.session.add(milestone)
    
    db.session.commit()
