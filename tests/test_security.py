import unittest
from unittest.mock import Mock, patch
import sys
import os
import jwt
import hashlib
from datetime import datetime, timedelta
from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Util.Padding import pad, unpad

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from db_setup import db
from models import User, Wallet
from flask_jwt_extended import create_access_token

class TestSecurity(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        app.config['TESTING'] = True
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        app.config['JWT_SECRET_KEY'] = 'test-jwt-secret'
        self.app = app
        
        with self.app.app_context():
            db.create_all()
            
            # Create test user
            self.user = User(
                username='test_user',
                password=self._hash_password('test_password'),
                salt=os.urandom(16).hex(),
                role='user'
            )
            db.session.add(self.user)
            
            # Create admin user
            self.admin = User(
                username='adminbb',
                password=self._hash_password('admin_password'),
                salt=os.urandom(16).hex(),
                role='admin'
            )
            db.session.add(self.admin)
            
            db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def _hash_password(self, password: str) -> str:
        """Hash password for testing"""
        from werkzeug.security import generate_password_hash
        return generate_password_hash(password)

    def test_authentication(self):
        """Test authentication system"""
        with self.app.test_client() as client:
            # Test successful login
            response = client.post('/login', json={
                'username': 'test_user',
                'password': 'test_password'
            })
            self.assertEqual(response.status_code, 200)
            data = response.get_json()
            self.assertIn('token', data)
            
            # Test invalid credentials
            response = client.post('/login', json={
                'username': 'test_user',
                'password': 'wrong_password'
            })
            self.assertEqual(response.status_code, 401)
            
            # Test token validation
            token = data['token']
            response = client.get(
                '/protected',
                headers={'Authorization': f'Bearer {token}'}
            )
            self.assertEqual(response.status_code, 200)
            
            # Test expired token
            expired_token = create_access_token(
                identity='test_user',
                expires_delta=timedelta(seconds=-1)
            )
            response = client.get(
                '/protected',
                headers={'Authorization': f'Bearer {expired_token}'}
            )
            self.assertEqual(response.status_code, 401)

    def test_authorization(self):
        """Test role-based access control"""
        with self.app.test_client() as client:
            # Get admin token
            response = client.post('/login', json={
                'username': 'adminbb',
                'password': 'admin_password'
            })
            admin_token = response.get_json()['token']
            
            # Get user token
            response = client.post('/login', json={
                'username': 'test_user',
                'password': 'test_password'
            })
            user_token = response.get_json()['token']
            
            # Test admin access
            response = client.get(
                '/admin/users',
                headers={'Authorization': f'Bearer {admin_token}'}
            )
            self.assertEqual(response.status_code, 200)
            
            # Test user restriction
            response = client.get(
                '/admin/users',
                headers={'Authorization': f'Bearer {user_token}'}
            )
            self.assertEqual(response.status_code, 403)

    def test_wallet_encryption(self):
        """Test wallet private key encryption"""
        with self.app.app_context():
            # Generate wallet
            private_key = os.urandom(32)
            username = "test_user"
            salt = os.urandom(16)
            
            # Generate key material
            key_material = self._generate_key_material(username)
            
            # Encrypt private key
            encrypted_key, iv = self._encrypt_private_key(
                private_key,
                key_material,
                salt
            )
            
            # Decrypt and verify
            decrypted_key = self._decrypt_private_key(
                encrypted_key,
                key_material,
                salt,
                iv
            )
            
            self.assertEqual(private_key, decrypted_key)

    def test_rate_limiting(self):
        """Test rate limiting functionality"""
        with self.app.test_client() as client:
            # Test login rate limiting
            for _ in range(5):  # Attempt multiple logins
                client.post('/login', json={
                    'username': 'test_user',
                    'password': 'test_password'
                })
            
            # Next attempt should be rate limited
            response = client.post('/login', json={
                'username': 'test_user',
                'password': 'test_password'
            })
            self.assertEqual(response.status_code, 429)
            
            # Test API rate limiting
            token = create_access_token(identity='test_user')
            for _ in range(100):  # Exceed rate limit
                client.get(
                    '/api/endpoint',
                    headers={'Authorization': f'Bearer {token}'}
                )
            
            response = client.get(
                '/api/endpoint',
                headers={'Authorization': f'Bearer {token}'}
            )
            self.assertEqual(response.status_code, 429)

    def test_input_validation(self):
        """Test input validation and sanitization"""
        with self.app.test_client() as client:
            # Test SQL injection prevention
            response = client.post('/login', json={
                'username': "' OR '1'='1",
                'password': "' OR '1'='1"
            })
            self.assertEqual(response.status_code, 401)
            
            # Test XSS prevention
            response = client.post('/api/message', json={
                'content': '<script>alert("XSS")</script>'
            })
            self.assertEqual(response.status_code, 400)
            
            # Test input length limits
            response = client.post('/register', json={
                'username': 'a' * 100,  # Too long
                'password': 'test_password'
            })
            self.assertEqual(response.status_code, 400)

    def test_session_management(self):
        """Test session management"""
        with self.app.test_client() as client:
            # Login and get token
            response = client.post('/login', json={
                'username': 'test_user',
                'password': 'test_password'
            })
            token = response.get_json()['token']
            
            # Test concurrent session limit
            tokens = []
            for _ in range(5):  # Create multiple sessions
                response = client.post('/login', json={
                    'username': 'test_user',
                    'password': 'test_password'
                })
                tokens.append(response.get_json()['token'])
            
            # Verify session limit
            response = client.post('/login', json={
                'username': 'test_user',
                'password': 'test_password'
            })
            self.assertEqual(response.status_code, 400)
            self.assertIn('max_sessions_reached', response.get_json()['message'])

    def test_csrf_protection(self):
        """Test CSRF protection"""
        with self.app.test_client() as client:
            # Get CSRF token
            response = client.get('/csrf-token')
            csrf_token = response.get_json()['csrf_token']
            
            # Test with valid CSRF token
            response = client.post(
                '/api/action',
                headers={'X-CSRF-Token': csrf_token}
            )
            self.assertEqual(response.status_code, 200)
            
            # Test without CSRF token
            response = client.post('/api/action')
            self.assertEqual(response.status_code, 400)
            
            # Test with invalid CSRF token
            response = client.post(
                '/api/action',
                headers={'X-CSRF-Token': 'invalid_token'}
            )
            self.assertEqual(response.status_code, 400)

    def test_password_security(self):
        """Test password security features"""
        with self.app.test_client() as client:
            # Test password complexity requirements
            response = client.post('/register', json={
                'username': 'new_user',
                'password': 'weak'  # Too simple
            })
            self.assertEqual(response.status_code, 400)
            
            # Test password history
            token = create_access_token(identity='test_user')
            
            # Change password multiple times
            passwords = ['Password1!', 'Password2@', 'Password3#']
            for password in passwords:
                response = client.post(
                    '/change-password',
                    headers={'Authorization': f'Bearer {token}'},
                    json={'new_password': password}
                )
                self.assertEqual(response.status_code, 200)
            
            # Try to reuse old password
            response = client.post(
                '/change-password',
                headers={'Authorization': f'Bearer {token}'},
                json={'new_password': passwords[0]}
            )
            self.assertEqual(response.status_code, 400)

    def _generate_key_material(self, username: str) -> str:
        """Generate key material for wallet encryption"""
        first_hash = hashlib.sha256(username.encode()).hexdigest()
        combined = f"{username}|{first_hash}"
        final_hash = hashlib.sha256(combined.encode()).hexdigest()
        return final_hash

    def _encrypt_private_key(self, private_key: bytes, key_material: str, salt: bytes) -> tuple:
        """Encrypt private key"""
        key = PBKDF2(key_material, salt, 32, 100000)
        cipher = AES.new(key, AES.MODE_CBC)
        encrypted_key = cipher.encrypt(pad(private_key, AES.block_size))
        return encrypted_key, cipher.iv

    def _decrypt_private_key(self, encrypted_key: bytes, key_material: str, salt: bytes, iv: bytes) -> bytes:
        """Decrypt private key"""
        key = PBKDF2(key_material, salt, 32, 100000)
        cipher = AES.new(key, AES.MODE_CBC, iv)
        decrypted_key = unpad(cipher.decrypt(encrypted_key), AES.block_size)
        return decrypted_key

if __name__ == '__main__':
    unittest.main()
