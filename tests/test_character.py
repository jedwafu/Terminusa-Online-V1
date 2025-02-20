"""
Tests for the character system.
"""

import pytest
from typing import Dict, Any
from datetime import datetime

def test_character_creation(test_user: Dict[str, Any], db_session):
    """Test character creation."""
    from models import PlayerCharacter, HunterClass, BaseJob, HealthStatus
    
    character = PlayerCharacter(
        user_id=test_user['id'],
        name="Test Character",
        level=1,
        experience=0,
        hunter_class=HunterClass.NOVICE,
        base_job=BaseJob.NONE,
        health=100,
        max_health=100,
        mana=100,
        max_mana=100,
        strength=10,
        agility=10,
        intelligence=10,
        vitality=10,
        status=HealthStatus.HEALTHY,
        created_at=datetime.utcnow()
    )
    
    db_session.add(character)
    db_session.commit()
    
    assert character.id is not None
    assert character.name == "Test Character"
    assert character.level == 1

def test_skill_creation(db_session):
    """Test skill creation."""
    from models import Skill, HunterClass, BaseJob
    
    skill = Skill(
        name="Test Skill",
        description="A test skill",
        hunter_class=HunterClass.FIGHTER,
        base_job=BaseJob.WARRIOR,
        level_requirement=1,
        mana_cost=10,
        cooldown=30,
        damage=50,
        healing=0,
        created_at=datetime.utcnow()
    )
    
    db_session.add(skill)
    db_session.commit()
    
    assert skill.id is not None
    assert skill.name == "Test Skill"
    assert skill.hunter_class == HunterClass.FIGHTER

def test_player_skill_assignment(test_character: Dict[str, Any], db_session):
    """Test assigning skills to a character."""
    from models import Skill, PlayerSkill, HunterClass, BaseJob
    
    # Create skill
    skill = Skill(
        name="Test Skill",
        hunter_class=HunterClass.NOVICE,
        base_job=BaseJob.NONE,
        level_requirement=1
    )
    
    db_session.add(skill)
    db_session.commit()
    
    # Assign skill to character
    player_skill = PlayerSkill(
        character_id=test_character['id'],
        skill_id=skill.id,
        level=1,
        experience=0,
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db_session.add(player_skill)
    db_session.commit()
    
    assert player_skill.id is not None
    assert player_skill.character_id == test_character['id']
    assert player_skill.skill_id == skill.id

def test_job_history(test_character: Dict[str, Any], db_session):
    """Test job history tracking."""
    from models import JobHistory, BaseJob
    
    history = JobHistory(
        character_id=test_character['id'],
        job=BaseJob.WARRIOR,
        start_date=datetime.utcnow(),
        level_reached=1,
        created_at=datetime.utcnow()
    )
    
    db_session.add(history)
    db_session.commit()
    
    assert history.id is not None
    assert history.character_id == test_character['id']
    assert history.job == BaseJob.WARRIOR

def test_job_quest(test_character: Dict[str, Any], db_session):
    """Test job quest system."""
    from models import JobQuest, BaseJob
    
    quest = JobQuest(
        character_id=test_character['id'],
        job=BaseJob.WARRIOR,
        name="Test Job Quest",
        description="A test job quest",
        level_requirement=1,
        reward_experience=100,
        reward_items='{"items": ["test_item"]}',
        status='active',
        start_date=datetime.utcnow(),
        created_at=datetime.utcnow()
    )
    
    db_session.add(quest)
    db_session.commit()
    
    assert quest.id is not None
    assert quest.character_id == test_character['id']
    assert quest.status == 'active'

@pytest.mark.parametrize('health_status,expected_effects', [
    (HealthStatus.HEALTHY, {'damage_modifier': 1.0, 'healing_modifier': 1.0}),
    (HealthStatus.INJURED, {'damage_modifier': 0.8, 'healing_modifier': 1.2}),
    (HealthStatus.CRITICAL, {'damage_modifier': 0.5, 'healing_modifier': 1.5}),
    (HealthStatus.EXHAUSTED, {'damage_modifier': 0.7, 'healing_modifier': 0.7}),
    (HealthStatus.RECOVERING, {'damage_modifier': 0.9, 'healing_modifier': 1.1})
])
def test_health_status_effects(test_character: Dict[str, Any], health_status: HealthStatus, 
                             expected_effects: Dict[str, float], db_session):
    """Test health status effects."""
    from models import PlayerCharacter
    
    character = PlayerCharacter.query.get(test_character['id'])
    character.status = health_status
    db_session.commit()
    
    assert character.get_damage_modifier() == expected_effects['damage_modifier']
    assert character.get_healing_modifier() == expected_effects['healing_modifier']

def test_character_leveling(test_character: Dict[str, Any], db_session):
    """Test character leveling system."""
    from models import PlayerCharacter
    
    character = PlayerCharacter.query.get(test_character['id'])
    initial_stats = {
        'strength': character.strength,
        'agility': character.agility,
        'intelligence': character.intelligence,
        'vitality': character.vitality
    }
    
    # Add experience to level up
    character.experience += 1000
    db_session.commit()
    
    # Verify stats increased
    assert character.level > 1
    assert character.strength > initial_stats['strength']
    assert character.agility > initial_stats['agility']
    assert character.intelligence > initial_stats['intelligence']
    assert character.vitality > initial_stats['vitality']

def test_hunter_class_progression(test_character: Dict[str, Any], db_session):
    """Test hunter class progression."""
    from models import PlayerCharacter, HunterClass
    
    character = PlayerCharacter.query.get(test_character['id'])
    
    # Progress from NOVICE to FIGHTER
    character.level = 10
    character.hunter_class = HunterClass.FIGHTER
    db_session.commit()
    
    assert character.hunter_class == HunterClass.FIGHTER
    
    # Verify can't skip classes
    with pytest.raises(ValueError):
        character.hunter_class = HunterClass.SUMMONER
        db_session.commit()

def test_skill_requirements(test_character: Dict[str, Any], db_session):
    """Test skill level requirements."""
    from models import Skill, PlayerSkill, HunterClass, BaseJob
    
    # Create high-level skill
    skill = Skill(
        name="Advanced Skill",
        hunter_class=HunterClass.FIGHTER,
        base_job=BaseJob.WARRIOR,
        level_requirement=50
    )
    
    db_session.add(skill)
    db_session.commit()
    
    # Try to assign to low-level character
    with pytest.raises(ValueError):
        player_skill = PlayerSkill(
            character_id=test_character['id'],
            skill_id=skill.id,
            level=1
        )
        db_session.add(player_skill)
        db_session.commit()

def test_job_change_requirements(test_character: Dict[str, Any], db_session):
    """Test job change requirements."""
    from models import PlayerCharacter, BaseJob
    
    character = PlayerCharacter.query.get(test_character['id'])
    
    # Try to change to advanced job at low level
    with pytest.raises(ValueError):
        character.base_job = BaseJob.KNIGHT
        db_session.commit()

def test_character_stats_calculation(test_character: Dict[str, Any], db_session):
    """Test character stats calculation."""
    from models import PlayerCharacter
    
    character = PlayerCharacter.query.get(test_character['id'])
    
    # Base stats
    base_hp = character.max_health
    base_mana = character.max_mana
    
    # Increase vitality and intelligence
    character.vitality += 10
    character.intelligence += 10
    db_session.commit()
    
    # Verify stats increased
    assert character.max_health > base_hp
    assert character.max_mana > base_mana
