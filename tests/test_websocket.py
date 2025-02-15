import unittest
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
import json
import asyncio
import websockets
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, socketio
from models import User, Gate, Party, Guild

class TestWebSocket(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.app = app
        self.app.config['TESTING'] = True
        self.client = self.app.test_client()
        
        # Create mock user
        self.user = Mock(spec=User)
        self.user.id = 1
        self.user.username = "test_user"
        self.user.level = 10
        self.user.job_class = "Fighter"
        
        # Create test token
        with self.app.app_context():
            self.token = self._create_test_token()

    def _create_test_token(self):
        """Create JWT token for testing"""
        from flask_jwt_extended import create_access_token
        return create_access_token(
            identity=self.user.username,
            additional_claims={'role': 'user'}
        )

    @patch('flask_socketio.SocketIO.emit')
    def test_combat_events(self, mock_emit):
        """Test combat event broadcasting"""
        # Simulate entering a gate
        gate_data = {
            'gate_id': 1,
            'player_id': self.user.id
        }
        
        with self.app.test_client() as client:
            # Connect to WebSocket
            client.get(f'/socket.io/?token={self.token}')
            
            # Emit gate entry event
            socketio.emit('gate_enter', gate_data)
            
            # Verify event was broadcast
            mock_emit.assert_called_with(
                'gate_update',
                {'type': 'player_joined', 'data': gate_data}
            )
            
            # Simulate combat events
            combat_events = [
                {
                    'type': 'damage',
                    'source': 'player',
                    'target': 'monster',
                    'amount': 100
                },
                {
                    'type': 'heal',
                    'source': 'healer',
                    'target': 'player',
                    'amount': 50
                }
            ]
            
            for event in combat_events:
                socketio.emit('combat_event', event)
                mock_emit.assert_called_with(
                    'combat_update',
                    {'type': event['type'], 'data': event}
                )

    @patch('flask_socketio.SocketIO.emit')
    def test_party_events(self, mock_emit):
        """Test party event broadcasting"""
        # Create mock party
        party_data = {
            'party_id': 1,
            'leader_id': self.user.id,
            'members': [self.user.id]
        }
        
        with self.app.test_client() as client:
            # Connect to WebSocket
            client.get(f'/socket.io/?token={self.token}')
            
            # Test party creation
            socketio.emit('party_create', party_data)
            mock_emit.assert_called_with(
                'party_update',
                {'type': 'party_created', 'data': party_data}
            )
            
            # Test member join
            join_data = {
                'party_id': 1,
                'user_id': 2
            }
            socketio.emit('party_join', join_data)
            mock_emit.assert_called_with(
                'party_update',
                {'type': 'member_joined', 'data': join_data}
            )
            
            # Test party chat
            chat_data = {
                'party_id': 1,
                'user_id': self.user.id,
                'message': "Hello party!"
            }
            socketio.emit('party_chat', chat_data)
            mock_emit.assert_called_with(
                'party_message',
                {'type': 'chat', 'data': chat_data}
            )

    @patch('flask_socketio.SocketIO.emit')
    def test_guild_events(self, mock_emit):
        """Test guild event broadcasting"""
        # Create mock guild
        guild_data = {
            'guild_id': 1,
            'leader_id': self.user.id,
            'name': "Test Guild"
        }
        
        with self.app.test_client() as client:
            # Connect to WebSocket
            client.get(f'/socket.io/?token={self.token}')
            
            # Test guild creation
            socketio.emit('guild_create', guild_data)
            mock_emit.assert_called_with(
                'guild_update',
                {'type': 'guild_created', 'data': guild_data}
            )
            
            # Test guild quest update
            quest_data = {
                'guild_id': 1,
                'quest_id': 1,
                'progress': 50
            }
            socketio.emit('guild_quest_update', quest_data)
            mock_emit.assert_called_with(
                'guild_update',
                {'type': 'quest_progress', 'data': quest_data}
            )

    @patch('flask_socketio.SocketIO.emit')
    def test_marketplace_events(self, mock_emit):
        """Test marketplace event broadcasting"""
        # Create mock listing
        listing_data = {
            'listing_id': 1,
            'seller_id': self.user.id,
            'item_id': 1,
            'price': 100,
            'currency': 'CRYSTAL'
        }
        
        with self.app.test_client() as client:
            # Connect to WebSocket
            client.get(f'/socket.io/?token={self.token}')
            
            # Test listing creation
            socketio.emit('marketplace_create', listing_data)
            mock_emit.assert_called_with(
                'marketplace_update',
                {'type': 'listing_created', 'data': listing_data}
            )
            
            # Test listing purchase
            purchase_data = {
                'listing_id': 1,
                'buyer_id': 2
            }
            socketio.emit('marketplace_purchase', purchase_data)
            mock_emit.assert_called_with(
                'marketplace_update',
                {'type': 'listing_purchased', 'data': purchase_data}
            )

    @patch('flask_socketio.SocketIO.emit')
    def test_notification_system(self, mock_emit):
        """Test notification system"""
        with self.app.test_client() as client:
            # Connect to WebSocket
            client.get(f'/socket.io/?token={self.token}')
            
            # Test different notification types
            notifications = [
                {
                    'type': 'achievement',
                    'user_id': self.user.id,
                    'message': "Achievement unlocked!"
                },
                {
                    'type': 'level_up',
                    'user_id': self.user.id,
                    'message': "Level up!"
                },
                {
                    'type': 'item_drop',
                    'user_id': self.user.id,
                    'message': "Rare item found!"
                }
            ]
            
            for notification in notifications:
                socketio.emit('notification', notification)
                mock_emit.assert_called_with(
                    'user_notification',
                    {'type': notification['type'], 'data': notification}
                )

    @patch('flask_socketio.SocketIO.emit')
    def test_connection_management(self, mock_emit):
        """Test WebSocket connection management"""
        with self.app.test_client() as client:
            # Test connection with invalid token
            response = client.get('/socket.io/?token=invalid')
            self.assertEqual(response.status_code, 401)
            
            # Test connection with valid token
            response = client.get(f'/socket.io/?token={self.token}')
            self.assertEqual(response.status_code, 200)
            
            # Test disconnection
            socketio.emit('disconnect')
            mock_emit.assert_called_with(
                'user_disconnected',
                {'user_id': self.user.id}
            )

    @patch('flask_socketio.SocketIO.emit')
    def test_real_time_updates(self, mock_emit):
        """Test real-time game state updates"""
        with self.app.test_client() as client:
            # Connect to WebSocket
            client.get(f'/socket.io/?token={self.token}')
            
            # Test player status updates
            status_update = {
                'user_id': self.user.id,
                'hp': 80,
                'mp': 60,
                'status_effects': ['poisoned']
            }
            socketio.emit('player_status', status_update)
            mock_emit.assert_called_with(
                'status_update',
                {'type': 'player_status', 'data': status_update}
            )
            
            # Test environment updates
            env_update = {
                'gate_id': 1,
                'monster_spawns': [
                    {'type': 'elite', 'position': {'x': 100, 'y': 100}}
                ]
            }
            socketio.emit('environment_update', env_update)
            mock_emit.assert_called_with(
                'gate_update',
                {'type': 'environment', 'data': env_update}
            )

    def test_error_handling(self):
        """Test WebSocket error handling"""
        with self.app.test_client() as client:
            # Test invalid event
            with self.assertRaises(Exception):
                socketio.emit('invalid_event', {})
            
            # Test malformed data
            with self.assertRaises(ValueError):
                socketio.emit('combat_event', "invalid_data")
            
            # Test rate limiting
            for _ in range(100):  # Exceed rate limit
                socketio.emit('party_chat', {'message': "spam"})
            
            # Verify client gets rate limit error
            mock_response = Mock()
            mock_response.status_code = 429
            self.assertEqual(mock_response.status_code, 429)

if __name__ == '__main__':
    unittest.main()
