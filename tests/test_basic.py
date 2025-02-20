"""
Basic tests to verify test setup and core functionality.
"""

import pytest
from flask import Flask
from flask.testing import FlaskClient
from typing import Dict, Any

def test_app_creation(app: Flask):
    """Test Flask application creation."""
    assert app is not None
    assert app.config['TESTING'] is True
    assert app.config['SQLALCHEMY_DATABASE_URI'].endswith('terminusa_test')

def test_database_setup(db_session):
    """Test database setup."""
    from models import User
    
    # Check if we can create and query a user
    user = User(
        username='testuser2',
        email='test2@example.com',
        role='player'
    )
    user.set_password('testpass123')
    
    db_session.add(user)
    db_session.commit()
    
    queried_user = User.query.filter_by(username='testuser2').first()
    assert queried_user is not None
    assert queried_user.email == 'test2@example.com'

def test_test_user_fixture(test_user: Dict[str, Any]):
    """Test test_user fixture."""
    assert test_user['username'] == 'testuser'
    assert test_user['email'] == 'test@example.com'
    assert test_user['role'] == 'player'

def test_test_admin_fixture(test_admin: Dict[str, Any]):
    """Test test_admin fixture."""
    assert test_admin['username'] == 'adminbb'
    assert test_admin['email'] == 'admin@terminusa.online'
    assert test_admin['role'] == 'admin'

def test_auth_headers(auth_headers: Dict[str, str]):
    """Test auth_headers fixture."""
    assert 'Authorization' in auth_headers
    assert auth_headers['Authorization'].startswith('Bearer ')

def test_client_setup(client: FlaskClient):
    """Test Flask test client setup."""
    response = client.get('/')
    assert response.status_code in [200, 302]  # Either OK or redirect to login

def test_test_guild_fixture(test_guild: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test test_guild fixture."""
    from models import Guild, GuildMember
    
    guild = Guild.query.get(test_guild['id'])
    assert guild is not None
    assert guild.name == 'Test Guild'
    
    member = GuildMember.query.filter_by(
        guild_id=guild.id,
        user_id=test_user['id']
    ).first()
    assert member is not None
    assert member.rank.value == 'MASTER'

def test_test_party_fixture(test_party: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test test_party fixture."""
    from models import Party, PartyMember
    
    party = Party.query.get(test_party['id'])
    assert party is not None
    assert party.name == 'Test Party'
    assert party.leader_id == test_user['id']
    
    member = PartyMember.query.filter_by(
        party_id=party.id,
        user_id=test_user['id']
    ).first()
    assert member is not None
    assert member.role.value == 'LEADER'

def test_test_gate_fixture(test_gate: Dict[str, Any], db_session):
    """Test test_gate fixture."""
    from models import Gate
    
    gate = Gate.query.get(test_gate['id'])
    assert gate is not None
    assert gate.name == 'Test Gate'
    assert gate.grade.value == 'F'
    assert gate.level == 1

def test_test_character_fixture(test_character: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test test_character fixture."""
    from models import PlayerCharacter
    
    character = PlayerCharacter.query.get(test_character['id'])
    assert character is not None
    assert character.name == 'Test Character'
    assert character.user_id == test_user['id']
    assert character.level == 1

def test_test_currencies_fixture(test_currencies: Dict[str, Any], test_user: Dict[str, Any], db_session):
    """Test test_currencies fixture."""
    from models import Currency
    
    for currency_type, currency_data in test_currencies.items():
        currency = Currency.query.get(currency_data['id'])
        assert currency is not None
        assert currency.user_id == test_user['id']
        assert currency.amount == 1000.0

@pytest.mark.parametrize('url', [
    '/',
    '/auth/login',
    '/auth/register'
])
def test_public_urls(client: FlaskClient, url: str):
    """Test public URL access."""
    response = client.get(url)
    assert response.status_code in [200, 302]

@pytest.mark.parametrize('url', [
    '/profile',
    '/marketplace',
    '/play'
])
def test_protected_urls_redirect(client: FlaskClient, url: str):
    """Test protected URL redirects for unauthorized users."""
    response = client.get(url)
    assert response.status_code == 302
    assert '/auth/login' in response.location

@pytest.mark.parametrize('url', [
    '/profile',
    '/marketplace',
    '/play'
])
def test_protected_urls_access(client: FlaskClient, auth_headers: Dict[str, str], url: str):
    """Test protected URL access for authorized users."""
    response = client.get(url, headers=auth_headers)
    assert response.status_code == 200

def test_database_rollback(db_session):
    """Test database changes are rolled back between tests."""
    from models import User
    
    # This user should not persist between tests
    user = User(
        username='rollbackuser',
        email='rollback@example.com',
        role='player'
    )
    user.set_password('testpass123')
    
    db_session.add(user)
    db_session.commit()
    
    # In a new session, this user should not exist
    db_session.remove()
    assert User.query.filter_by(username='rollbackuser').first() is None
