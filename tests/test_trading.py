import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass
from enum import Enum, auto

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from models import User, Item, Inventory, Wallet

class TradeStatus(Enum):
    """Trade status states"""
    PENDING = auto()
    ACCEPTED = auto()
    DECLINED = auto()
    CANCELLED = auto()
    COMPLETED = auto()

@dataclass
class TradeOffer:
    """Trade offer data"""
    items: List[Dict[str, int]]  # item_id, amount
    crystals: int = 0
    exons: int = 0
    locked: bool = False

@dataclass
class Trade:
    """Trade data"""
    id: int
    initiator_id: int
    target_id: int
    initiator_offer: TradeOffer
    target_offer: TradeOffer
    status: TradeStatus
    created_at: datetime
    expires_at: datetime
    completed_at: Optional[datetime] = None

class TradingSystem:
    """Manages player trading"""
    def __init__(self):
        self.trades: Dict[int, Trade] = {}
        self.next_trade_id = 1
        self.trade_timeout = timedelta(minutes=5)

    def initiate_trade(
        self,
        initiator_id: int,
        target_id: int
    ) -> Optional[Trade]:
        """Start a new trade"""
        # Check if either player is in active trade
        for trade in self.trades.values():
            if trade.status == TradeStatus.PENDING:
                if initiator_id in (trade.initiator_id, trade.target_id):
                    return None
                if target_id in (trade.initiator_id, trade.target_id):
                    return None
        
        # Create trade
        trade = Trade(
            id=self.next_trade_id,
            initiator_id=initiator_id,
            target_id=target_id,
            initiator_offer=TradeOffer(items=[]),
            target_offer=TradeOffer(items=[]),
            status=TradeStatus.PENDING,
            created_at=datetime.utcnow(),
            expires_at=datetime.utcnow() + self.trade_timeout
        )
        
        self.trades[self.next_trade_id] = trade
        self.next_trade_id += 1
        
        return trade

    def add_items(
        self,
        trade_id: int,
        user_id: int,
        items: List[Dict[str, int]],
        inventory: Inventory
    ) -> bool:
        """Add items to trade"""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != TradeStatus.PENDING:
            return False
        
        # Get correct offer
        offer = (
            trade.initiator_offer if user_id == trade.initiator_id
            else trade.target_offer if user_id == trade.target_id
            else None
        )
        
        if not offer or offer.locked:
            return False
        
        # Verify items exist in inventory
        for item in items:
            if not self._verify_item(inventory, item):
                return False
        
        offer.items.extend(items)
        return True

    def add_currency(
        self,
        trade_id: int,
        user_id: int,
        wallet: Wallet,
        crystals: int = 0,
        exons: int = 0
    ) -> bool:
        """Add currency to trade"""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != TradeStatus.PENDING:
            return False
        
        # Get correct offer
        offer = (
            trade.initiator_offer if user_id == trade.initiator_id
            else trade.target_offer if user_id == trade.target_id
            else None
        )
        
        if not offer or offer.locked:
            return False
        
        # Verify currency amounts
        if crystals > wallet.crystals or exons > wallet.exons:
            return False
        
        offer.crystals = crystals
        offer.exons = exons
        return True

    def lock_offer(self, trade_id: int, user_id: int) -> bool:
        """Lock trade offer"""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != TradeStatus.PENDING:
            return False
        
        # Get correct offer
        offer = (
            trade.initiator_offer if user_id == trade.initiator_id
            else trade.target_offer if user_id == trade.target_id
            else None
        )
        
        if not offer:
            return False
        
        offer.locked = True
        return True

    def accept_trade(
        self,
        trade_id: int,
        user_id: int,
        inventory: Inventory,
        wallet: Wallet
    ) -> bool:
        """Accept trade"""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != TradeStatus.PENDING:
            return False
        
        # Verify both offers are locked
        if not (trade.initiator_offer.locked and trade.target_offer.locked):
            return False
        
        # Verify items still exist
        initiator_items_valid = all(
            self._verify_item(inventory, item)
            for item in trade.initiator_offer.items
        )
        target_items_valid = all(
            self._verify_item(inventory, item)
            for item in trade.target_offer.items
        )
        
        if not (initiator_items_valid and target_items_valid):
            return False
        
        # Verify currency
        if (trade.initiator_offer.crystals > wallet.crystals or
            trade.initiator_offer.exons > wallet.exons or
            trade.target_offer.crystals > wallet.crystals or
            trade.target_offer.exons > wallet.exons):
            return False
        
        trade.status = TradeStatus.COMPLETED
        trade.completed_at = datetime.utcnow()
        return True

    def cancel_trade(self, trade_id: int, user_id: int) -> bool:
        """Cancel trade"""
        trade = self.trades.get(trade_id)
        if not trade or trade.status != TradeStatus.PENDING:
            return False
        
        if user_id not in (trade.initiator_id, trade.target_id):
            return False
        
        trade.status = TradeStatus.CANCELLED
        return True

    def _verify_item(self, inventory: Inventory, item: Dict[str, int]) -> bool:
        """Verify item exists in inventory"""
        # Implementation would check inventory here
        return True

