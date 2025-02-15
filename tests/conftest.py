import pytest
import sys
import os
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import asyncio
import json
import jwt
from unittest.mock import Mock

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Mock data for testing
TEST_USERS = {
    1: {
        'id': 1,
        'username': 'test_user',
        'email': 'test@example.com',
        'level': 10,
        'experience': 1000,
        'created_at': datetime.utcnow()
    }
}

TEST_ITEMS = {
    1: {
        'id': 1,
        'name': 'Test Sword',
        'type': 'weapon',
        'rarity': 'common',
        'stats': {'damage': 10, 'speed': 5}
    }
}

TEST_GUILDS = {
    1: {
        'id': 1,
        'name': 'Test Guild',
        'leader_id': 1,
        'members': [1],
        'level': 5
    }
}

@pytest.fixture
def mock_db():
    """Mock database for testing"""
    class MockDB:
        def __init__(self):
            self.users = TEST_USERS.copy()
            self.items = TEST_ITEMS.copy()
            self.guilds = TEST_GUILDS.copy()
        
        async def get_user(self, user_id: int):
            return self.users.get(user_id)
        
        async def create_user(self, data: Dict):
            user_id = max(self.users.keys()) + 1
            user = {
                'id': user_id,
                'created_at': datetime.utcnow(),
                **data
            }
            self.users[user_id] = user
            return user
        
        async def update_user(self, user_id: int, data: Dict):
            if user_id in self.users:
                self.users[user_id].update(data)
                return self.users[user_id]
            return None
        
        async def get_item(self, item_id: int):
            return self.items.get(item_id)
        
        async def get_guild(self, guild_id: int):
            return self.guilds.get(guild_id)
    
    return MockDB()

@pytest.fixture
def mock_auth():
    """Mock authentication for testing"""
    class MockAuth:
        def __init__(self):
            self.secret = "test-secret-key"
            self.tokens = {}
        
        def create_token(self, user_id: int) -> str:
            token = jwt.encode(
                {
                    'user_id': user_id,
                    'exp': datetime.utcnow() + timedelta(days=1)
                },
                self.secret,
                algorithm='HS256'
            )
            self.tokens[token] = user_id
            return token
        
        def verify_token(self, token: str) -> Optional[int]:
            try:
                payload = jwt.decode(
                    token,
                    self.secret,
                    algorithms=['HS256']
                )
                return payload['user_id']
            except:
                return None
    
    return MockAuth()

@pytest.fixture
def mock_game_state():
    """Mock game state for testing"""
    class MockGameState:
        def __init__(self):
            self.online_players = set()
            self.player_positions = {}
            self.player_stats = {}
        
        def add_player(self, user_id: int):
            self.online_players.add(user_id)
            self.player_positions[user_id] = {'x': 0, 'y': 0}
            self.player_stats[user_id] = {
                'health': 100,
                'mana': 100,
                'level': 1
            }
        
        def remove_player(self, user_id: int):
            self.online_players.discard(user_id)
            self.player_positions.pop(user_id, None)
            self.player_stats.pop(user_id, None)
        
        def update_position(self, user_id: int, x: float, y: float):
            if user_id in self.online_players:
                self.player_positions[user_id] = {'x': x, 'y': y}
        
        def update_stats(self, user_id: int, stats: Dict):
            if user_id in self.online_players:
                self.player_stats[user_id].update(stats)
    
    return MockGameState()

