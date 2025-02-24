import pytest
import random

import config as config
from api import create_app
from database.models import *


@pytest.fixture
def app():
    app = create_app(config.TestingConfig)
    with app.app_context():
        db.create_all()
    yield app


@pytest.fixture
def client(app):
    client = app.test_client()
    return client


@pytest.fixture
def auth(client):
    user_ruslan = {
        'login': 'ruslan',
        'password': "123"
    }
    user_artem = {
        'login': 'artem',
        'password': "123"
    }
    user_user = {
        'login': 'user',
        'password': "123"
    }
    log1 = client.post('/api/auth/login', json=user_ruslan)
    token1 = log1.get_json()['token']
    log2 = client.post('/api/auth/login', json=user_artem)
    token2 = log2.get_json()['token']
    log3 = client.post('/api/auth/login', json=user_user)
    token3 = log3.get_json()['token']
    return [token1, token2, token3]


def test_game(client, auth):
    game = client.post('/api/game')
    users = auth.copy()
    auth_token = lambda token: {'Authorization': f'Bearer {token}'}
    game_id = game.get_json()['id']
    bets = []
    multipliers = [0.1, random.uniform(1.0, game.get_json()['multiplier']),
                   random.uniform(1.0, game.get_json()['multiplier'])]
    for i in users:
        bet = client.post(f'/api/bet/{game_id}', headers=auth_token(i), json={'amount': 10})
        bets.append(bet.get_json()['id'])
    for i in range(len(bets)):
        bet_back = client.patch(f'/api/bet/{bets[i]}', headers=auth_token(users[i]),
                                json={'multiplier': multipliers[i]})
    game_over = client.post(f'/api/game/{game_id}')
    assert game.status_code == 201


