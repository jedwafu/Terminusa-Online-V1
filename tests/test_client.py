import unittest
from unittest.mock import Mock, patch
import sys
import os
import json
import asyncio
import websockets
from datetime import datetime, timedelta

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from client import GameClient, ClientConfig
from models import User, Gate, Party

class TestGameClient(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.config = ClientConfig(
            server_url="ws://localhost:5000",
            api_url="http://localhost:5000",
            username="test_user",
            password="test_password"
        )
        
        self.client = GameClient(self.config)
        
        # Mock token
        self.token = "test_token"
        self.client.token = self.token

    @patch('websockets.connect')
    @patch('requests.post')
    def test_client_authentication(self, mock_post, mock_ws_connect):
        """Test client authentication process"""
        # Mock login response
        mock_post.return_value.json.return_value = {
            'status': 'success',
            'token': self.token,
            'user': {
                'id': 1,
                'username': 'test_user',
                'level': 10
            }
        }
        
        # Test login
        success = self.client.login()
        self.assertTrue(success)
        self.assertEqual(self.client.token, self.token)
        
        # Verify WebSocket connection uses token
        mock_ws_connect.assert_called_with(
            f"{self.config.server_url}/ws?token={self.token}"
        )

    @patch('websockets.connect')
    def test_websocket_communication(self, mock_ws_connect):
        """Test WebSocket message handling"""
        # Mock WebSocket
        mock_ws = Mock()
        mock_ws_connect.return_value.__aenter__.return_value = mock_ws
        
        # Test message sending
        async def test_send():
            await self.client.send_message({
                'type': 'chat',
                'content': 'Hello'
            })
            mock_ws.send.assert_called_with(json.dumps({
                'type': 'chat',
                'content': 'Hello'
            }))
        
        asyncio.run(test_send())
        
        # Test message receiving
        mock_ws.recv.return_value = json.dumps({
            'type': 'chat',
            'sender': 'other_user',
            'content': 'Hi!'
        })
        
        async def test_receive():
            message = await self.client.receive_message()
            self.assertEqual(message['type'], 'chat')
            self.assertEqual(message['content'], 'Hi!')
        
        asyncio.run(test_receive())

    def test_command_handling(self):
        """Test client command handling"""
        # Test command parsing
        commands = [
            "/help",
            "/party create Test Party",
            "/trade user_2 item_1",
            "/gate enter 1"
        ]
        
        for command in commands:
            parsed = self.client.parse_command(command)
            self.assertIsNotNone(parsed)
            self.assertIn('command', parsed)
            self.assertIn('args', parsed)
        
        # Test invalid command
        parsed = self.client.parse_command("invalid command")
        self.assertIsNone(parsed)

    @patch('requests.get')
    def test_game_state_updates(self, mock_get):
        """Test game state synchronization"""
        # Mock state response
        mock_get.return_value.json.return_value = {
            'hp': 100,
            'mp': 50,
            'level': 10,
            'experience': 1000,
            'location': 'town'
        }
        
        # Update state
        self.client.update_game_state()
        
        # Verify state
        self.assertEqual(self.client.game_state['hp'], 100)
        self.assertEqual(self.client.game_state['mp'], 50)
        self.assertEqual(self.client.game_state['level'], 10)

    @patch('requests.post')
    def test_combat_system(self, mock_post):
        """Test client-side combat handling"""
        # Mock combat response
        mock_post.return_value.json.return_value = {
            'status': 'success',
            'combat_log': [
                {'type': 'damage', 'value': 50},
                {'type': 'heal', 'value': 30}
            ],
            'rewards': {
                'experience': 100,
                'items': ['potion']
            }
        }
        
        # Process combat
        result = self.client.process_combat_event({
            'type': 'combat',
            'target': 'monster_1'
        })
        
        # Verify combat processing
        self.assertTrue(result['status'] == 'success')
        self.assertEqual(len(result['combat_log']), 2)
        self.assertIn('rewards', result)

    def test_inventory_management(self):
        """Test client-side inventory management"""
        # Add items
        items = [
            {'id': 1, 'name': 'Sword', 'type': 'weapon'},
            {'id': 2, 'name': 'Potion', 'type': 'consumable'}
        ]
        
        for item in items:
            self.client.add_to_inventory(item)
        
        # Verify inventory
        self.assertEqual(len(self.client.inventory), 2)
        
        # Use item
        result = self.client.use_item(2)  # Use potion
        self.assertTrue(result)
        self.assertEqual(len(self.client.inventory), 1)

    @patch('requests.get')
    def test_party_system(self, mock_get):
        """Test client-side party handling"""
        # Mock party data
        mock_get.return_value.json.return_value = {
            'party_id': 1,
            'leader': 'test_user',
            'members': [
                {'username': 'test_user', 'level': 10},
                {'username': 'member_1', 'level': 8}
            ]
        }
        
        # Get party info
        party_info = self.client.get_party_info()
        
        # Verify party data
        self.assertEqual(party_info['party_id'], 1)
        self.assertEqual(len(party_info['members']), 2)
        self.assertEqual(party_info['leader'], 'test_user')

    def test_ui_updates(self):
        """Test client UI update handling"""
        # Mock UI elements
        ui_elements = {
            'hp_bar': Mock(),
            'mp_bar': Mock(),
            'exp_bar': Mock(),
            'chat_box': Mock()
        }
        self.client.ui_elements = ui_elements
        
        # Test HP update
        self.client.update_ui('hp', 80)
        ui_elements['hp_bar'].update.assert_called_with(80)
        
        # Test chat message
        self.client.update_ui('chat', 'Hello!')
        ui_elements['chat_box'].append.assert_called_with('Hello!')

    @patch('requests.get')
    def test_marketplace_interaction(self, mock_get):
        """Test client-side marketplace functionality"""
        # Mock marketplace data
        mock_get.return_value.json.return_value = {
            'listings': [
                {
                    'id': 1,
                    'item': {'name': 'Sword', 'price': 100},
                    'seller': 'seller_1'
                }
            ]
        }
        
        # Get marketplace listings
        listings = self.client.get_marketplace_listings()
        
        # Verify listings
        self.assertEqual(len(listings['listings']), 1)
        self.assertEqual(listings['listings'][0]['item']['name'], 'Sword')

    def test_error_handling(self):
        """Test client-side error handling"""
        # Test network error
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Network error")
            result = self.client.safe_request(lambda: requests.get('/api/test'))
            self.assertFalse(result['success'])
            self.assertIn('error', result)
        
        # Test invalid response
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.side_effect = ValueError
            result = self.client.safe_request(lambda: requests.get('/api/test'))
            self.assertFalse(result['success'])
            self.assertIn('error', result)

    def test_client_configuration(self):
        """Test client configuration management"""
        # Test config loading
        config = {
            'server_url': 'ws://localhost:5000',
            'api_url': 'http://localhost:5000',
            'username': 'test_user',
            'keybindings': {
                'inventory': 'i',
                'character': 'c',
                'map': 'm'
            }
        }
        
        self.client.load_config(config)
        
        # Verify config
        self.assertEqual(self.client.config.server_url, config['server_url'])
        self.assertEqual(self.client.config.api_url, config['api_url'])
        self.assertEqual(
            self.client.config.keybindings['inventory'],
            config['keybindings']['inventory']
        )

    def test_offline_functionality(self):
        """Test client behavior when offline"""
        # Simulate offline mode
        self.client.is_online = False
        
        # Test command queueing
        self.client.queue_command({
            'type': 'movement',
            'direction': 'north'
        })
        
        self.assertEqual(len(self.client.command_queue), 1)
        
        # Test state caching
        self.client.cache_game_state({
            'hp': 100,
            'mp': 50,
            'inventory': ['potion']
        })
        
        self.assertIsNotNone(self.client.cached_state)
        self.assertEqual(self.client.cached_state['hp'], 100)

if __name__ == '__main__':
    unittest.main()
