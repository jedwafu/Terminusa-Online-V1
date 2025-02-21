from typing import Dict, List, Optional
from decimal import Decimal
from datetime import datetime
from models import db, User, Item, Transaction
from game_config import (
    CRYSTAL_TAX_RATE, EXON_TAX_RATE,
    GUILD_CRYSTAL_TAX_RATE, GUILD_EXON_TAX_RATE,
    ADMIN_USERNAME
)

class MarketplaceListing:
    def __init__(self, id: int, seller_id: int, item_id: int, quantity: int,
                 price: Decimal, currency: str, created_at: datetime):
        self.id = id
        self.seller_id = seller_id
        self.item_id = item_id
        self.quantity = quantity
        self.price = price
        self.currency = currency
        self.created_at = created_at

class MarketplaceSystem:
    def __init__(self):
        self.admin_user = User.query.filter_by(username=ADMIN_USERNAME).first()
        self.listings = {}  # In-memory storage for active listings
        self.next_listing_id = 1

    def create_listing(self, seller: User, item: Item, quantity: int,
                      price: Decimal, currency: str) -> Dict:
        """Create a new marketplace listing"""
        if quantity <= 0:
            return {
                "success": False,
                "message": "Quantity must be greater than 0"
            }

        # Verify seller has the item
        inventory_item = next(
            (inv for inv in seller.inventory_items 
             if inv.item_id == item.id and inv.quantity >= quantity),
            None
        )
        if not inventory_item:
            return {
                "success": False,
                "message": "Insufficient item quantity"
            }

        # Create listing
        listing = MarketplaceListing(
            id=self.next_listing_id,
            seller_id=seller.id,
            item_id=item.id,
            quantity=quantity,
            price=price,
            currency=currency,
            created_at=datetime.utcnow()
        )
        self.listings[listing.id] = listing
        self.next_listing_id += 1

        # Remove items from seller's inventory
        inventory_item.quantity -= quantity
        if inventory_item.quantity == 0:
            db.session.delete(inventory_item)
        db.session.commit()

        return {
            "success": True,
            "message": "Listing created successfully",
            "listing_id": listing.id
        }

    def purchase_listing(self, buyer: User, listing_id: int) -> Dict:
        """Purchase an item from the marketplace"""
        listing = self.listings.get(listing_id)
        if not listing:
            return {
                "success": False,
                "message": "Listing not found"
            }

        seller = User.query.get(listing.seller_id)
        if not seller:
            return {
                "success": False,
                "message": "Seller not found"
            }

        # Check buyer's balance
        if not self._check_balance(buyer, listing.currency, listing.price):
            return {
                "success": False,
                "message": f"Insufficient {listing.currency} balance"
            }

        # Calculate tax
        tax_rate = self._get_tax_rate(listing.currency, seller)
        tax_amount = listing.price * tax_rate
        net_amount = listing.price - tax_amount

        try:
            # Process payment
            if listing.currency == "crystals":
                buyer.crystals -= int(listing.price)
                seller.crystals += int(net_amount)
                if self.admin_user:
                    self.admin_user.crystals += int(tax_amount)
            elif listing.currency == "exons":
                buyer.exons_balance -= listing.price
                seller.exons_balance += net_amount
                # Tax handled by blockchain

            # Transfer item to buyer
            item = Item.query.get(listing.item_id)
            buyer_inventory = next(
                (inv for inv in buyer.inventory_items if inv.item_id == item.id),
                None
            )
            if buyer_inventory:
                buyer_inventory.quantity += listing.quantity
            else:
                buyer_inventory = Item(
                    user_id=buyer.id,
                    item_id=item.id,
                    quantity=listing.quantity
                )
                db.session.add(buyer_inventory)

            # Record transaction
            transaction = Transaction(
                user_id=buyer.id,
                recipient_id=seller.id,
                type="market_purchase",
                currency=listing.currency,
                amount=listing.price,
                tax_amount=tax_amount
            )
            db.session.add(transaction)

            # Remove listing
            del self.listings[listing_id]

            db.session.commit()

            return {
                "success": True,
                "message": "Purchase successful",
                "tax_paid": str(tax_amount),
                "net_amount": str(net_amount)
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Transaction failed: {str(e)}"
            }

    def cancel_listing(self, seller: User, listing_id: int) -> Dict:
        """Cancel a marketplace listing"""
        listing = self.listings.get(listing_id)
        if not listing:
            return {
                "success": False,
                "message": "Listing not found"
            }

        if listing.seller_id != seller.id:
            return {
                "success": False,
                "message": "Not authorized to cancel this listing"
            }

        try:
            # Return items to seller's inventory
            item = Item.query.get(listing.item_id)
            seller_inventory = next(
                (inv for inv in seller.inventory_items if inv.item_id == item.id),
                None
            )
            if seller_inventory:
                seller_inventory.quantity += listing.quantity
            else:
                seller_inventory = Item(
                    user_id=seller.id,
                    item_id=item.id,
                    quantity=listing.quantity
                )
                db.session.add(seller_inventory)

            # Remove listing
            del self.listings[listing_id]

            db.session.commit()

            return {
                "success": True,
                "message": "Listing cancelled successfully"
            }

        except Exception as e:
            db.session.rollback()
            return {
                "success": False,
                "message": f"Failed to cancel listing: {str(e)}"
            }

    def get_listings(self, currency: Optional[str] = None,
                    item_type: Optional[str] = None,
                    min_price: Optional[Decimal] = None,
                    max_price: Optional[Decimal] = None) -> List[Dict]:
        """Get filtered marketplace listings"""
        listings = self.listings.values()

        # Apply filters
        if currency:
            listings = [l for l in listings if l.currency == currency]
        if item_type:
            listings = [l for l in listings if Item.query.get(l.item_id).type == item_type]
        if min_price is not None:
            listings = [l for l in listings if l.price >= min_price]
        if max_price is not None:
            listings = [l for l in listings if l.price <= max_price]

        # Convert to dictionary format
        return [{
            'id': l.id,
            'seller_id': l.seller_id,
            'seller_name': User.query.get(l.seller_id).username,
            'item_id': l.item_id,
            'item_name': Item.query.get(l.item_id).name,
            'quantity': l.quantity,
            'price': str(l.price),
            'currency': l.currency,
            'created_at': l.created_at.isoformat()
        } for l in listings]

    def _check_balance(self, user: User, currency: str, amount: Decimal) -> bool:
        """Check if user has sufficient balance"""
        if currency == "crystals":
            return user.crystals >= amount
        elif currency == "exons":
            return user.exons_balance >= amount
        return False

    def _get_tax_rate(self, currency: str, user: User) -> Decimal:
        """Get tax rate for marketplace transaction"""
        base_rate = {
            "crystals": CRYSTAL_TAX_RATE,
            "exons": EXON_TAX_RATE
        }.get(currency, Decimal("0"))

        # Add guild tax if applicable
        if user.guild_id:
            guild_rate = {
                "crystals": GUILD_CRYSTAL_TAX_RATE,
                "exons": GUILD_EXON_TAX_RATE
            }.get(currency, Decimal("0"))
            base_rate += guild_rate

        return base_rate
