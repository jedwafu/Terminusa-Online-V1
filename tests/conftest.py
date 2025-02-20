"""
Test configuration and fixtures.
"""

import os
import pytest
from flask import Flask
from flask.testing import FlaskClient
from typing import Generator, Dict, Any
from datetime import datetime, timedelta

from database import db
from models import init_db
from app_final import create_app

# Test database URL
TEST_DATABASE_URL = os.getenv(
    'TEST_DATABASE_URL',
    'postgresql://postgres:postgres@localhost:5432/terminusa_test'
)

@pytest.fixture(scope='session')
def app() -> Flask:
    """Create Flask application for testing."""
    app = create_app()
    app.config.update({
        'TESTING': True,
        'SQLALCHEMY_DATABASE_URI': TEST_DATABASE_URL,
        'SQLALCHEMY_TRACK_MODIFICATIONS': False,
        'WTF_CSRF_ENABLED': False,
        'SERVER_NAME': 'localhost.localdomain',
        'PREFERRED_URL_SCHEME': 'http',
    })
    
    return app

@pytest.fixture(scope='session')
def _db(app: Flask) -> Generator:
    """Create database for testing."""
    with app.app_context():
        db.create_all()
        init_db()  # Initialize with test data
        yield db
        db.session.remove()
        db.drop_all()

@pytest.fixture(scope='function')
def db_session(_db: db) -> Generator:
    """Create a new database session for a test."""
    connection = _db.engine.connect()
    transaction = connection.begin()
    
    session = _db.create_scoped_session(
        options={'bind': connection, 'binds': {}}
    )
    _db.session = session
    
    yield session
    
    transaction.rollback()
    connection.close()
    session.remove()

@pytest.fixture(scope='function')
def client(app: Flask) -> FlaskClient:
    """Create Flask test client."""
    return app.test_client()

@pytest.fixture(scope='function')
def auth_headers(app: Flask, test_user: Dict[str, Any]) -> Dict[str, str]:
    """Create authentication headers for test user."""
    with app.app_context():
        access_token = create_access_token(
            identity=test_user['username'],
            additional_claims={
                'role': test_user['role'],
                'email': test_user['email']
            },
            expires_delta=timedelta(days=1)
        )
        return {'Authorization': f'Bearer {access_token}'}

@pytest.fixture(scope='function')
def test_user(db_session) -> Dict[str, Any]:
    """Create test user."""
    from models import User
    
    user = User(
        username='testuser',
        email='test@example.com',
        role='player',
        is_email_verified=True,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    user.set_password('testpass123')
    
    db_session.add(user)
    db_session.commit()
    
    return {
        'id': user.id,
        'username': user.username,
        'email': user.email,
        'role': user.role
    }

@pytest.fixture(scope='function')
def test_admin(db_session) -> Dict[str, Any]:
    """Create test admin user."""
    from models import User
    
    admin = User(
        username='adminbb',
        email='admin@terminusa.online',
        role='admin',
        is_email_verified=True,
        created_at=datetime.utcnow(),
        last_login=datetime.utcnow()
    )
    admin.set_password('adminpass123')
    
    db_session.add(admin)
    db_session.commit()
    
    return {
        'id': admin.id,
        'username': admin.username,
        'email': admin.email,
        'role': admin.role
    }

@pytest.fixture(scope='function')
def test_guild(db_session, test_user) -> Dict[str, Any]:
    """Create test guild."""
    from models import Guild, GuildMember, GuildRank
    
    guild = Guild(
        name='Test Guild',
        description='A test guild',
        level=1,
        experience=0,
        creation_cost_exons=100000,
        creation_cost_crystals=50000,
        max_members=100,
        created_at=datetime.utcnow()
    )
    
    db_session.add(guild)
    db_session.commit()
    
    member = GuildMember(
        guild_id=guild.id,
        user_id=test_user['id'],
        rank=GuildRank.MASTER,
        contribution=0,
        joined_at=datetime.utcnow()
    )
    
    db_session.add(member)
    db_session.commit()
    
    return {
        'id': guild.id,
        'name': guild.name,
        'level': guild.level
    }

@pytest.fixture(scope='function')
def test_party(db_session, test_user) -> Dict[str, Any]:
    """Create test party."""
    from models import Party, PartyMember, PartyRole
    
    party = Party(
        name='Test Party',
        leader_id=test_user['id'],
        is_active=True,
        created_at=datetime.utcnow()
    )
    
    db_session.add(party)
    db_session.commit()
    
    member = PartyMember(
        party_id=party.id,
        user_id=test_user['id'],
        role=PartyRole.LEADER,
        joined_at=datetime.utcnow()
    )
    
    db_session.add(member)
    db_session.commit()
    
    return {
        'id': party.id,
        'name': party.name,
        'leader_id': party.leader_id
    }

@pytest.fixture(scope='function')
def test_gate(db_session) -> Dict[str, Any]:
    """Create test gate."""
    from models import Gate, GateGrade
    
    gate = Gate(
        name='Test Gate',
        description='A test gate',
        grade=GateGrade.F,
        level=1,
        difficulty=1.0,
        is_active=True,
        max_players=1,
        created_at=datetime.utcnow()
    )
    
    db_session.add(gate)
    db_session.commit()
    
    return {
        'id': gate.id,
        'name': gate.name,
        'grade': gate.grade.value
    }

@pytest.fixture(scope='function')
def test_character(db_session, test_user) -> Dict[str, Any]:
    """Create test character."""
    from models import PlayerCharacter, HunterClass, BaseJob, HealthStatus
    
    character = PlayerCharacter(
        user_id=test_user['id'],
        name='Test Character',
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
    
    return {
        'id': character.id,
        'name': character.name,
        'level': character.level
    }

@pytest.fixture(scope='function')
def test_currencies(db_session, test_user) -> Dict[str, Any]:
    """Create test currencies."""
    from models import Currency, CurrencyType
    
    currencies = {}
    for currency_type in CurrencyType:
        currency = Currency(
            user_id=test_user['id'],
            type=currency_type,
            amount=1000.0,
            created_at=datetime.utcnow()
        )
        db_session.add(currency)
        currencies[currency_type.value] = currency
    
    db_session.commit()
    
    return {
        name: {
            'id': currency.id,
            'amount': currency.amount
        }
        for name, currency in currencies.items()
    }
