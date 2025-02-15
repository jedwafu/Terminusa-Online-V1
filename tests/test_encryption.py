import unittest
from unittest.mock import Mock, patch
import sys
import os
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
import base64
import json
import hashlib
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.primitives import padding
from cryptography.hazmat.backends import default_backend

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class EncryptionError(Exception):
    """Encryption error"""
    pass

class EncryptionSystem:
    """Manages data encryption and security"""
    def __init__(self, master_key: bytes = None):
        if master_key is None:
            master_key = Fernet.generate_key()
        self.master_key = master_key
        self.fernet = Fernet(master_key)
        self.backend = default_backend()

    def generate_key(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Generate encryption key from password"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        
        key = kdf.derive(password.encode())
        return key, salt

    def encrypt_data(self, data: Any) -> bytes:
        """Encrypt data using Fernet"""
        try:
            serialized = json.dumps(data).encode()
            return self.fernet.encrypt(serialized)
        except Exception as e:
            raise EncryptionError(f"Encryption failed: {str(e)}")

    def decrypt_data(self, encrypted: bytes) -> Any:
        """Decrypt data using Fernet"""
        try:
            decrypted = self.fernet.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception as e:
            raise EncryptionError(f"Decryption failed: {str(e)}")

    def encrypt_file(self, file_path: str, key: bytes) -> None:
        """Encrypt file using AES"""
        try:
            iv = os.urandom(16)
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=self.backend
            )
            encryptor = cipher.encryptor()
            padder = padding.PKCS7(128).padder()
            
            with open(file_path, 'rb') as f:
                data = f.read()
            
            padded_data = padder.update(data) + padder.finalize()
            encrypted_data = encryptor.update(padded_data) + encryptor.finalize()
            
            with open(f"{file_path}.encrypted", 'wb') as f:
                f.write(iv + encrypted_data)
            
        except Exception as e:
            raise EncryptionError(f"File encryption failed: {str(e)}")

    def decrypt_file(self, file_path: str, key: bytes) -> None:
        """Decrypt file using AES"""
        try:
            with open(file_path, 'rb') as f:
                iv = f.read(16)
                encrypted_data = f.read()
            
            cipher = Cipher(
                algorithms.AES(key),
                modes.CBC(iv),
                backend=self.backend
            )
            decryptor = cipher.decryptor()
            unpadder = padding.PKCS7(128).unpadder()
            
            decrypted_data = decryptor.update(encrypted_data) + decryptor.finalize()
            unpadded_data = unpadder.update(decrypted_data) + unpadder.finalize()
            
            output_path = file_path.replace('.encrypted', '.decrypted')
            with open(output_path, 'wb') as f:
                f.write(unpadded_data)
            
        except Exception as e:
            raise EncryptionError(f"File decryption failed: {str(e)}")

    def hash_password(self, password: str, salt: bytes = None) -> Tuple[bytes, bytes]:
        """Hash password using PBKDF2"""
        if salt is None:
            salt = os.urandom(16)
        
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
            backend=self.backend
        )
        
        hashed = kdf.derive(password.encode())
        return hashed, salt

    def verify_password(
        self,
        password: str,
        hashed: bytes,
        salt: bytes
    ) -> bool:
        """Verify password hash"""
        try:
            kdf = PBKDF2HMAC(
                algorithm=hashes.SHA256(),
                length=32,
                salt=salt,
                iterations=100000,
                backend=self.backend
            )
            
            kdf.verify(password.encode(), hashed)
            return True
        except Exception:
            return False

    def generate_token(self, data: Dict) -> str:
        """Generate encrypted token"""
        try:
            serialized = json.dumps(data).encode()
            encrypted = self.fernet.encrypt(serialized)
            return base64.urlsafe_b64encode(encrypted).decode()
        except Exception as e:
            raise EncryptionError(f"Token generation failed: {str(e)}")

    def validate_token(self, token: str) -> Optional[Dict]:
        """Validate and decrypt token"""
        try:
            encrypted = base64.urlsafe_b64decode(token.encode())
            decrypted = self.fernet.decrypt(encrypted)
            return json.loads(decrypted.decode())
        except Exception:
            return None

