from decimal import Decimal
from typing import Dict, Optional
from dataclasses import dataclass
from datetime import datetime
import json

@dataclass
class Currency:
    name: str
    symbol: str
    max_supply: Decimal
    current_supply: Decimal
    can_earn_in_gates: bool
    tax_rate: Decimal
    guild_tax_rate: Decimal

class CurrencySystem:
    def __init__(self):
        self.currencies = {
            'CRYSTAL': Currency(
                name='Crystal',
                symbol='CRYS',
                max_supply=Decimal('100000000'),
                current_supply=Decimal('0'),
                can_earn_in_gates=True,
                tax_rate=Decimal('0.13'),  # 13%
                guild_tax_rate=Decimal('0.02')  # Additional 2% for guild transactions
            ),
            'EXON': Currency(
                name='Exon',
                symbol='EXON',
                max_supply=Decimal('0'),  # No max supply for Exons as it's a token
                current_supply=Decimal('0'),
                can_earn_in_gates=False,
                tax_rate=Decimal('0.13'),  # 13%
                guild_tax_rate=Decimal('0.02')  # Additional 2% for guild transactions
            )
        }
        self.admin_wallet = "FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw"
        self.admin_username = "adminbb"

    def add_currency(self, symbol: str, name: str, max_supply: Decimal, can_earn_in_gates: bool,
                    tax_rate: Decimal, guild_tax_rate: Decimal) -> bool:
        """Add a new currency to the system"""
        if symbol in self.currencies:
            return False
        
        self.currencies[symbol] = Currency(
            name=name,
            symbol=symbol,
            max_supply=max_supply,
            current_supply=Decimal('0'),
            can_earn_in_gates=can_earn_in_gates,
            tax_rate=tax_rate,
            guild_tax_rate=guild_tax_rate
        )
        return True

    def calculate_taxes(self, amount: Decimal, currency: str, is_guild_transaction: bool = False) -> Dict[str, Decimal]:
        """Calculate taxes for a transaction"""
        if currency not in self.currencies:
            raise ValueError(f"Unknown currency: {currency}")
        
        currency_info = self.currencies[currency]
        base_tax = amount * currency_info.tax_rate
        guild_tax = amount * currency_info.guild_tax_rate if is_guild_transaction else Decimal('0')
        
        return {
            'base_tax': base_tax,
            'guild_tax': guild_tax,
            'total_tax': base_tax + guild_tax,
            'amount_after_tax': amount - (base_tax + guild_tax)
        }

    def mint(self, currency: str, amount: Decimal) -> bool:
        """Mint new currency if within max supply"""
        if currency not in self.currencies:
            return False
            
        currency_info = self.currencies[currency]
        if currency_info.max_supply > 0:  # Check if there's a max supply limit
            if currency_info.current_supply + amount > currency_info.max_supply:
                return False
                
        currency_info.current_supply += amount
        return True

    def burn(self, currency: str, amount: Decimal) -> bool:
        """Burn existing currency"""
        if currency not in self.currencies:
            return False
            
        currency_info = self.currencies[currency]
        if currency_info.current_supply < amount:
            return False
            
        currency_info.current_supply -= amount
        return True

    def get_currency_info(self, currency: str) -> Optional[Dict]:
        """Get information about a currency"""
        if currency not in self.currencies:
            return None
            
        currency_info = self.currencies[currency]
        return {
            'name': currency_info.name,
            'symbol': currency_info.symbol,
            'max_supply': str(currency_info.max_supply),
            'current_supply': str(currency_info.current_supply),
            'can_earn_in_gates': currency_info.can_earn_in_gates,
            'tax_rate': str(currency_info.tax_rate),
            'guild_tax_rate': str(currency_info.guild_tax_rate)
        }

class MarketplaceSystem:
    def __init__(self, currency_system: CurrencySystem):
        self.currency_system = currency_system
        self.listings = {}
        self.next_listing_id = 1

    def create_listing(self, seller, item_id: int, quantity: int, price: Decimal,
                      currency: str, duration_days: int) -> Dict:
        """Create a new marketplace listing"""
        if currency not in self.currency_system.currencies:
            return {'status': 'error', 'message': 'Invalid currency'}

        listing_id = self.next_listing_id
        self.next_listing_id += 1

        self.listings[listing_id] = {
            'seller_id': seller.id,
            'item_id': item_id,
            'quantity': quantity,
            'price': price,
            'currency': currency,
            'created_at': datetime.utcnow(),
            'expires_at': datetime.utcnow() + datetime.timedelta(days=duration_days),
            'status': 'active'
        }

        return {
            'status': 'success',
            'listing_id': listing_id,
            'message': 'Listing created successfully'
        }

    def purchase_listing(self, buyer, listing_id: int) -> Dict:
        """Purchase an item from the marketplace"""
        if listing_id not in self.listings:
            return {'status': 'error', 'message': 'Listing not found'}

        listing = self.listings[listing_id]
        if listing['status'] != 'active':
            return {'status': 'error', 'message': 'Listing is not active'}

        if listing['expires_at'] < datetime.utcnow():
            return {'status': 'error', 'message': 'Listing has expired'}

        # Calculate taxes
        price_with_taxes = self.currency_system.calculate_taxes(
            listing['price'],
            listing['currency']
        )

        # Process the transaction
        # This would involve checking buyer's balance and transferring currency
        # For now, we'll just mark the listing as sold
        listing['status'] = 'sold'
        listing['buyer_id'] = buyer.id
        listing['sold_at'] = datetime.utcnow()

        return {
            'status': 'success',
            'message': 'Purchase successful',
            'price_paid': str(price_with_taxes['amount_after_tax']),
            'taxes_paid': str(price_with_taxes['total_tax'])
        }

