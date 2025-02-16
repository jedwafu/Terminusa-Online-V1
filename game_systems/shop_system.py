from typing import Dict, List, Optional
from datetime import datetime
import logging
from .currency_system import CurrencySystem

logger = logging.getLogger(__name__)

class ShopItem:
    def __init__(self, id: str, name: str, description: str, price: float,
                 currency: str, stock: int = -1, level_req: int = 1,
                 item_type: str = 'consumable'):
        self.id = id
        self.name = name
        self.description = description
        self.price = price
        self.currency = currency
        self.stock = stock  # -1 for unlimited
        self.level_req = level_req
        self.item_type = item_type

class ShopSystem:
    def __init__(self, currency_system: CurrencySystem):
        self.logger = logger
        self.logger.info("Initializing Shop System")
        self.currency_system = currency_system
        self.items: Dict[str, ShopItem] = self._initialize_shop_items()
        self.purchase_history: List[Dict] = []

    def _initialize_shop_items(self) -> Dict[str, ShopItem]:
        """Initialize default shop items"""
        return {
            'health_potion': ShopItem(
                id='health_potion',
                name='Health Potion',
                description='Restores 100 HP',
                price=100,
                currency='CRYSTAL',
                stock=-1,
                level_req=1,
                item_type='consumable'
            ),
            'mana_potion': ShopItem(
                id='mana_potion',
                name='Mana Potion',
                description='Restores 100 MP',
                price=100,
                currency='CRYSTAL',
                stock=-1,
                level_req=1,
                item_type='consumable'
            ),
            'repair_kit': ShopItem(
                id='repair_kit',
                name='Repair Kit',
                description='Repairs equipment durability',
                price=500,
                currency='CRYSTAL',
                stock=-1,
                level_req=10,
                item_type='consumable'
            ),
            'inventory_expansion': ShopItem(
                id='inventory_expansion',
                name='Inventory Expansion',
                description='Adds 10 inventory slots',
                price=1000,
                currency='EXON',
                stock=1,
                level_req=20,
                item_type='upgrade'
            )
        }

    def get_available_items(self, user_level: int) -> List[Dict]:
        """Get list of items available for purchase"""
        try:
            available_items = []
            for item in self.items.values():
                if item.level_req <= user_level and (item.stock == -1 or item.stock > 0):
                    available_items.append({
                        'id': item.id,
                        'name': item.name,
                        'description': item.description,
                        'price': item.price,
                        'currency': item.currency,
                        'level_req': item.level_req,
                        'item_type': item.item_type,
                        'in_stock': item.stock == -1 or item.stock > 0
                    })
            return available_items
        except Exception as e:
            self.logger.error(f"Error getting available items: {str(e)}", exc_info=True)
            return []

    def purchase_item(self, user, item_id: str, quantity: int = 1) -> Dict:
        """Process item purchase"""
        try:
            # Validate item exists
            item = self.items.get(item_id)
            if not item:
                return {'status': 'error', 'message': 'Item not found'}

            # Check level requirement
            if user.level < item.level_req:
                return {
                    'status': 'error',
                    'message': f'Level {item.level_req} required'
                }

            # Check stock
            if item.stock != -1:
                if item.stock < quantity:
                    return {'status': 'error', 'message': 'Insufficient stock'}

            # Calculate total price
            total_price = item.price * quantity

            # Validate currency and amount
            valid, message = self.currency_system.validate_amount(
                item.currency,
                total_price
            )
            if not valid:
                return {'status': 'error', 'message': message}

            # Check if user can afford
            if not self._can_afford(user, item.currency, total_price):
                return {
                    'status': 'error',
                    'message': f'Insufficient funds ({total_price} {item.currency})'
                }

            # Process transaction
            transaction_result = self._process_transaction(
                user,
                item,
                quantity,
                total_price
            )
            if transaction_result['status'] != 'success':
                return transaction_result

            # Update stock
            if item.stock != -1:
                item.stock -= quantity

            # Record purchase
            self.purchase_history.append({
                'user_id': user.id,
                'item_id': item_id,
                'quantity': quantity,
                'price': total_price,
                'currency': item.currency,
                'timestamp': datetime.utcnow()
            })

            return {
                'status': 'success',
                'transaction_id': transaction_result['transaction_id'],
                'message': 'Purchase successful'
            }

        except Exception as e:
            self.logger.error(f"Error processing purchase: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def get_purchase_history(self, user_id: int,
                           limit: int = 10) -> List[Dict]:
        """Get user's purchase history"""
        try:
            user_history = [
                purchase for purchase in self.purchase_history
                if purchase['user_id'] == user_id
            ]
            return sorted(
                user_history,
                key=lambda x: x['timestamp'],
                reverse=True
            )[:limit]
        except Exception as e:
            self.logger.error(f"Error getting purchase history: {str(e)}", exc_info=True)
            return []

    def add_shop_item(self, item: ShopItem) -> Dict:
        """Add new item to shop"""
        try:
            if item.id in self.items:
                return {'status': 'error', 'message': 'Item ID already exists'}

            self.items[item.id] = item
            return {
                'status': 'success',
                'message': 'Item added successfully'
            }
        except Exception as e:
            self.logger.error(f"Error adding shop item: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def update_item_stock(self, item_id: str, stock: int) -> Dict:
        """Update item stock"""
        try:
            item = self.items.get(item_id)
            if not item:
                return {'status': 'error', 'message': 'Item not found'}

            item.stock = stock
            return {
                'status': 'success',
                'message': 'Stock updated successfully'
            }
        except Exception as e:
            self.logger.error(f"Error updating stock: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Internal error'}

    def _can_afford(self, user, currency: str, amount: float) -> bool:
        """Check if user can afford purchase"""
        # TODO: Implement actual balance check
        return True

    def _process_transaction(self, user, item: ShopItem,
                           quantity: int, total_price: float) -> Dict:
        """Process the shop transaction"""
        try:
            # TODO: Implement actual transaction processing
            return {
                'status': 'success',
                'transaction_id': f"tx_{datetime.utcnow().timestamp()}"
            }
        except Exception as e:
            self.logger.error(f"Error processing transaction: {str(e)}", exc_info=True)
            return {'status': 'error', 'message': 'Transaction failed'}
