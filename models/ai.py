from app import db
from datetime import datetime
from enum import Enum

class AIModelType(Enum):
    QUEST = "quest"
    GATE = "gate"
    GACHA = "gacha"
    GAMBLING = "gambling"
    COMBAT = "combat"
    REWARD = "reward"
    ACHIEVEMENT = "achievement"

class PlayerActivityType(Enum):
    GATE_HUNTING = "gate_hunting"
    GAMBLING = "gambling"
    TRADING = "trading"
    CRAFTING = "crafting"
    SOCIALIZING = "socializing"
    QUESTING = "questing"
    GRINDING = "grinding"

class AIModel(db.Model):
    """AI model configuration and state"""
    __tablename__ = 'ai_models'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    model_type = db.Column(db.Enum(AIModelType), nullable=False)
    description = db.Column(db.Text, nullable=False)
    version = db.Column(db.String(20), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Model Configuration
    parameters = db.Column(db.JSON, nullable=False)  # Model hyperparameters
    features = db.Column(db.JSON, nullable=False)  # Input features used
    weights = db.Column(db.JSON, nullable=False)  # Current model weights
    
    # Performance Metrics
    accuracy = db.Column(db.Float, nullable=True)
    fairness_score = db.Column(db.Float, nullable=True)
    last_evaluation = db.Column(db.DateTime, nullable=True)
    
    # Training Info
    training_iterations = db.Column(db.Integer, default=0)
    last_trained = db.Column(db.DateTime, nullable=True)
    training_data_version = db.Column(db.String(20), nullable=True)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<AIModel {self.name}>"

class PlayerProfile(db.Model):
    """AI player profiling model"""
    __tablename__ = 'player_profiles'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    
    # Activity Preferences (0-1 scale)
    activity_preferences = db.Column(db.JSON, nullable=False, default=dict)  # Mapped to PlayerActivityType
    
    # Behavioral Metrics
    risk_tolerance = db.Column(db.Float, default=0.5)  # 0-1 scale
    social_engagement = db.Column(db.Float, default=0.5)  # 0-1 scale
    progression_speed = db.Column(db.Float, default=0.5)  # 0-1 scale
    spending_behavior = db.Column(db.Float, default=0.5)  # 0-1 scale
    
    # Time Patterns
    active_hours = db.Column(db.JSON, nullable=False, default=list)  # List of typical active hours
    session_duration = db.Column(db.Float, default=0)  # Average session length in minutes
    weekly_playtime = db.Column(db.Float, default=0)  # Average weekly playtime in hours
    
    # Performance Metrics
    success_rate = db.Column(db.JSON, nullable=False, default=dict)  # Success rates by activity
    progression_rate = db.Column(db.JSON, nullable=False, default=dict)  # Progression speeds by aspect
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PlayerProfile {self.character_id}>"

class ActivityLog(db.Model):
    """Player activity log for AI training"""
    __tablename__ = 'activity_logs'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    activity_type = db.Column(db.Enum(PlayerActivityType), nullable=False)
    details = db.Column(db.JSON, nullable=False)
    success = db.Column(db.Boolean, nullable=True)
    duration = db.Column(db.Integer, nullable=True)  # in seconds
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<ActivityLog {self.activity_type}>"

class AIDecision(db.Model):
    """AI decision log for analysis and improvement"""
    __tablename__ = 'ai_decisions'

    id = db.Column(db.Integer, primary_key=True)
    model_id = db.Column(db.Integer, db.ForeignKey('ai_models.id'), nullable=False)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    decision_type = db.Column(db.String(50), nullable=False)
    input_data = db.Column(db.JSON, nullable=False)
    output_data = db.Column(db.JSON, nullable=False)
    confidence = db.Column(db.Float, nullable=False)
    success = db.Column(db.Boolean, nullable=True)
    feedback = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<AIDecision {self.decision_type}>"

class GachaSystem(db.Model):
    """Gacha system configuration and state"""
    __tablename__ = 'gacha_systems'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Base Rates
    rates = db.Column(db.JSON, nullable=False)  # Base rates for each grade
    pity_system = db.Column(db.JSON, nullable=False)  # Pity counter configuration
    
    # AI Configuration
    player_factor_weights = db.Column(db.JSON, nullable=False)  # How player factors affect rates
    activity_bonus_rates = db.Column(db.JSON, nullable=False)  # Activity-based rate boosts
    fairness_parameters = db.Column(db.JSON, nullable=False)  # Fairness ensuring parameters
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GachaSystem {self.name}>"

class GachaHistory(db.Model):
    """Player gacha pull history"""
    __tablename__ = 'gacha_history'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    gacha_id = db.Column(db.Integer, db.ForeignKey('gacha_systems.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=False)
    grade = db.Column(db.String(20), nullable=False)
    pity_count = db.Column(db.Integer, nullable=False)
    exon_cost = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<GachaHistory {self.id}>"

class GamblingSystem(db.Model):
    """Gambling system configuration and state"""
    __tablename__ = 'gambling_systems'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    
    # Game Configuration
    base_odds = db.Column(db.Float, nullable=False)  # Base winning probability
    min_bet = db.Column(db.Integer, nullable=False)
    max_bet = db.Column(db.Integer, nullable=False)
    
    # AI Configuration
    player_factor_weights = db.Column(db.JSON, nullable=False)  # How player factors affect odds
    activity_modifiers = db.Column(db.JSON, nullable=False)  # Activity-based modifications
    fairness_parameters = db.Column(db.JSON, nullable=False)  # Fairness ensuring parameters
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GamblingSystem {self.name}>"

class GamblingHistory(db.Model):
    """Player gambling history"""
    __tablename__ = 'gambling_history'

    id = db.Column(db.Integer, primary_key=True)
    character_id = db.Column(db.Integer, db.ForeignKey('player_characters.id'), nullable=False)
    system_id = db.Column(db.Integer, db.ForeignKey('gambling_systems.id'), nullable=False)
    bet_amount = db.Column(db.Integer, nullable=False)
    win = db.Column(db.Boolean, nullable=False)
    payout = db.Column(db.Integer, nullable=False)
    odds = db.Column(db.Float, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<GamblingHistory {self.id}>"
