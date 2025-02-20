"""
Tests for the AI systems.
"""

import pytest
from typing import Dict, Any
from datetime import datetime
import numpy as np
from sklearn.ensemble import RandomForestClassifier

def test_ai_model_creation(db_session):
    """Test AI model creation."""
    from models import AIModel
    
    model = AIModel(
        name="Test Model",
        description="A test AI model",
        model_type="quest",
        version="1.0.0",
        parameters={
            'n_estimators': 100,
            'max_depth': 10,
            'min_samples_split': 2
        },
        features=[
            'level', 'job_class', 'hunter_class',
            'total_gates_cleared', 'achievement_points'
        ],
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db_session.add(model)
    db_session.commit()
    
    assert model.id is not None
    assert model.name == "Test Model"
    assert model.version == "1.0.0"

def test_ai_training_data(db_session):
    """Test AI training data management."""
    from models import AIModel, AITrainingData
    
    # Create model
    model = AIModel(
        name="Training Test Model",
        model_type="quest",
        version="1.0.0"
    )
    db_session.add(model)
    db_session.commit()
    
    # Add training data
    training_data = AITrainingData(
        model_id=model.id,
        data_type="quest_generation",
        features={
            'level': 10,
            'job_class': 'WARRIOR',
            'hunter_class': 'FIGHTER'
        },
        labels={
            'difficulty': 2,
            'reward_scale': 1.5
        },
        created_at=datetime.utcnow()
    )
    
    db_session.add(training_data)
    db_session.commit()
    
    assert training_data.id is not None
    assert training_data.model_id == model.id

def test_ai_evaluation(db_session):
    """Test AI model evaluation."""
    from models import AIModel, AIEvaluation, AIMetric
    
    # Create model
    model = AIModel(
        name="Evaluation Test Model",
        model_type="quest",
        version="1.0.0"
    )
    db_session.add(model)
    db_session.commit()
    
    # Add evaluation
    evaluation = AIEvaluation(
        model_id=model.id,
        metric=AIMetric.ACCURACY,
        value=0.85,
        details={
            'precision': 0.83,
            'recall': 0.87,
            'f1_score': 0.85
        },
        evaluated_at=datetime.utcnow()
    )
    
    db_session.add(evaluation)
    db_session.commit()
    
    assert evaluation.id is not None
    assert evaluation.value == 0.85

def test_player_activity_tracking(test_user: Dict[str, Any], db_session):
    """Test player activity tracking."""
    from models import PlayerActivity, ActivityType
    
    # Record activity
    activity = PlayerActivity(
        user_id=test_user['id'],
        type=ActivityType.GATE_HUNTING,
        details={
            'gate_id': 1,
            'time_spent': 3600,
            'outcome': 'success'
        },
        created_at=datetime.utcnow()
    )
    
    db_session.add(activity)
    db_session.commit()
    
    assert activity.id is not None
    assert activity.type == ActivityType.GATE_HUNTING

def test_quest_generation(test_user: Dict[str, Any], test_character: Dict[str, Any], db_session):
    """Test AI-driven quest generation."""
    from models import AIModel, Quest, QuestType
    
    # Create and train model
    model = AIModel(
        name="Quest Generator",
        model_type="quest",
        version="1.0.0",
        parameters={'n_estimators': 10}  # Small model for testing
    )
    db_session.add(model)
    db_session.commit()
    
    # Create classifier
    clf = RandomForestClassifier(**model.parameters)
    X = np.random.rand(100, 5)  # Random features
    y = np.random.randint(0, 3, 100)  # Random labels
    clf.fit(X, y)
    
    # Generate quest
    quest_params = model.generate_quest_parameters(
        user=test_user,
        quest_type=QuestType.DAILY,
        level_requirement=1
    )
    
    assert isinstance(quest_params, dict)
    assert 'objectives' in quest_params
    assert 'time_limit' in quest_params
    assert 'rewards' in quest_params

def test_achievement_evaluation(test_user: Dict[str, Any], db_session):
    """Test AI-driven achievement evaluation."""
    from models import AIModel, Achievement, AchievementType
    
    # Create and train model
    model = AIModel(
        name="Achievement Evaluator",
        model_type="achievement",
        version="1.0.0",
        parameters={'n_estimators': 10}  # Small model for testing
    )
    db_session.add(model)
    db_session.commit()
    
    # Create achievement
    achievement = Achievement(
        name="Test Achievement",
        type=AchievementType.COMBAT,
        requirements={'gates_completed': 10}
    )
    db_session.add(achievement)
    db_session.commit()
    
    # Evaluate achievement
    completion_prob = model.evaluate_achievement_completion(
        user=test_user,
        achievement=achievement,
        requirements=achievement.requirements
    )
    
    assert isinstance(completion_prob, float)
    assert 0 <= completion_prob <= 1

def test_combat_prediction(test_character: Dict[str, Any], test_gate: Dict[str, Any], db_session):
    """Test AI-driven combat prediction."""
    from models import AIModel
    
    # Create and train model
    model = AIModel(
        name="Combat Predictor",
        model_type="combat",
        version="1.0.0",
        parameters={'n_estimators': 10}  # Small model for testing
    )
    db_session.add(model)
    db_session.commit()
    
    # Extract features
    features = model._extract_user_features(test_character)
    
    # Make prediction
    clf = RandomForestClassifier(**model.parameters)
    X = np.random.rand(100, len(features))  # Random features
    y = np.random.randint(0, 2, 100)  # Random labels (win/lose)
    clf.fit(X, y)
    
    # Predict outcome
    prediction = clf.predict_proba([list(features.values())])[0]
    
    assert len(prediction) == 2  # Binary outcome
    assert np.sum(prediction) == pytest.approx(1.0)  # Probabilities sum to 1

def test_activity_preference_calculation(test_user: Dict[str, Any], db_session):
    """Test activity preference calculation."""
    from models import PlayerActivity, ActivityType
    
    # Create activities
    activities = [
        (ActivityType.GATE_HUNTING, 5),
        (ActivityType.GAMBLING, 3),
        (ActivityType.TRADING, 2)
    ]
    
    for activity_type, count in activities:
        for _ in range(count):
            activity = PlayerActivity(
                user_id=test_user['id'],
                type=activity_type,
                created_at=datetime.utcnow()
            )
            db_session.add(activity)
    
    db_session.commit()
    
    # Get recent activities
    recent = PlayerActivity.get_recent_activities(test_user['id'])
    
    # Calculate preferences
    total = sum(count for _, count in activities)
    expected_prefs = {
        ActivityType.GATE_HUNTING: 5/total,
        ActivityType.GAMBLING: 3/total,
        ActivityType.TRADING: 2/total
    }
    
    for activity_type, expected_pref in expected_prefs.items():
        actual_count = sum(1 for a in recent if a.type == activity_type)
        actual_pref = actual_count / total
        assert actual_pref == pytest.approx(expected_pref)

def test_model_versioning(db_session):
    """Test AI model versioning."""
    from models import AIModel
    
    # Create multiple versions
    versions = ['1.0.0', '1.1.0', '2.0.0']
    for version in versions:
        model = AIModel(
            name="Versioned Model",
            model_type="quest",
            version=version,
            is_active=version == '2.0.0'  # Latest version is active
        )
        db_session.add(model)
    
    db_session.commit()
    
    # Get latest active model
    latest = AIModel.get_quest_model()
    assert latest.version == '2.0.0'