class TestEncryption(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.encryption = EncryptionSystem()
        self.test_data = {
            'username': 'test_user',
            'email': 'test@example.com',
            'settings': {
                'theme': 'dark',
                'notifications': True
            }
        }

    def test_data_encryption(self):
        """Test basic data encryption/decryption"""
        # Encrypt data
        encrypted = self.encryption.encrypt_data(self.test_data)
        self.assertIsInstance(encrypted, bytes)
        
        # Decrypt data
        decrypted = self.encryption.decrypt_data(encrypted)
        self.assertEqual(decrypted, self.test_data)

    def test_key_generation(self):
        """Test encryption key generation"""
        password = "test_password"
        
        # Generate key
        key, salt = self.encryption.generate_key(password)
        
        # Verify key properties
        self.assertEqual(len(key), 32)  # 256 bits
        self.assertEqual(len(salt), 16)  # 128 bits
        
        # Generate key with same salt
        key2, _ = self.encryption.generate_key(password, salt)
        self.assertEqual(key, key2)

    def test_file_encryption(self):
        """Test file encryption/decryption"""
        # Create test file
        test_file = "test_file.txt"
        test_content = b"Test file content"
        
        with open(test_file, 'wb') as f:
            f.write(test_content)
        
        try:
            # Generate key
            key, _ = self.encryption.generate_key("test_password")
            
            # Encrypt file
            self.encryption.encrypt_file(test_file, key)
            self.assertTrue(os.path.exists(f"{test_file}.encrypted"))
            
            # Decrypt file
            self.encryption.decrypt_file(f"{test_file}.encrypted", key)
            
            # Verify content
            with open(f"{test_file}.decrypted", 'rb') as f:
                decrypted_content = f.read()
            
            self.assertEqual(decrypted_content, test_content)
            
        finally:
            # Clean up
            for suffix in ['', '.encrypted', '.decrypted']:
                path = f"{test_file}{suffix}"
                if os.path.exists(path):
                    os.remove(path)

    def test_password_hashing(self):
        """Test password hashing"""
        password = "test_password"
        
        # Hash password
        hashed, salt = self.encryption.hash_password(password)
        
        # Verify correct password
        self.assertTrue(
            self.encryption.verify_password(password, hashed, salt)
        )
        
        # Verify incorrect password
        self.assertFalse(
            self.encryption.verify_password("wrong_password", hashed, salt)
        )

    def test_token_generation(self):
        """Test token generation/validation"""
        token_data = {
            'user_id': 123,
            'role': 'admin',
            'permissions': ['read', 'write']
        }
        
        # Generate token
        token = self.encryption.generate_token(token_data)
        self.assertIsInstance(token, str)
        
        # Validate token
        validated = self.encryption.validate_token(token)
        self.assertEqual(validated, token_data)
        
        # Validate invalid token
        self.assertIsNone(
            self.encryption.validate_token("invalid_token")
        )

    def test_encryption_error_handling(self):
        """Test encryption error handling"""
        # Test invalid data encryption
        with self.assertRaises(EncryptionError):
            self.encryption.encrypt_data(object())  # Non-serializable object
        
        # Test invalid data decryption
        with self.assertRaises(EncryptionError):
            self.encryption.decrypt_data(b"invalid_data")

    def test_large_data_encryption(self):
        """Test encryption of large data"""
        # Create large dataset
        large_data = {
            'array': list(range(1000)),
            'string': 'x' * 10000
        }
        
        # Encrypt and decrypt
        encrypted = self.encryption.encrypt_data(large_data)
        decrypted = self.encryption.decrypt_data(encrypted)
        
        self.assertEqual(decrypted, large_data)

    def test_multiple_encryptions(self):
        """Test multiple encryption operations"""
        # Encrypt same data multiple times
        results = []
        for _ in range(3):
            encrypted = self.encryption.encrypt_data(self.test_data)
            results.append(encrypted)
        
        # Each encryption should be different
        self.assertNotEqual(results[0], results[1])
        self.assertNotEqual(results[1], results[2])
        
        # But should decrypt to same data
        for encrypted in results:
            decrypted = self.encryption.decrypt_data(encrypted)
            self.assertEqual(decrypted, self.test_data)

    def test_key_persistence(self):
        """Test encryption key persistence"""
        # Create encryption systems with same key
        key = Fernet.generate_key()
        encryption1 = EncryptionSystem(key)
        encryption2 = EncryptionSystem(key)
        
        # Encrypt with first system
        encrypted = encryption1.encrypt_data(self.test_data)
        
        # Decrypt with second system
        decrypted = encryption2.decrypt_data(encrypted)
        self.assertEqual(decrypted, self.test_data)

    def test_binary_data_encryption(self):
        """Test binary data encryption"""
        binary_data = os.urandom(1000)
        
        # Encrypt binary data
        encrypted = self.encryption.encrypt_data(
            {'binary': base64.b64encode(binary_data).decode()}
        )
        
        # Decrypt and verify
        decrypted = self.encryption.decrypt_data(encrypted)
        recovered = base64.b64decode(decrypted['binary'].encode())
        
        self.assertEqual(recovered, binary_data)

if __name__ == '__main__':
    unittest.main()
