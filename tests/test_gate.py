"""
Tests for the gate system.
"""

import pytest
from typing import Dict, Any
from datetime import datetime

def test_gate_creation(db_session):
    """Test gate creation."""
    from models import Gate, GateGrade
    
    gate = Gate(
        name="Test Gate",
        description="A test gate",
        grade=GateGrade.F,
        level=1,
        difficulty=1.0,
        is_active=True,
        max_players=1,
        created_at=datetime.utcnow()
    )
    
    db_session.add(gate)
    db_session.commit()
    
    assert gate.id is not None
    assert gate.name == "Test Gate"
    assert gate.grade == GateGrade.F

def test_magic_beast_creation(test_gate: Dict[str, Any], db_session):
    """Test magic beast creation."""
    from models import MagicBeast, MagicBeastType, Gate
    
    beast = MagicBeast(
        name="Test Beast",
        description="A test magic beast",
        type=MagicBeastType.NORMAL,
        level=1,
        hp=100,
        attack=10,
        defense=10,
        speed=10,
        created_at=datetime.utcnow()
    )
    
    db_session.add(beast)
    db_session.commit()
    
    # Add beast to gate
    gate = Gate.query.get(test_gate['id'])
    gate.magic_beasts.append(beast)
    db_session.commit()
    
    assert beast.id is not None
    assert len(gate.magic_beasts) == 1
    assert gate.magic_beasts[0].name == "Test Beast"

def test_gate_session_creation(test_gate: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test gate session creation."""
    from models import GateSession
    
    session = GateSession(
        gate_id=test_gate['id'],
        player_id=test_user['id'],
        start_time=datetime.utcnow(),
        status='active',
        created_at=datetime.utcnow()
    )
    
    db_session.add(session)
    db_session.commit()
    
    assert session.id is not None
    assert session.status == 'active'
    assert session.gate_id == test_gate['id']
    assert session.player_id == test_user['id']

def test_ai_behavior_creation(db_session):
    """Test AI behavior creation."""
    from models import AIBehavior, MagicBeast, MagicBeastType
    
    # Create magic beast first
    beast = MagicBeast(
        name="AI Beast",
        type=MagicBeastType.BOSS,
        level=10,
        hp=1000,
        attack=100,
        defense=100,
        speed=100
    )
    
    db_session.add(beast)
    db_session.commit()
    
    # Create AI behavior
    behavior = AIBehavior(
        magic_beast_id=beast.id,
        trigger_condition="hp < 50%",
        action="use_special_attack",
        cooldown=60,
        priority=1,
        created_at=datetime.utcnow()
    )
    
    db_session.add(behavior)
    db_session.commit()
    
    assert behavior.id is not None
    assert behavior.magic_beast_id == beast.id
    assert len(beast.behaviors) == 1

@pytest.mark.parametrize('grade,expected_level', [
    (GateGrade.F, 1),
    (GateGrade.E, 10),
    (GateGrade.D, 20),
    (GateGrade.C, 30),
    (GateGrade.B, 40),
    (GateGrade.A, 50),
    (GateGrade.S, 60),
    (GateGrade.SS, 70),
    (GateGrade.SSS, 80)
])
def test_gate_grade_level_requirements(grade: GateGrade, expected_level: int, db_session):
    """Test gate grade level requirements."""
    from models import Gate
    
    gate = Gate(
        name=f"Test {grade.value} Gate",
        grade=grade,
        level=expected_level,
        difficulty=1.0
    )
    
    db_session.add(gate)
    db_session.commit()
    
    assert gate.level >= expected_level

def test_gate_completion(test_gate: Dict[str, Any], test_user: Dict[str, Any], test_currencies: Dict[str, Any], db_session):
    """Test gate completion and rewards."""
    from models import GateSession, Currency, Transaction, TransactionType
    
    # Create and complete gate session
    session = GateSession(
        gate_id=test_gate['id'],
        player_id=test_user['id'],
        start_time=datetime.utcnow(),
        status='completed',
        score=100,
        rewards='{"crystals": 100}'
    )
    
    db_session.add(session)
    db_session.commit()
    
    # Verify crystal rewards
    crystal_currency = Currency.query.get(test_currencies['CRYSTALS']['id'])
    initial_amount = crystal_currency.amount
    
    # Add reward transaction
    transaction = Transaction(
        currency_id=crystal_currency.id,
        user_id=test_user['id'],
        type=TransactionType.GATE,
        amount=100.0,
        description=f"Reward for completing gate {test_gate['id']}"
    )
    
    db_session.add(transaction)
    db_session.commit()
    
    assert crystal_currency.amount == initial_amount + 100.0

def test_party_gate_session(test_gate: Dict[str, Any], test_party: Dict[str, Any], db_session):
    """Test party gate session."""
    from models import GateSession
    
    # Create gate session for party
    session = GateSession(
        gate_id=test_gate['id'],
        player_id=test_party['leader_id'],
        start_time=datetime.utcnow(),
        status='active',
        party_id=test_party['id']
    )
    
    db_session.add(session)
    db_session.commit()
    
    assert session.id is not None
    assert session.party_id == test_party['id']

def test_gate_difficulty_scaling(db_session):
    """Test gate difficulty scaling."""
    from models import Gate, GateGrade
    
    difficulties = []
    for grade in GateGrade:
        gate = Gate(
            name=f"Test {grade.value} Gate",
            grade=grade,
            level=1,
            difficulty=1.0
        )
        
        db_session.add(gate)
        difficulties.append(gate.difficulty)
    
    db_session.commit()
    
    # Verify difficulties increase with grade
    assert all(difficulties[i] <= difficulties[i+1] for i in range(len(difficulties)-1))

def test_magic_beast_type_stats(db_session):
    """Test magic beast type stats scaling."""
    from models import MagicBeast, MagicBeastType
    
    stats = {}
    for beast_type in MagicBeastType:
        beast = MagicBeast(
            name=f"Test {beast_type.value} Beast",
            type=beast_type,
            level=1,
            hp=100,
            attack=10,
            defense=10,
            speed=10
        )
        
        db_session.add(beast)
        stats[beast_type] = (beast.hp, beast.attack, beast.defense, beast.speed)
    
    db_session.commit()
    
    # Verify boss and raid types have higher stats
    normal_stats = stats[MagicBeastType.NORMAL]
    boss_stats = stats[MagicBeastType.BOSS]
    raid_stats = stats[MagicBeastType.RAID]
    
    assert all(b > n for b, n in zip(boss_stats, normal_stats))
    assert all(r > n for r, n in zip(raid_stats, normal_stats))

def test_gate_session_status_transitions(test_gate: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test gate session status transitions."""
    from models import GateSession
    
    session = GateSession(
        gate_id=test_gate['id'],
        player_id=test_user['id'],
        start_time=datetime.utcnow(),
        status='active'
    )
    
    db_session.add(session)
    db_session.commit()
    
    # Test valid transitions
    valid_transitions = [
        ('active', 'completed'),
        ('active', 'failed'),
        ('failed', 'active'),  # Allow retry
    ]
    
    for from_status, to_status in valid_transitions:
        session.status = from_status
        db_session.commit()
        
        session.status = to_status
        db_session.commit()
        
        assert session.status == to_status
    
    # Test invalid transition
    with pytest.raises(ValueError):
        session.status = 'invalid_status'
        db_session.commit()
