import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from decimal import Decimal
import json
import random
import string

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from db_setup import db
from models import User, Wallet, Gate, Guild, Item
from game_manager import MainGameManager
from economy_systems import CurrencySystem

class TestErrorHandling(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        self.app = app
        self.client = self.app.test_client()
        self.game_manager = MainGameManager()
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.user = User(
                username='test_user',
                password='hashed_password',
                salt='test_salt',
                role='user',
                level=10
            )
            db.session.add(self.user)
            
            # Create wallet
            self.wallet = Wallet(
                user_id=1,
                address='test_address',
                encrypted_privkey='test_key',
                iv='test_iv',
                sol_balance=Decimal('1.0'),
                crystals=1000,
                exons=1000
            )
            db.session.add(self.wallet)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_invalid_inputs(self):
        """Test handling of invalid input data"""
        # Test SQL injection attempts
        response = self.client.post('/login', json={
            'username': "' OR '1'='1",
            'password': "' OR '1'='1"
        })
        self.assertEqual(response.status_code, 401)
        
        # Test XSS attempts
        response = self.client.post('/register', json={
            'username': '<script>alert("XSS")</script>',
            'password': 'test_password'
        })
        self.assertEqual(response.status_code, 400)
        
        # Test oversized inputs
        long_string = ''.join(random.choices(string.ascii_letters, k=10000))
        response = self.client.post('/register', json={
            'username': long_string,
            'password': 'test_password'
        })
        self.assertEqual(response.status_code, 400)
        
        # Test invalid JSON
        response = self.client.post(
            '/api/action',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)

    def test_database_errors(self):
        """Test handling of database errors"""
        with self.app.app_context():
            # Test duplicate key
            duplicate_user = User(
                username='test_user',  # Same username
                password='other_password',
                salt='other_salt',
                role='user'
            )
            db.session.add(duplicate_user)
            with self.assertRaises(Exception):
                db.session.commit()
            db.session.rollback()
            
            # Test invalid foreign key
            invalid_wallet = Wallet(
                user_id=999,  # Non-existent user
                address='invalid_address',
                encrypted_privkey='invalid_key',
                iv='invalid_iv'
            )
            db.session.add(invalid_wallet)
            with self.assertRaises(Exception):
                db.session.commit()
            db.session.rollback()
            
            # Test transaction rollback
            try:
                with db.session.begin_nested():
                    user = User.query.get(self.user.id)
                    user.crystals += 100  # Invalid column
                    db.session.commit()
            except Exception:
                db.session.rollback()
            
            user = User.query.get(self.user.id)
            self.assertFalse(hasattr(user, 'crystals'))

    def test_network_errors(self):
        """Test handling of network-related errors"""
        # Test timeout handling
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.Timeout
            response = self.client.get('/api/external_service')
            self.assertEqual(response.status_code, 504)
        
        # Test connection error handling
        with patch('requests.get') as mock_get:
            mock_get.side_effect = requests.ConnectionError
            response = self.client.get('/api/external_service')
            self.assertEqual(response.status_code, 503)
        
        # Test invalid response handling
        with patch('requests.get') as mock_get:
            mock_get.return_value.json.side_effect = ValueError
            response = self.client.get('/api/external_service')
            self.assertEqual(response.status_code, 502)

    def test_game_state_errors(self):
        """Test handling of invalid game states"""
        with self.app.app_context():
            # Test entering gate with insufficient level
            gate = Gate(
                name='High Level Gate',
                grade='S',
                min_level=100,  # Higher than user level
                max_players=10,
                crystal_reward=1000
            )
            db.session.add(gate)
            db.session.commit()
            
            result = self.game_manager.process_command(
                'gate_enter',
                self.user.id,
                {'gate_id': gate.id}
            )
            self.assertEqual(result['status'], 'error')
            self.assertIn('level requirement', result['message'].lower())
            
            # Test joining full party
            party_result = self.game_manager.process_command(
                'party_create',
                self.user.id,
                {'name': "Full Party", 'max_members': 1}
            )
            
            result = self.game_manager.process_command(
                'party_join',
                2,  # Different user
                {'party_id': party_result['party_id']}
            )
            self.assertEqual(result['status'], 'error')
            self.assertIn('full', result['message'].lower())
            
            # Test invalid item usage
            result = self.game_manager.process_command(
                'use_item',
                self.user.id,
                {'item_id': 999}  # Non-existent item
            )
            self.assertEqual(result['status'], 'error')
            self.assertIn('not found', result['message'].lower())

    def test_currency_errors(self):
        """Test handling of currency-related errors"""
        with self.app.app_context():
            # Test insufficient funds
            result = self.game_manager.process_command(
                'token_swap',
                self.user.id,
                {
                    'from_currency': 'SOLANA',
                    'to_currency': 'EXON',
                    'amount': Decimal('100.0')  # More than balance
                }
            )
            self.assertEqual(result['status'], 'error')
            self.assertIn('insufficient', result['message'].lower())
            
            # Test invalid currency
            result = self.game_manager.process_command(
                'token_swap',
                self.user.id,
                {
                    'from_currency': 'INVALID',
                    'to_currency': 'EXON',
                    'amount': Decimal('1.0')
                }
            )
            self.assertEqual(result['status'], 'error')
            self.assertIn('invalid currency', result['message'].lower())
            
            # Test negative amount
            result = self.game_manager.process_command(
                'token_swap',
                self.user.id,
                {
                    'from_currency': 'SOLANA',
                    'to_currency': 'EXON',
                    'amount': Decimal('-1.0')
                }
            )
            self.assertEqual(result['status'], 'error')
            self.assertIn('invalid amount', result['message'].lower())

    def test_permission_errors(self):
        """Test handling of permission-related errors"""
        with self.app.app_context():
            # Test unauthorized admin access
            response = self.client.get('/admin/users')
            self.assertEqual(response.status_code, 401)
            
            # Test invalid role elevation
            response = self.client.post('/admin/users/1', json={
                'role': 'admin'
            })
            self.assertEqual(response.status_code, 401)
            
            # Test guild leadership actions
            guild = Guild(
                name='Test Guild',
                leader_id=2,  # Different user
                level=1
            )
            db.session.add(guild)
            db.session.commit()
            
            result = self.game_manager.process_command(
                'guild_kick',
                self.user.id,  # Not the leader
                {
                    'guild_id': guild.id,
                    'user_id': 3
                }
            )
            self.assertEqual(result['status'], 'error')
            self.assertIn('permission', result['message'].lower())

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        # Test API rate limiting
        for _ in range(100):  # Exceed rate limit
            response = self.client.get('/api/status')
        
        response = self.client.get('/api/status')
        self.assertEqual(response.status_code, 429)
        
        # Test login rate limiting
        for _ in range(5):  # Exceed login attempts
            response = self.client.post('/login', json={
                'username': 'test_user',
                'password': 'wrong_password'
            })
        
        response = self.client.post('/login', json={
            'username': 'test_user',
            'password': 'test_password'
        })
        self.assertEqual(response.status_code, 429)

    def test_websocket_errors(self):
        """Test WebSocket error handling"""
        # Test invalid message format
        with self.client.websocket_connect('/ws') as websocket:
            websocket.send(b'invalid message')
            response = websocket.receive()
            self.assertEqual(response['error'], 'invalid_format')
        
        # Test unauthorized access
        with self.client.websocket_connect('/ws') as websocket:
            websocket.send(json.dumps({
                'type': 'admin_action',
                'data': {}
            }))
            response = websocket.receive()
            self.assertEqual(response['error'], 'unauthorized')
        
        # Test connection limit
        connections = []
        try:
            for _ in range(1000):  # Exceed connection limit
                connections.append(self.client.websocket_connect('/ws'))
        except Exception as e:
            self.assertIn('connection_limit', str(e))
        finally:
            for conn in connections:
                conn.close()

    def test_recovery_mechanisms(self):
        """Test system recovery mechanisms"""
        with self.app.app_context():
            # Test transaction retry
            with patch('sqlalchemy.orm.Session.commit') as mock_commit:
                mock_commit.side_effect = [Exception, None]  # Fail once, then succeed
                result = self.game_manager.process_command(
                    'gate_enter',
                    self.user.id,
                    {'gate_id': 1}
                )
                self.assertEqual(result['status'], 'success')
            
            # Test state recovery
            gate_state = {
                'gate_id': 1,
                'players': [self.user.id],
                'start_time': datetime.utcnow() - timedelta(hours=2)  # Expired
            }
            self.game_manager.game_state.active_gates[1] = gate_state
            
            # System should detect and clean up expired state
            self.game_manager.update_game_state()
            self.assertNotIn(1, self.game_manager.game_state.active_gates)
            
            # Test connection recovery
            with patch('websockets.connect') as mock_connect:
                mock_connect.side_effect = [Exception, Mock()]  # Fail once, then succeed
                result = self.game_manager.process_command(
                    'websocket_connect',
                    self.user.id,
                    {}
                )
                self.assertEqual(result['status'], 'success')

if __name__ == '__main__':
    unittest.main()