class TestTrading(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.trading_system = TradingSystem()
        
        # Create test users
        self.user1_id = 1
        self.user2_id = 2
        
        # Create mock inventories and wallets
        self.inventory1 = Mock(spec=Inventory)
        self.inventory2 = Mock(spec=Inventory)
        
        self.wallet1 = Mock(spec=Wallet)
        self.wallet1.crystals = 1000
        self.wallet1.exons = 1000
        
        self.wallet2 = Mock(spec=Wallet)
        self.wallet2.crystals = 1000
        self.wallet2.exons = 1000

    def test_trade_initiation(self):
        """Test trade initiation"""
        # Start trade
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        # Verify trade
        self.assertIsNotNone(trade)
        self.assertEqual(trade.initiator_id, self.user1_id)
        self.assertEqual(trade.target_id, self.user2_id)
        self.assertEqual(trade.status, TradeStatus.PENDING)

    def test_item_trading(self):
        """Test item trading"""
        # Start trade
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        # Add items to trade
        items1 = [{'item_id': 1, 'amount': 1}]
        success = self.trading_system.add_items(
            trade.id,
            self.user1_id,
            items1,
            self.inventory1
        )
        
        self.assertTrue(success)
        self.assertEqual(len(trade.initiator_offer.items), 1)
        
        items2 = [{'item_id': 2, 'amount': 1}]
        success = self.trading_system.add_items(
            trade.id,
            self.user2_id,
            items2,
            self.inventory2
        )
        
        self.assertTrue(success)
        self.assertEqual(len(trade.target_offer.items), 1)

    def test_currency_trading(self):
        """Test currency trading"""
        # Start trade
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        # Add currency to trade
        success = self.trading_system.add_currency(
            trade.id,
            self.user1_id,
            self.wallet1,
            crystals=100
        )
        
        self.assertTrue(success)
        self.assertEqual(trade.initiator_offer.crystals, 100)
        
        success = self.trading_system.add_currency(
            trade.id,
            self.user2_id,
            self.wallet2,
            exons=50
        )
        
        self.assertTrue(success)
        self.assertEqual(trade.target_offer.exons, 50)

    def test_trade_locking(self):
        """Test trade offer locking"""
        # Start trade
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        # Lock offers
        success = self.trading_system.lock_offer(trade.id, self.user1_id)
        self.assertTrue(success)
        self.assertTrue(trade.initiator_offer.locked)
        
        success = self.trading_system.lock_offer(trade.id, self.user2_id)
        self.assertTrue(success)
        self.assertTrue(trade.target_offer.locked)

    def test_trade_completion(self):
        """Test trade completion"""
        # Start trade
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        # Add items and lock
        self.trading_system.add_items(
            trade.id,
            self.user1_id,
            [{'item_id': 1, 'amount': 1}],
            self.inventory1
        )
        self.trading_system.add_items(
            trade.id,
            self.user2_id,
            [{'item_id': 2, 'amount': 1}],
            self.inventory2
        )
        
        self.trading_system.lock_offer(trade.id, self.user1_id)
        self.trading_system.lock_offer(trade.id, self.user2_id)
        
        # Complete trade
        success = self.trading_system.accept_trade(
            trade.id,
            self.user2_id,
            self.inventory2,
            self.wallet2
        )
        
        self.assertTrue(success)
        self.assertEqual(trade.status, TradeStatus.COMPLETED)

    def test_trade_cancellation(self):
        """Test trade cancellation"""
        # Start trade
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        # Cancel trade
        success = self.trading_system.cancel_trade(trade.id, self.user1_id)
        
        self.assertTrue(success)
        self.assertEqual(trade.status, TradeStatus.CANCELLED)

    def test_trade_timeout(self):
        """Test trade timeout"""
        # Start trade with short timeout
        self.trading_system.trade_timeout = timedelta(seconds=1)
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        # Wait for timeout
        import time
        time.sleep(2)
        
        # Try to modify expired trade
        success = self.trading_system.add_items(
            trade.id,
            self.user1_id,
            [{'item_id': 1, 'amount': 1}],
            self.inventory1
        )
        
        self.assertFalse(success)

    def test_multiple_trades(self):
        """Test multiple trade handling"""
        # Start first trade
        trade1 = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        # Try to start second trade
        trade2 = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        self.assertIsNone(trade2)

    def test_invalid_trades(self):
        """Test invalid trade scenarios"""
        # Try to trade with self
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user1_id
        )
        
        self.assertIsNone(trade)
        
        # Try to add items after lock
        trade = self.trading_system.initiate_trade(
            self.user1_id,
            self.user2_id
        )
        
        self.trading_system.lock_offer(trade.id, self.user1_id)
        
        success = self.trading_system.add_items(
            trade.id,
            self.user1_id,
            [{'item_id': 1, 'amount': 1}],
            self.inventory1
        )
        
        self.assertFalse(success)

if __name__ == '__main__':
    unittest.main()
