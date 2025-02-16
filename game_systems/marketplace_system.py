from typing import Dict, List, Optional, Tuple
from datetime import datetime, timedelta
import logging
from .currency_system import CurrencySystem

logger = logging.getLogger(__name__)

class MarketplaceListing:
    def __init__(self, id: int, seller_id: int, item_id: int, quantity: int,
                 price: float, currency: str, created_at: datetime,
                 expires_at: datetime, status: str = 'active'):
        self.id = id
        self.seller_id = seller_id
        self.item_id = item_id
        self.quantity = quantity
        self.price = price
        self.currency = currency
        self.created_at = created_at
        self.expires_at = expires_at
        self.status = status

class MarketplaceSystem:
    def __init__(self, currency_system: CurrencySystem):
        self.logger = logger
        self.logger.info("Initializing Marketplace System")
        self.currency_system = currency_system
        self.listings: Dict[int, MarketplaceListing] = {}
        self.next_listing_id = 1
        self.default_duration_days = 7
        self.min_listing_fee = {
            'SOLANA': 0.01,
            'EXON': 10,
            'CRYSTAL': 100
        }

    def create_listing(self, seller, item_id: int, quantity: int,
                      price: float, currency: str,
                      duration_days: int = None) -> Dict:
        """Create a new marketplace listing"""
        try:
            # Validate currency and amount
            valid, message = self.currency_system.validate_amount(currency, price)
            if not valid:
                return {'status': 'error', 'message': message}

            # Calculate listing fee
            fee = max(self.min_listing_fee[currency],
                     self.currency_system.calculate_fee(currency, price))

            # Validate seller has enough currency for fee
            if not self._can_pay_fee(seller, currency, fee):
                return {
                    'status': 'error',
                    'message': f'Insufficient funds for listing fee ({fee} {currency})'
                }

            # Create listing
            duration = duration_days or self.default_duration_days
            listing = MarketplaceListing(
                id=self.next_listing_id,
                seller_id=seller.id,
                item_id=item_id,
                quantity=quantity,
                price=price,
                currency=currency,
                created_at=datetime.utcnow(),
                expires_at=datetime.utcnow() + timedelta(days=duration)
            )

            # Store listing
            self.listings[listing.id] = listing
            self.next_listing_id += 1

            # Deduct listing fee
            self._deduct_fee(seller, currency, fee)

            return {
                'status': 'success',
                'listing_id': listing.id,
                'fee_paid': fee,
                'message': 'Listing created successfully'
            }

        except Exception as e:
            self.logger.error(f"Error creating listing: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def purchase_listing(self, buyer, listing_id: int) -> Dict:
        """Purchase an item from a marketplace listing"""
        try:
            # Get listing
            listing = self.listings.get(listing_id)
            if not listing:
                return {'status': 'error', 'message': 'Listing not found'}

            if listing.status != 'active':
                return {'status': 'error', 'message': 'Listing is not active'}

            if listing.expires_at < datetime.utcnow():
                return {'status': 'error', 'message': 'Listing has expired'}

            # Validate buyer has enough currency
            if not self._can_afford_purchase(buyer, listing):
                return {
                    'status': 'error',
                    'message': f'Insufficient funds ({listing.price} {listing.currency})'
                }

            # Process transaction
            transaction_result = self._process_transaction(buyer, listing)
            if transaction_result['status'] != 'success':
                return transaction_result

            # Update listing status
            listing.status = 'completed'

            return {
                'status': 'success',
                'transaction_id': transaction_result['transaction_id'],
                'message': 'Purchase successful'
            }

        except Exception as e:
            self.logger.error(f"Error processing purchase: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def get_active_listings(self, currency: Optional[str] = None,
                          item_type: Optional[str] = None,
                          max_price: Optional[float] = None) -> List[Dict]:
        """Get active marketplace listings with optional filters"""
        try:
            current_time = datetime.utcnow()
            active_listings = []

            for listing in self.listings.values():
                if listing.status != 'active' or listing.expires_at < current_time:
                    continue

                if currency and listing.currency != currency:
                    continue

                if max_price and listing.price > max_price:
                    continue

                # TODO: Add item type filtering when item system is implemented

                active_listings.append({
                    'id': listing.id,
                    'seller_id': listing.seller_id,
                    'item_id': listing.item_id,
                    'quantity': listing.quantity,
                    'price': listing.price,
                    'currency': listing.currency,
                    'created_at': listing.created_at.isoformat(),
                    'expires_at': listing.expires_at.isoformat()
                })

            return active_listings

        except Exception as e:
            self.logger.error(f"Error getting listings: {str(e)}", exc_info=True)
            return []

    def cancel_listing(self, seller_id: int, listing_id: int) -> Dict:
        """Cancel an active marketplace listing"""
        try:
            listing = self.listings.get(listing_id)
            if not listing:
                return {'status': 'error', 'message': 'Listing not found'}

            if listing.seller_id != seller_id:
                return {'status': 'error', 'message': 'Not authorized to cancel listing'}

            if listing.status != 'active':
                return {'status': 'error', 'message': 'Listing is not active'}

            listing.status = 'cancelled'

            return {
                'status': 'success',
                'message': 'Listing cancelled successfully'
            }

        except Exception as e:
            self.logger.error(f"Error cancelling listing: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _can_pay_fee(self, user, currency: str, fee: float) -> bool:
        """Check if user can pay listing fee"""
        # TODO: Implement actual wallet balance check
        return True

    def _deduct_fee(self, user, currency: str, fee: float) -> None:
        """Deduct listing fee from user's wallet"""
        # TODO: Implement actual fee deduction
        pass

    def _can_afford_purchase(self, buyer, listing: MarketplaceListing) -> bool:
        """Check if buyer can afford the purchase"""
        # TODO: Implement actual balance check
        return True

    def _process_transaction(self, buyer, listing: MarketplaceListing) -> Dict:
        """Process the marketplace transaction"""
        try:
            # TODO: Implement actual transaction processing
            return {
                'status': 'success',
                'transaction_id': f"tx_{datetime.utcnow().timestamp()}"
            }
        except Exception as e:
            self.logger.error(f"Error processing transaction: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Transaction failed'}

    def cleanup_expired_listings(self) -> int:
        """Clean up expired listings and return count of cleaned listings"""
        try:
            current_time = datetime.utcnow()
            expired_count = 0

            for listing in self.listings.values():
                if listing.status == 'active' and listing.expires_at < current_time:
                    listing.status = 'expired'
                    expired_count += 1

            return expired_count

        except Exception as e:
            self.logger.error(f"Error cleaning up listings: {str(e)}", exc_info=True)
            return 0
