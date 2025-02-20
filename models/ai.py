from database import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, JSON
import enum
import numpy as np
from sklearn.ensemble import RandomForestClassifier
import joblib

class AIMetric(enum.Enum):
    ACCURACY = "Accuracy"
    PRECISION = "Precision"
    RECALL = "Recall"
    F1_SCORE = "F1 Score"
    AUC_ROC = "AUC ROC"

class ActivityType(enum.Enum):
    GATE_HUNTING = "Gate Hunting"
    GAMBLING = "Gambling"
    TRADING = "Trading"
    CRAFTING = "Crafting"
    SOCIAL = "Social"
    QUESTING = "Questing"
    COMBAT = "Combat"

class AIModel(db.Model):
    __tablename__ = 'ai_models'

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    description = Column(String(500))
    model_type = Column(String(50), nullable=False)  # quest, achievement, combat, etc.
    version = Column(String(20), nullable=False)
    parameters = Column(JSON)  # Model hyperparameters
    features = Column(JSON)  # Feature definitions
    model_path = Column(String(200))  # Path to saved model file
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    training_data = relationship('AITrainingData', back_populates='model')
    evaluations = relationship('AIEvaluation', back_populates='model')

    def __repr__(self):
        return f'<AIModel {self.name} v{self.version}>'

    @classmethod
    def get_quest_model(cls):
        """Get the active quest generation model"""
        return cls.query.filter_by(
            model_type='quest',
            is_active=True
        ).order_by(cls.version.desc()).first()

    @classmethod
    def get_achievement_model(cls):
        """Get the active achievement evaluation model"""
        return cls.query.filter_by(
            model_type='achievement',
            is_active=True
        ).order_by(cls.version.desc()).first()

    @classmethod
    def get_combat_model(cls):
        """Get the active combat prediction model"""
        return cls.query.filter_by(
            model_type='combat',
            is_active=True
        ).order_by(cls.version.desc()).first()

    def load_model(self):
        """Load the trained model from file"""
        return joblib.load(self.model_path)

    def generate_quest_parameters(self, user, quest_type, level_requirement):
        """Generate quest parameters based on user profile"""
        # Load model
        model = self.load_model()

        # Get user features
        features = self._extract_user_features(user)

        # Generate quest parameters
        params = model.predict_quest_params(
            features=features,
            quest_type=quest_type,
            level_requirement=level_requirement
        )

        return params

    def evaluate_achievement_completion(self, user, achievement, requirements):
        """Evaluate if user meets achievement requirements"""
        # Load model
        model = self.load_model()

        # Get user features
        features = self._extract_user_features(user)

        # Add achievement-specific features
        features.update(self._extract_achievement_features(achievement, requirements))

        # Predict completion probability
        completion_prob = model.predict_proba([features])[0][1]

        return completion_prob

    def _extract_user_features(self, user):
        """Extract relevant features from user profile"""
        # Get user's recent activities
        activities = PlayerActivity.get_recent_activities(user.id)
        activity_counts = {
            activity_type: sum(1 for a in activities if a.type == activity_type)
            for activity_type in ActivityType
        }

        # Calculate activity preferences
        total_activities = sum(activity_counts.values()) or 1
        activity_preferences = {
            f"pref_{k.value.lower()}": v / total_activities
            for k, v in activity_counts.items()
        }

        return {
            'level': user.character.level,
            'job_class': user.character.job_class.value,
            'hunter_class': user.character.hunter_class.value,
            'total_gates_cleared': user.character.total_gates_cleared,
            'achievement_points': user.total_achievement_points,
            'guild_rank': user.guild_membership.rank.value if user.guild_membership else None,
            'party_role': user.party_memberships[-1].role.value if user.party_memberships else None,
            **activity_preferences
        }

    def _extract_achievement_features(self, achievement, requirements):
        """Extract relevant features from achievement"""
        return {
            'achievement_type': achievement.type.value,
            'points': achievement.points,
            'requirements': requirements
        }

class AITrainingData(db.Model):
    __tablename__ = 'ai_training_data'

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False)
    data_type = Column(String(50), nullable=False)
    features = Column(JSON, nullable=False)
    labels = Column(JSON, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    model = relationship('AIModel', back_populates='training_data')

    def __repr__(self):
        return f'<AITrainingData {self.data_type} for {self.model.name}>'

class AIEvaluation(db.Model):
    __tablename__ = 'ai_evaluations'

    id = Column(Integer, primary_key=True)
    model_id = Column(Integer, ForeignKey('ai_models.id'), nullable=False)
    metric = Column(Enum(AIMetric), nullable=False)
    value = Column(Float, nullable=False)
    details = Column(JSON)  # Additional evaluation details
    evaluated_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    model = relationship('AIModel', back_populates='evaluations')

    def __repr__(self):
        return f'<AIEvaluation {self.metric.value}: {self.value}>'

class PlayerActivity(db.Model):
    __tablename__ = 'player_activities'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Enum(ActivityType), nullable=False)
    details = Column(JSON)  # Activity-specific details
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    user = relationship('User', back_populates='activities')

    def __repr__(self):
        return f'<PlayerActivity {self.user.username} - {self.type.value}>'

    @classmethod
    def get_recent_activities(cls, user_id, limit=100):
        """Get user's recent activities"""
        return cls.query.filter_by(user_id=user_id)\
            .order_by(cls.created_at.desc())\
            .limit(limit)\
            .all()

# Initialize default AI models
def init_ai_models():
    """Initialize default AI models"""
    default_models = [
        {
            'name': 'Quest Generator',
            'description': 'Generates personalized quests based on user profile',
            'model_type': 'quest',
            'version': '1.0.0',
            'parameters': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2
            },
            'features': [
                'level', 'job_class', 'hunter_class',
                'total_gates_cleared', 'achievement_points',
                'guild_rank', 'party_role',
                'pref_gate_hunting', 'pref_gambling',
                'pref_trading', 'pref_crafting',
                'pref_social', 'pref_questing',
                'pref_combat'
            ]
        },
        {
            'name': 'Achievement Evaluator',
            'description': 'Evaluates achievement completion probability',
            'model_type': 'achievement',
            'version': '1.0.0',
            'parameters': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2
            },
            'features': [
                'level', 'job_class', 'hunter_class',
                'total_gates_cleared', 'achievement_points',
                'achievement_type', 'points', 'requirements'
            ]
        },
        {
            'name': 'Combat Predictor',
            'description': 'Predicts combat outcomes and generates rewards',
            'model_type': 'combat',
            'version': '1.0.0',
            'parameters': {
                'n_estimators': 100,
                'max_depth': 10,
                'min_samples_split': 2
            },
            'features': [
                'level', 'job_class', 'hunter_class',
                'total_gates_cleared', 'achievement_points',
                'equipment_stats', 'party_composition',
                'gate_grade', 'magic_beast_type'
            ]
        }
    ]

    # Initialize models
    for model_data in default_models:
        model = AIModel.query.filter_by(
            name=model_data['name'],
            version=model_data['version']
        ).first()

        if not model:
            # Create and train model
            clf = RandomForestClassifier(**model_data['parameters'])
            
            # Save model to file
            model_path = f"models/ai/{model_data['model_type']}_{model_data['version']}.joblib"
            joblib.dump(clf, model_path)
            
            # Create model record
            model_data['model_path'] = model_path
            model = AIModel(**model_data)
            db.session.add(model)

    db.session.commit()
