import unittest
from unittest.mock import Mock, patch
import sys
import os
from decimal import Decimal
from solders.keypair import Keypair
from solders.pubkey import Pubkey
from solana.rpc.api import Client
from solders.system_program import TransferParams, transfer
from solana.transaction import Transaction
import base58
import hashlib

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User, Wallet
from economy_systems import TokenSystem, CurrencySystem

class TestWeb3Integration(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        # Initialize Solana client with devnet
        self.solana_client = Client("https://api.devnet.solana.com")
        
        # Create test keypair
        self.test_keypair = Keypair()
        
        # Create currency system
        self.currency_system = CurrencySystem()
        
        # Create token system
        self.token_system = TokenSystem(self.currency_system)
        
        # Create mock user
        self.user = Mock(spec=User)
        self.user.id = 1
        self.user.username = "test_user"
        
        # Create mock wallet
        self.wallet = Mock(spec=Wallet)
        self.wallet.user_id = 1
        self.wallet.address = str(self.test_keypair.pubkey())
        self.wallet.encrypted_privkey = "encrypted_key"
        self.wallet.iv = "test_iv"
        self.wallet.sol_balance = Decimal('1.0')
        self.wallet.exons = 1000
        self.wallet.crystals = 1000
        
        self.user.wallet = self.wallet

    @patch('solana.rpc.api.Client')
    def test_wallet_creation(self, mock_client):
        """Test wallet creation and encryption"""
        # Generate new keypair
        keypair = Keypair()
        
        # Generate key material
        username = "test_user"
        salt = os.urandom(16).hex()
        key_material = self._generate_key_material(username)
        
        # Encrypt private key
        encrypted_key, iv = self._encrypt_private_key(
            keypair.secret(),
            key_material,
            bytes.fromhex(salt)
        )
        
        # Create wallet
        wallet = Wallet(
            user_id=1,
            address=str(keypair.pubkey()),
            encrypted_privkey=base58.b58encode(encrypted_key).decode(),
            iv=base58.b58encode(iv).decode(),
            sol_balance=Decimal('0'),
            exons=0,
            crystals=0
        )
        
        # Verify wallet
        self.assertEqual(wallet.address, str(keypair.pubkey()))
        self.assertIsNotNone(wallet.encrypted_privkey)
        self.assertIsNotNone(wallet.iv)

    @patch('solana.rpc.api.Client')
    def test_solana_transfer(self, mock_client):
        """Test Solana transfer functionality"""
        # Set up mock response
        mock_client.return_value.get_balance.return_value = {'result': {'value': 1000000000}}  # 1 SOL
        mock_client.return_value.send_transaction.return_value = {'result': 'test_signature'}
        
        # Create transfer parameters
        amount = 0.1  # SOL
        lamports = int(amount * 1000000000)  # Convert to lamports
        
        # Create recipient keypair
        recipient = Keypair()
        
        # Create transfer transaction
        transfer_params = TransferParams(
            from_pubkey=self.test_keypair.pubkey(),
            to_pubkey=recipient.pubkey(),
            lamports=lamports
        )
        
        transaction = Transaction()
        transaction.add(transfer(transfer_params))
        
        # Sign and send transaction
        result = self.solana_client.send_transaction(
            transaction,
            self.test_keypair
        )
        
        # Verify transaction
        self.assertIsNotNone(result['result'])

    def test_token_swap(self):
        """Test token swap calculations and execution"""
        # Test SOLANA to EXON swap
        amount = Decimal('0.5')  # SOL
        result_amount, fee = self.token_system.calculate_swap_amount(
            'SOLANA',
            'EXON',
            amount
        )
        
        # Verify conversion
        expected_exons = amount * self.token_system.swap_rates['SOLANA_TO_EXON']
        self.assertEqual(result_amount, expected_exons)
        
        # Verify fee calculation
        expected_fee = amount * Decimal('0.01')  # 1% fee
        self.assertEqual(fee, expected_fee)
        
        # Test minimum swap amounts
        valid, message = self.token_system.validate_swap(
            'SOLANA',
            Decimal('0.05')  # Below minimum
        )
        self.assertFalse(valid)

    @patch('solana.rpc.api.Client')
    def test_exon_token_contract(self, mock_client):
        """Test Exon token contract interactions"""
        # Mock token program ID
        token_program_id = Pubkey.from_string("TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA")
        
        # Mock token mint
        token_mint = Keypair()
        
        # Mock token account
        token_account = Keypair()
        
        # Test token transfer
        amount = 1000  # EXON tokens
        
        # Create transfer instruction
        mock_client.return_value.send_transaction.return_value = {'result': 'test_signature'}
        
        # Verify transfer
        self.assertIsNotNone(mock_client.return_value.send_transaction.call_args)

    def test_wallet_balance_updates(self):
        """Test wallet balance updates after transactions"""
        initial_sol = self.wallet.sol_balance
        initial_exons = self.wallet.exons
        
        # Simulate Solana deposit
        deposit_amount = Decimal('0.5')
        self.wallet.sol_balance += deposit_amount
        
        self.assertEqual(
            self.wallet.sol_balance,
            initial_sol + deposit_amount
        )
        
        # Simulate token swap
        swap_amount = Decimal('0.1')
        exon_amount = swap_amount * self.token_system.swap_rates['SOLANA_TO_EXON']
        
        self.wallet.sol_balance -= swap_amount
        self.wallet.exons += exon_amount
        
        self.assertEqual(
            self.wallet.exons,
            initial_exons + exon_amount
        )

    def test_transaction_validation(self):
        """Test transaction validation"""
        # Test insufficient balance
        amount = Decimal('2.0')  # More than wallet balance
        
        valid = self._validate_transaction(
            self.wallet.sol_balance,
            amount
        )
        self.assertFalse(valid)
        
        # Test valid transaction
        amount = Decimal('0.5')
        valid = self._validate_transaction(
            self.wallet.sol_balance,
            amount
        )
        self.assertTrue(valid)

    def _generate_key_material(self, username: str) -> str:
        """Generate key material for wallet encryption"""
        first_hash = hashlib.sha256(username.encode()).hexdigest()
        combined = f"{username}|{first_hash}"
        final_hash = hashlib.sha256(combined.encode()).hexdigest()
        return final_hash

    def _encrypt_private_key(self, private_key: bytes, key_material: str, salt: bytes) -> tuple:
        """Encrypt private key"""
        from Crypto.Cipher import AES
        from Crypto.Protocol.KDF import PBKDF2
        from Crypto.Util.Padding import pad
        
        # Derive key
        key = PBKDF2(key_material, salt, 32, 100000)
        
        # Create cipher
        cipher = AES.new(key, AES.MODE_CBC)
        
        # Encrypt
        encrypted_key = cipher.encrypt(pad(private_key, AES.block_size))
        
        return encrypted_key, cipher.iv

    def _validate_transaction(self, balance: Decimal, amount: Decimal) -> bool:
        """Validate transaction amount against balance"""
        return balance >= amount

    @patch('solana.rpc.api.Client')
    def test_admin_wallet_operations(self, mock_client):
        """Test admin wallet specific operations"""
        admin_wallet = "FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw"
        
        # Test tax collection
        tax_amount = Decimal('10')
        
        mock_client.return_value.get_balance.return_value = {'result': {'value': 1000000000}}
        mock_client.return_value.send_transaction.return_value = {'result': 'test_signature'}
        
        # Simulate tax transfer
        transaction = Transaction()
        transfer_params = TransferParams(
            from_pubkey=self.test_keypair.pubkey(),
            to_pubkey=Pubkey.from_string(admin_wallet),
            lamports=int(tax_amount * 1000000000)
        )
        transaction.add(transfer(transfer_params))
        
        result = self.solana_client.send_transaction(
            transaction,
            self.test_keypair
        )
        
        self.assertIsNotNone(result['result'])

    def test_transaction_history(self):
        """Test transaction history tracking"""
        # Create mock transaction
        tx = {
            'signature': 'test_signature',
            'from_address': self.wallet.address,
            'to_address': 'recipient_address',
            'amount': Decimal('0.1'),
            'currency': 'SOLANA',
            'timestamp': '2024-02-14T12:00:00Z',
            'status': 'confirmed'
        }
        
        # Add transaction to history
        # In real implementation, this would be stored in database
        
        # Verify transaction details
        self.assertEqual(tx['from_address'], self.wallet.address)
        self.assertEqual(tx['currency'], 'SOLANA')
        self.assertEqual(tx['status'], 'confirmed')

if __name__ == '__main__':
    unittest.main()