@pytest.fixture
def mock_inventory():
    """Mock inventory system for testing"""
    class MockInventory:
        def __init__(self):
            self.inventories = {}
        
        def get_inventory(self, user_id: int) -> Dict:
            if user_id not in self.inventories:
                self.inventories[user_id] = {
                    'items': [],
                    'capacity': 20,
                    'gold': 0
                }
            return self.inventories[user_id]
        
        def add_item(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
            inventory = self.get_inventory(user_id)
            if len(inventory['items']) >= inventory['capacity']:
                return False
            
            inventory['items'].append({
                'item_id': item_id,
                'quantity': quantity
            })
            return True
        
        def remove_item(self, user_id: int, item_id: int, quantity: int = 1) -> bool:
            inventory = self.get_inventory(user_id)
            for item in inventory['items']:
                if item['item_id'] == item_id:
                    if item['quantity'] >= quantity:
                        item['quantity'] -= quantity
                        if item['quantity'] == 0:
                            inventory['items'].remove(item)
                        return True
            return False
    
    return MockInventory()

@pytest.fixture
def mock_combat():
    """Mock combat system for testing"""
    class MockCombat:
        def __init__(self):
            self.active_battles = {}
        
        def start_battle(self, attacker_id: int, defender_id: int) -> str:
            battle_id = f"battle_{len(self.active_battles)}"
            self.active_battles[battle_id] = {
                'attacker': attacker_id,
                'defender': defender_id,
                'turns': [],
                'status': 'active'
            }
            return battle_id
        
        def process_turn(self, battle_id: str, action: Dict) -> Dict:
            if battle_id not in self.active_battles:
                return None
            
            battle = self.active_battles[battle_id]
            battle['turns'].append(action)
            
            # Simulate battle result
            result = {
                'damage_dealt': 10,
                'status_effects': [],
                'is_critical': False
            }
            
            if len(battle['turns']) >= 5:
                battle['status'] = 'completed'
            
            return result
    
    return MockCombat()

@pytest.fixture
def mock_chat():
    """Mock chat system for testing"""
    class MockChat:
        def __init__(self):
            self.channels = {
                'global': [],
                'trade': [],
                'guild': {}
            }
        
        def send_message(
            self,
            channel: str,
            user_id: int,
            content: str,
            guild_id: Optional[int] = None
        ) -> Dict:
            message = {
                'id': len(self.channels[channel]),
                'channel': channel,
                'user_id': user_id,
                'content': content,
                'timestamp': datetime.utcnow()
            }
            
            if channel == 'guild':
                if guild_id not in self.channels['guild']:
                    self.channels['guild'][guild_id] = []
                self.channels['guild'][guild_id].append(message)
            else:
                self.channels[channel].append(message)
            
            return message
        
        def get_messages(
            self,
            channel: str,
            limit: int = 50,
            guild_id: Optional[int] = None
        ) -> List[Dict]:
            if channel == 'guild':
                messages = self.channels['guild'].get(guild_id, [])
            else:
                messages = self.channels[channel]
            
            return sorted(
                messages,
                key=lambda m: m['timestamp'],
                reverse=True
            )[:limit]
    
    return MockChat()

@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def test_client(event_loop):
    """Create test client for API tests"""
    from aiohttp import web
    
    async def create_app():
        app = web.Application()
        return app
    
    app = event_loop.run_until_complete(create_app())
    return app

@pytest.fixture
def mock_redis():
    """Mock Redis for testing"""
    class MockRedis:
        def __init__(self):
            self.data = {}
            self.expires = {}
        
        async def get(self, key: str) -> Optional[str]:
            if key in self.expires and self.expires[key] < datetime.utcnow():
                del self.data[key]
                del self.expires[key]
                return None
            return self.data.get(key)
        
        async def set(
            self,
            key: str,
            value: str,
            expire: Optional[int] = None
        ):
            self.data[key] = value
            if expire:
                self.expires[key] = datetime.utcnow() + timedelta(seconds=expire)
        
        async def delete(self, key: str):
            self.data.pop(key, None)
            self.expires.pop(key, None)
        
        async def exists(self, key: str) -> bool:
            return key in self.data
    
    return MockRedis()

@pytest.fixture
def mock_websocket():
    """Mock WebSocket for testing"""
    class MockWebSocket:
        def __init__(self):
            self.connected = set()
            self.messages = []
        
        async def connect(self, user_id: int):
            self.connected.add(user_id)
        
        async def disconnect(self, user_id: int):
            self.connected.discard(user_id)
        
        async def send_message(self, user_id: int, message: Dict):
            if user_id in self.connected:
                self.messages.append({
                    'user_id': user_id,
                    'message': message,
                    'timestamp': datetime.utcnow()
                })
        
        def get_messages(self, user_id: int) -> List[Dict]:
            return [
                m for m in self.messages
                if m['user_id'] == user_id
            ]
    
    return MockWebSocket()

@pytest.fixture
def mock_logger():
    """Mock logger for testing"""
    class MockLogger:
        def __init__(self):
            self.logs = []
        
        def log(self, level: str, message: str, **kwargs):
            self.logs.append({
                'level': level,
                'message': message,
                'timestamp': datetime.utcnow(),
                'metadata': kwargs
            })
        
        def get_logs(
            self,
            level: Optional[str] = None,
            start_time: Optional[datetime] = None
        ) -> List[Dict]:
            logs = self.logs
            
            if level:
                logs = [log for log in logs if log['level'] == level]
            
            if start_time:
                logs = [
                    log for log in logs
                    if log['timestamp'] >= start_time
                ]
            
            return sorted(logs, key=lambda l: l['timestamp'])
    
    return MockLogger()