class ShopSystem:
    def __init__(self, currency_system: CurrencySystem):
        self.currency_system = currency_system
        self.shop_items = {
            'inventory_expansion': {
                'name': 'Inventory Expansion (+10 slots)',
                'price': Decimal('100'),
                'currency': 'CRYSTAL'
            },
            'rename_license': {
                'name': 'Character Rename License',
                'price': Decimal('500'),
                'currency': 'CRYSTAL'
            },
            'job_reset': {
                'name': 'Job Reset License',
                'price': Decimal('1000'),
                'currency': 'EXON'
            },
            'job_class_license': {
                'name': 'Job Class License',
                'price': Decimal('2000'),
                'currency': 'EXON'
            },
            'remote_shop_license': {
                'name': 'Remote Shop License',
                'price': Decimal('5000'),
                'currency': 'EXON'
            }
        }
        
        self.antidotes = {
            'chill_antidote': {
                'name': 'Chill Antidote',
                'price': Decimal('20'),
                'currency': 'CRYSTAL',
                'cures': ['burn']
            },
            'cleansing_antidote': {
                'name': 'Cleansing Antidote',
                'price': Decimal('20'),
                'currency': 'CRYSTAL',
                'cures': ['poison']
            },
            'flame_antidote': {
                'name': 'Flame Antidote',
                'price': Decimal('20'),
                'currency': 'CRYSTAL',
                'cures': ['frozen']
            },
            'shilajit_antidote': {
                'name': 'Shilajit Antidote',
                'price': Decimal('50'),
                'currency': 'CRYSTAL',
                'cures': ['feared', 'confused']
            }
        }

    def purchase_item(self, user, item_key: str, quantity: int = 1) -> Dict:
        """Purchase an item from the shop"""
        if item_key not in self.shop_items and item_key not in self.antidotes:
            return {'status': 'error', 'message': 'Item not found'}

        item = self.shop_items.get(item_key) or self.antidotes.get(item_key)
        total_price = item['price'] * Decimal(str(quantity))

        # Calculate taxes
        price_with_taxes = self.currency_system.calculate_taxes(
            total_price,
            item['currency']
        )

        # Process the transaction
        # This would involve checking user's balance and applying the item effect
        # For now, we'll just return the calculated price
        return {
            'status': 'success',
            'message': 'Purchase successful',
            'item_name': item['name'],
            'quantity': quantity,
            'price_paid': str(price_with_taxes['amount_after_tax']),
            'taxes_paid': str(price_with_taxes['total_tax'])
        }

class GachaSystem:
    def __init__(self, currency_system: CurrencySystem):
        self.currency_system = currency_system
        self.rates = {
            'Basic': Decimal('0.50'),      # 50%
            'Intermediate': Decimal('0.30'),# 30%
            'Excellent': Decimal('0.15'),  # 15%
            'Legendary': Decimal('0.04'),  # 4%
            'Immortal': Decimal('0.01')    # 1%
        }
        self.pull_price = Decimal('100')  # Price in EXON
        self.currency = 'EXON'

    def adjust_rates(self, user) -> Dict[str, Decimal]:
        """Adjust gacha rates based on user data"""
        # This would be enhanced with AI behavior analysis
        return self.rates

    def pull_gacha(self, user, gacha_type: str, pulls: int = 1) -> Dict:
        """Perform gacha pulls"""
        if pulls < 1:
            return {'status': 'error', 'message': 'Invalid number of pulls'}

        total_price = self.pull_price * Decimal(str(pulls))
        price_with_taxes = self.currency_system.calculate_taxes(
            total_price,
            self.currency
        )

        # Adjust rates based on user data
        adjusted_rates = self.adjust_rates(user)

        # Simulate pulls (actual implementation would use these rates)
        # For now, just return the cost calculation
        return {
            'status': 'success',
            'pulls': pulls,
            'price_paid': str(price_with_taxes['amount_after_tax']),
            'taxes_paid': str(price_with_taxes['total_tax'])
        }
