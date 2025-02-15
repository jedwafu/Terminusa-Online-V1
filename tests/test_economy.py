import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import uuid
import json

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class CurrencyType(Enum):
    """Types of currency"""
    CRYSTAL = auto()
    EXON = auto()
    GOLD = auto()
    TOKEN = auto()
    REPUTATION = auto()

class TransactionType(Enum):
    """Types of transactions"""
    PURCHASE = auto()
    SALE = auto()
    TRADE = auto()
    REWARD = auto()
    REFUND = auto()
    ADJUSTMENT = auto()
    TRANSFER = auto()

@dataclass
class Transaction:
    """Transaction data"""
    id: str
    type: TransactionType
    source_id: int
    target_id: Optional[int]
    currency: CurrencyType
    amount: float
    timestamp: datetime
    reference: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Wallet:
    """Wallet data"""
    user_id: int
    balances: Dict[CurrencyType, float]
    locked_balances: Dict[CurrencyType, float]
    created_at: datetime
    last_updated: datetime

class EconomySystem:
    """System for economy management"""
    def __init__(self):
        self.wallets: Dict[int, Wallet] = {}
        self.transactions: List[Transaction] = []
        self.currency_limits: Dict[CurrencyType, float] = {
            CurrencyType.CRYSTAL: float('inf'),
            CurrencyType.EXON: float('inf'),
            CurrencyType.GOLD: 999999999,
            CurrencyType.TOKEN: 9999,
            CurrencyType.REPUTATION: 100000
        }

    def create_wallet(self, user_id: int) -> Wallet:
        """Create a new wallet"""
        if user_id in self.wallets:
            return self.wallets[user_id]
        
        now = datetime.utcnow()
        wallet = Wallet(
            user_id=user_id,
            balances={ct: 0.0 for ct in CurrencyType},
            locked_balances={ct: 0.0 for ct in CurrencyType},
            created_at=now,
            last_updated=now
        )
        
        self.wallets[user_id] = wallet
        return wallet

    def add_currency(
        self,
        user_id: int,
        currency: CurrencyType,
        amount: float,
        transaction_type: TransactionType,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Add currency to wallet"""
        if amount <= 0:
            return False
        
        wallet = self.wallets.get(user_id)
        if not wallet:
            return False
        
        new_balance = wallet.balances[currency] + amount
        if new_balance > self.currency_limits[currency]:
            return False
        
        # Record transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            type=transaction_type,
            source_id=0,  # System
            target_id=user_id,
            currency=currency,
            amount=amount,
            timestamp=datetime.utcnow(),
            reference=reference,
            metadata=metadata
        )
        
        self.transactions.append(transaction)
        
        # Update wallet
        wallet.balances[currency] = new_balance
        wallet.last_updated = datetime.utcnow()
        
        return True

    def remove_currency(
        self,
        user_id: int,
        currency: CurrencyType,
        amount: float,
        transaction_type: TransactionType,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Remove currency from wallet"""
        if amount <= 0:
            return False
        
        wallet = self.wallets.get(user_id)
        if not wallet:
            return False
        
        if wallet.balances[currency] < amount:
            return False
        
        # Record transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            type=transaction_type,
            source_id=user_id,
            target_id=0,  # System
            currency=currency,
            amount=amount,
            timestamp=datetime.utcnow(),
            reference=reference,
            metadata=metadata
        )
        
        self.transactions.append(transaction)
        
        # Update wallet
        wallet.balances[currency] -= amount
        wallet.last_updated = datetime.utcnow()
        
        return True

    def transfer_currency(
        self,
        source_id: int,
        target_id: int,
        currency: CurrencyType,
        amount: float,
        reference: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """Transfer currency between wallets"""
        if amount <= 0:
            return False
        
        source_wallet = self.wallets.get(source_id)
        target_wallet = self.wallets.get(target_id)
        if not source_wallet or not target_wallet:
            return False
        
        if source_wallet.balances[currency] < amount:
            return False
        
        new_target_balance = target_wallet.balances[currency] + amount
        if new_target_balance > self.currency_limits[currency]:
            return False
        
        # Record transaction
        transaction = Transaction(
            id=str(uuid.uuid4()),
            type=TransactionType.TRANSFER,
            source_id=source_id,
            target_id=target_id,
            currency=currency,
            amount=amount,
            timestamp=datetime.utcnow(),
            reference=reference,
            metadata=metadata
        )
        
        self.transactions.append(transaction)
        
        # Update wallets
        source_wallet.balances[currency] -= amount
        target_wallet.balances[currency] += amount
        now = datetime.utcnow()
        source_wallet.last_updated = now
        target_wallet.last_updated = now
        
        return True

    def lock_currency(
        self,
        user_id: int,
        currency: CurrencyType,
        amount: float
    ) -> bool:
        """Lock currency in wallet"""
        if amount <= 0:
            return False
        
        wallet = self.wallets.get(user_id)
        if not wallet:
            return False
        
        if wallet.balances[currency] < amount:
            return False
        
        wallet.balances[currency] -= amount
        wallet.locked_balances[currency] += amount
        wallet.last_updated = datetime.utcnow()
        
        return True

    def unlock_currency(
        self,
        user_id: int,
        currency: CurrencyType,
        amount: float
    ) -> bool:
        """Unlock currency in wallet"""
        if amount <= 0:
            return False
        
        wallet = self.wallets.get(user_id)
        if not wallet:
            return False
        
        if wallet.locked_balances[currency] < amount:
            return False
        
        wallet.locked_balances[currency] -= amount
        wallet.balances[currency] += amount
        wallet.last_updated = datetime.utcnow()
        
        return True

    def get_transactions(
        self,
        user_id: Optional[int] = None,
        transaction_type: Optional[TransactionType] = None,
        currency: Optional[CurrencyType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> List[Transaction]:
        """Get filtered transactions"""
        transactions = self.transactions
        
        if user_id is not None:
            transactions = [
                t for t in transactions
                if t.source_id == user_id or t.target_id == user_id
            ]
        
        if transaction_type:
            transactions = [
                t for t in transactions
                if t.type == transaction_type
            ]
        
        if currency:
            transactions = [
                t for t in transactions
                if t.currency == currency
            ]
        
        if start_time:
            transactions = [
                t for t in transactions
                if t.timestamp >= start_time
            ]
        
        if end_time:
            transactions = [
                t for t in transactions
                if t.timestamp <= end_time
            ]
        
        return sorted(transactions, key=lambda t: t.timestamp)

class TestEconomy(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.economy = EconomySystem()

    def test_wallet_creation(self):
        """Test wallet creation"""
        # Create wallet
        wallet = self.economy.create_wallet(1)
        
        # Verify wallet
        self.assertEqual(wallet.user_id, 1)
        self.assertEqual(wallet.balances[CurrencyType.GOLD], 0)
        self.assertEqual(wallet.locked_balances[CurrencyType.GOLD], 0)

    def test_currency_addition(self):
        """Test currency addition"""
        # Create wallet and add currency
        self.economy.create_wallet(1)
        success = self.economy.add_currency(
            1,
            CurrencyType.GOLD,
            100,
            TransactionType.REWARD
        )
        
        # Verify addition
        self.assertTrue(success)
        wallet = self.economy.wallets[1]
        self.assertEqual(wallet.balances[CurrencyType.GOLD], 100)

    def test_currency_removal(self):
        """Test currency removal"""
        # Create wallet and add currency
        self.economy.create_wallet(1)
        self.economy.add_currency(
            1,
            CurrencyType.GOLD,
            100,
            TransactionType.REWARD
        )
        
        # Remove currency
        success = self.economy.remove_currency(
            1,
            CurrencyType.GOLD,
            50,
            TransactionType.PURCHASE
        )
        
        # Verify removal
        self.assertTrue(success)
        wallet = self.economy.wallets[1]
        self.assertEqual(wallet.balances[CurrencyType.GOLD], 50)

    def test_currency_transfer(self):
        """Test currency transfer"""
        # Create wallets and add currency
        self.economy.create_wallet(1)
        self.economy.create_wallet(2)
        self.economy.add_currency(
            1,
            CurrencyType.GOLD,
            100,
            TransactionType.REWARD
        )
        
        # Transfer currency
        success = self.economy.transfer_currency(
            1,
            2,
            CurrencyType.GOLD,
            50
        )
        
        # Verify transfer
        self.assertTrue(success)
        wallet1 = self.economy.wallets[1]
        wallet2 = self.economy.wallets[2]
        self.assertEqual(wallet1.balances[CurrencyType.GOLD], 50)
        self.assertEqual(wallet2.balances[CurrencyType.GOLD], 50)

    def test_currency_locking(self):
        """Test currency locking"""
        # Create wallet and add currency
        self.economy.create_wallet(1)
        self.economy.add_currency(
            1,
            CurrencyType.GOLD,
            100,
            TransactionType.REWARD
        )
        
        # Lock currency
        success = self.economy.lock_currency(
            1,
            CurrencyType.GOLD,
            50
        )
        
        # Verify lock
        self.assertTrue(success)
        wallet = self.economy.wallets[1]
        self.assertEqual(wallet.balances[CurrencyType.GOLD], 50)
        self.assertEqual(wallet.locked_balances[CurrencyType.GOLD], 50)

    def test_currency_unlocking(self):
        """Test currency unlocking"""
        # Create wallet and lock currency
        self.economy.create_wallet(1)
        self.economy.add_currency(
            1,
            CurrencyType.GOLD,
            100,
            TransactionType.REWARD
        )
        self.economy.lock_currency(1, CurrencyType.GOLD, 50)
        
        # Unlock currency
        success = self.economy.unlock_currency(
            1,
            CurrencyType.GOLD,
            25
        )
        
        # Verify unlock
        self.assertTrue(success)
        wallet = self.economy.wallets[1]
        self.assertEqual(wallet.balances[CurrencyType.GOLD], 75)
        self.assertEqual(wallet.locked_balances[CurrencyType.GOLD], 25)

    def test_transaction_history(self):
        """Test transaction history"""
        # Create wallet and perform transactions
        self.economy.create_wallet(1)
        self.economy.add_currency(
            1,
            CurrencyType.GOLD,
            100,
            TransactionType.REWARD
        )
        self.economy.remove_currency(
            1,
            CurrencyType.GOLD,
            50,
            TransactionType.PURCHASE
        )
        
        # Get transactions
        transactions = self.economy.get_transactions(user_id=1)
        
        # Verify transactions
        self.assertEqual(len(transactions), 2)
        self.assertEqual(transactions[0].amount, 100)
        self.assertEqual(transactions[1].amount, 50)

    def test_currency_limits(self):
        """Test currency limits"""
        # Create wallet
        self.economy.create_wallet(1)
        
        # Try to exceed limit
        success = self.economy.add_currency(
            1,
            CurrencyType.TOKEN,
            10000,  # Above limit
            TransactionType.REWARD
        )
        
        # Verify limit enforcement
        self.assertFalse(success)
        wallet = self.economy.wallets[1]
        self.assertEqual(wallet.balances[CurrencyType.TOKEN], 0)

    def test_invalid_operations(self):
        """Test invalid operations"""
        # Create wallet
        self.economy.create_wallet(1)
        
        # Test negative amount
        success = self.economy.add_currency(
            1,
            CurrencyType.GOLD,
            -100,
            TransactionType.REWARD
        )
        self.assertFalse(success)
        
        # Test insufficient balance
        success = self.economy.remove_currency(
            1,
            CurrencyType.GOLD,
            100,
            TransactionType.PURCHASE
        )
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
