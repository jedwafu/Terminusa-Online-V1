import unittest
from unittest.mock import Mock, patch
import sys
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import uuid

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ListingType(Enum):
    """Types of marketplace listings"""
    SELL = auto()
    BUY = auto()
    AUCTION = auto()
    EXCHANGE = auto()

class ListingStatus(Enum):
    """Listing status states"""
    ACTIVE = auto()
    COMPLETED = auto()
    CANCELLED = auto()
    EXPIRED = auto()

@dataclass
class MarketItem:
    """Market item data"""
    item_id: str
    name: str
    description: str
    category: str
    rarity: str
    tradeable: bool = True
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class Listing:
    """Marketplace listing data"""
    id: str
    type: ListingType
    seller_id: int
    item_id: str
    quantity: int
    price: float
    currency: str
    status: ListingStatus
    created_at: datetime
    expires_at: Optional[datetime] = None
    buyer_id: Optional[int] = None
    completed_at: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None

class MarketplaceSystem:
    """System for marketplace management"""
    def __init__(self):
        self.listings: Dict[str, Listing] = {}
        self.items: Dict[str, MarketItem] = {}
        self.user_listings: Dict[int, List[str]] = {}
        self.listing_fee = 0.05  # 5% listing fee
        self.transaction_fee = 0.02  # 2% transaction fee

    def register_item(self, item: MarketItem):
        """Register a market item"""
        self.items[item.item_id] = item

    def create_listing(
        self,
        seller_id: int,
        item_id: str,
        quantity: int,
        price: float,
        currency: str,
        listing_type: ListingType = ListingType.SELL,
        duration: Optional[timedelta] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """Create a marketplace listing"""
        item = self.items.get(item_id)
        if not item or not item.tradeable:
            return None
        
        if price <= 0 or quantity <= 0:
            return None
        
        listing_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        listing = Listing(
            id=listing_id,
            type=listing_type,
            seller_id=seller_id,
            item_id=item_id,
            quantity=quantity,
            price=price,
            currency=currency,
            status=ListingStatus.ACTIVE,
            created_at=now,
            expires_at=now + duration if duration else None,
            metadata=metadata
        )
        
        self.listings[listing_id] = listing
        if seller_id not in self.user_listings:
            self.user_listings[seller_id] = []
        self.user_listings[seller_id].append(listing_id)
        
        return listing_id

    def cancel_listing(
        self,
        listing_id: str,
        user_id: int
    ) -> bool:
        """Cancel a marketplace listing"""
        listing = self.listings.get(listing_id)
        if not listing:
            return False
        
        if listing.seller_id != user_id:
            return False
        
        if listing.status != ListingStatus.ACTIVE:
            return False
        
        listing.status = ListingStatus.CANCELLED
        return True

    def purchase_listing(
        self,
        listing_id: str,
        buyer_id: int,
        quantity: Optional[int] = None
    ) -> Optional[float]:
        """Purchase from a listing"""
        listing = self.listings.get(listing_id)
        if not listing:
            return None
        
        if listing.status != ListingStatus.ACTIVE:
            return None
        
        if buyer_id == listing.seller_id:
            return None
        
        if listing.expires_at and datetime.utcnow() > listing.expires_at:
            listing.status = ListingStatus.EXPIRED
            return None
        
        quantity = quantity or listing.quantity
        if quantity > listing.quantity:
            return None
        
        # Calculate total cost
        total_cost = listing.price * quantity
        
        # Update listing
        if quantity == listing.quantity:
            listing.status = ListingStatus.COMPLETED
        else:
            listing.quantity -= quantity
        
        listing.buyer_id = buyer_id
        listing.completed_at = datetime.utcnow()
        
        return total_cost

    def get_listing(self, listing_id: str) -> Optional[Listing]:
        """Get listing by ID"""
        return self.listings.get(listing_id)

    def get_user_listings(
        self,
        user_id: int,
        active_only: bool = True
    ) -> List[Listing]:
        """Get user's listings"""
        if user_id not in self.user_listings:
            return []
        
        listings = [
            self.listings[lid]
            for lid in self.user_listings[user_id]
        ]
        
        if active_only:
            listings = [
                l for l in listings
                if l.status == ListingStatus.ACTIVE
            ]
        
        return listings

    def search_listings(
        self,
        item_id: Optional[str] = None,
        category: Optional[str] = None,
        min_price: Optional[float] = None,
        max_price: Optional[float] = None,
        listing_type: Optional[ListingType] = None
    ) -> List[Listing]:
        """Search marketplace listings"""
        listings = [
            l for l in self.listings.values()
            if l.status == ListingStatus.ACTIVE
        ]
        
        if item_id:
            listings = [l for l in listings if l.item_id == item_id]
        
        if category:
            listings = [
                l for l in listings
                if self.items[l.item_id].category == category
            ]
        
        if min_price is not None:
            listings = [l for l in listings if l.price >= min_price]
        
        if max_price is not None:
            listings = [l for l in listings if l.price <= max_price]
        
        if listing_type:
            listings = [l for l in listings if l.type == listing_type]
        
        return sorted(listings, key=lambda x: x.price)

    def calculate_fees(
        self,
        price: float,
        quantity: int
    ) -> Tuple[float, float]:
        """Calculate marketplace fees"""
        total = price * quantity
        listing_fee = total * self.listing_fee
        transaction_fee = total * self.transaction_fee
        return listing_fee, transaction_fee

class TestMarketplace(unittest.TestCase):
    def setUp(self):
        """Set up test environment"""
        self.marketplace = MarketplaceSystem()
        
        # Register test items
        self.test_item = MarketItem(
            item_id="test_item",
            name="Test Item",
            description="A test item",
            category="Test",
            rarity="Common"
        )
        
        self.marketplace.register_item(self.test_item)

    def test_listing_creation(self):
        """Test listing creation"""
        # Create listing
        listing_id = self.marketplace.create_listing(
            1,
            "test_item",
            1,
            100.0,
            "CRYSTAL"
        )
        
        # Verify listing
        self.assertIsNotNone(listing_id)
        listing = self.marketplace.get_listing(listing_id)
        self.assertEqual(listing.price, 100.0)
        self.assertEqual(listing.status, ListingStatus.ACTIVE)

    def test_listing_purchase(self):
        """Test listing purchase"""
        # Create and purchase listing
        listing_id = self.marketplace.create_listing(
            1,
            "test_item",
            1,
            100.0,
            "CRYSTAL"
        )
        
        cost = self.marketplace.purchase_listing(listing_id, 2)
        
        # Verify purchase
        self.assertEqual(cost, 100.0)
        listing = self.marketplace.get_listing(listing_id)
        self.assertEqual(listing.status, ListingStatus.COMPLETED)
        self.assertEqual(listing.buyer_id, 2)

    def test_listing_cancellation(self):
        """Test listing cancellation"""
        # Create and cancel listing
        listing_id = self.marketplace.create_listing(
            1,
            "test_item",
            1,
            100.0,
            "CRYSTAL"
        )
        
        success = self.marketplace.cancel_listing(listing_id, 1)
        
        # Verify cancellation
        self.assertTrue(success)
        listing = self.marketplace.get_listing(listing_id)
        self.assertEqual(listing.status, ListingStatus.CANCELLED)

    def test_partial_purchase(self):
        """Test partial listing purchase"""
        # Create listing with multiple items
        listing_id = self.marketplace.create_listing(
            1,
            "test_item",
            5,
            100.0,
            "CRYSTAL"
        )
        
        # Purchase part
        cost = self.marketplace.purchase_listing(listing_id, 2, 2)
        
        # Verify partial purchase
        self.assertEqual(cost, 200.0)
        listing = self.marketplace.get_listing(listing_id)
        self.assertEqual(listing.quantity, 3)
        self.assertEqual(listing.status, ListingStatus.ACTIVE)

    def test_listing_expiry(self):
        """Test listing expiry"""
        # Create listing with duration
        listing_id = self.marketplace.create_listing(
            1,
            "test_item",
            1,
            100.0,
            "CRYSTAL",
            duration=timedelta(seconds=1)
        )
        
        # Wait for expiry
        import time
        time.sleep(1.1)
        
        # Try to purchase
        cost = self.marketplace.purchase_listing(listing_id, 2)
        
        # Verify expiry
        self.assertIsNone(cost)
        listing = self.marketplace.get_listing(listing_id)
        self.assertEqual(listing.status, ListingStatus.EXPIRED)

    def test_listing_search(self):
        """Test listing search"""
        # Create multiple listings
        self.marketplace.create_listing(
            1,
            "test_item",
            1,
            100.0,
            "CRYSTAL"
        )
        self.marketplace.create_listing(
            2,
            "test_item",
            1,
            200.0,
            "CRYSTAL"
        )
        
        # Search by price range
        listings = self.marketplace.search_listings(
            min_price=150.0,
            max_price=250.0
        )
        
        # Verify search
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].price, 200.0)

    def test_fee_calculation(self):
        """Test marketplace fee calculation"""
        # Calculate fees
        listing_fee, transaction_fee = self.marketplace.calculate_fees(
            100.0,
            1
        )
        
        # Verify fees
        self.assertEqual(listing_fee, 5.0)  # 5%
        self.assertEqual(transaction_fee, 2.0)  # 2%

    def test_user_listings(self):
        """Test user listing retrieval"""
        # Create multiple listings
        self.marketplace.create_listing(
            1,
            "test_item",
            1,
            100.0,
            "CRYSTAL"
        )
        listing_id = self.marketplace.create_listing(
            1,
            "test_item",
            1,
            200.0,
            "CRYSTAL"
        )
        
        # Cancel one listing
        self.marketplace.cancel_listing(listing_id, 1)
        
        # Get active listings
        listings = self.marketplace.get_user_listings(1)
        
        # Verify active listings
        self.assertEqual(len(listings), 1)
        self.assertEqual(listings[0].price, 100.0)

    def test_invalid_purchases(self):
        """Test invalid purchase scenarios"""
        listing_id = self.marketplace.create_listing(
            1,
            "test_item",
            1,
            100.0,
            "CRYSTAL"
        )
        
        # Try to buy own listing
        cost = self.marketplace.purchase_listing(listing_id, 1)
        self.assertIsNone(cost)
        
        # Try to buy more than available
        cost = self.marketplace.purchase_listing(listing_id, 2, 2)
        self.assertIsNone(cost)
        
        # Try to buy cancelled listing
        self.marketplace.cancel_listing(listing_id, 1)
        cost = self.marketplace.purchase_listing(listing_id, 2)
        self.assertIsNone(cost)

if __name__ == '__main__':
    unittest.main()
