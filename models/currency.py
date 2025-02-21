"""
Currency model for Terminusa Online
"""
from typing import Dict, Optional
from datetime import datetime
from decimal import Decimal
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class Currency(db.Model):
    __tablename__ = 'currencies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    
    # Currency Properties
    is_crypto = db.Column(db.Boolean, default=False)
    is_tradeable = db.Column(db.Boolean, default=True)
    is_mintable = db.Column(db.Boolean, default=False)
    
    # Supply Information
    total_supply = db.Column(db.Numeric(precision=36, scale=18), nullable=False)
    circulating_supply = db.Column(db.Numeric(precision=36, scale=18), nullable=False)
    max_supply = db.Column(db.Numeric(precision=36, scale=18), nullable=True)
    
    # Exchange Rates (updated periodically)
    exchange_rates = db.Column(JSONB, nullable=False, default={})
    
    # Transaction Limits
    min_transaction = db.Column(db.Numeric(precision=36, scale=18), nullable=False)
    max_transaction = db.Column(db.Numeric(precision=36, scale=18), nullable=True)
    daily_limit = db.Column(db.Numeric(precision=36, scale=18), nullable=True)
    
    # Fee Structure
    transfer_fee = db.Column(db.Numeric(precision=5, scale=2), default=0)  # Percentage
    swap_fee = db.Column(db.Numeric(precision=5, scale=2), default=0)      # Percentage
    mint_fee = db.Column(db.Numeric(precision=5, scale=2), default=0)      # Percentage
    
    # Metadata
    metadata = db.Column(JSONB, nullable=False, default={})
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_rate_update = db.Column(db.DateTime, nullable=True)

    def __init__(self, name: str, symbol: str, total_supply: Decimal, 
                 circulating_supply: Decimal, min_transaction: Decimal):
        self.name = name
        self.symbol = symbol
        self.total_supply = total_supply
        self.circulating_supply = circulating_supply
        self.min_transaction = min_transaction

    def update_exchange_rates(self, rates: Dict[str, Decimal]) -> bool:
        """Update currency exchange rates"""
        try:
            self.exchange_rates = {
                currency: str(rate)  # Convert Decimal to string for JSONB
                for currency, rate in rates.items()
            }
            self.last_rate_update = datetime.utcnow()
            db.session.commit()
            return True
        except Exception:
            db.session.rollback()
            return False

    def get_exchange_rate(self, to_currency: str) -> Optional[Decimal]:
        """Get exchange rate to another currency"""
        if to_currency in self.exchange_rates:
            return Decimal(self.exchange_rates[to_currency])
        return None

    def calculate_swap_amount(self, amount: Decimal, to_currency: str) -> Dict:
        """Calculate swap amount including fees"""
        rate = self.get_exchange_rate(to_currency)
        if not rate:
            return {
                'success': False,
                'message': f'No exchange rate found for {to_currency}'
            }
            
        # Check minimum transaction
        if amount < self.min_transaction:
            return {
                'success': False,
                'message': f'Amount below minimum transaction of {self.min_transaction} {self.symbol}'
            }
            
        # Check maximum transaction
        if self.max_transaction and amount > self.max_transaction:
            return {
                'success': False,
                'message': f'Amount above maximum transaction of {self.max_transaction} {self.symbol}'
            }
            
        # Calculate fees
        swap_fee = (amount * self.swap_fee) / 100
        
        # Calculate conversion
        converted_amount = (amount - swap_fee) * rate
        
        return {
            'success': True,
            'input_amount': amount,
            'fee': swap_fee,
            'rate': rate,
            'output_amount': converted_amount,
            'output_currency': to_currency
        }

    def calculate_transfer_fee(self, amount: Decimal) -> Decimal:
        """Calculate transfer fee for amount"""
        return (amount * self.transfer_fee) / 100

    def can_mint(self, amount: Decimal) -> bool:
        """Check if amount can be minted"""
        if not self.is_mintable:
            return False
            
        if self.max_supply:
            return self.circulating_supply + amount <= self.max_supply
            
        return True

    def mint(self, amount: Decimal) -> bool:
        """Mint new currency"""
        try:
            if not self.can_mint(amount):
                return False
                
            self.circulating_supply += amount
            self.total_supply += amount
            
            db.session.commit()
            return True
            
        except Exception:
            db.session.rollback()
            return False

    def burn(self, amount: Decimal) -> bool:
        """Burn (destroy) currency"""
        try:
            if amount > self.circulating_supply:
                return False
                
            self.circulating_supply -= amount
            self.total_supply -= amount
            
            db.session.commit()
            return True
            
        except Exception:
            db.session.rollback()
            return False

    def to_dict(self) -> Dict:
        """Convert currency data to dictionary"""
        return {
            'id': self.id,
            'name': self.name,
            'symbol': self.symbol,
            'properties': {
                'is_crypto': self.is_crypto,
                'is_tradeable': self.is_tradeable,
                'is_mintable': self.is_mintable
            },
            'supply': {
                'total': str(self.total_supply),
                'circulating': str(self.circulating_supply),
                'max': str(self.max_supply) if self.max_supply else None
            },
            'exchange_rates': self.exchange_rates,
            'limits': {
                'min_transaction': str(self.min_transaction),
                'max_transaction': str(self.max_transaction) if self.max_transaction else None,
                'daily_limit': str(self.daily_limit) if self.daily_limit else None
            },
            'fees': {
                'transfer': str(self.transfer_fee),
                'swap': str(self.swap_fee),
                'mint': str(self.mint_fee)
            },
            'metadata': self.metadata,
            'timestamps': {
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat(),
                'last_rate_update': self.last_rate_update.isoformat() if self.last_rate_update else None
            }
        }

    @classmethod
    def get_by_symbol(cls, symbol: str) -> Optional['Currency']:
        """Get currency by symbol"""
        return cls.query.filter_by(symbol=symbol).first()

    @classmethod
    def initialize_game_currencies(cls):
        """Initialize default game currencies"""
        currencies = [
            {
                'name': 'Solana',
                'symbol': 'SOL',
                'is_crypto': True,
                'total_supply': Decimal('1000000000'),
                'circulating_supply': Decimal('500000000'),
                'min_transaction': Decimal('0.000000001'),
                'transfer_fee': Decimal('0.5'),
                'swap_fee': Decimal('1.0')
            },
            {
                'name': 'Exons',
                'symbol': 'EXON',
                'is_crypto': True,
                'total_supply': Decimal('1000000000000'),
                'circulating_supply': Decimal('100000000000'),
                'min_transaction': Decimal('0.000001'),
                'transfer_fee': Decimal('0.1'),
                'swap_fee': Decimal('0.5')
            },
            {
                'name': 'Crystals',
                'symbol': 'CRYS',
                'is_crypto': False,
                'total_supply': Decimal('1000000000000000'),
                'circulating_supply': Decimal('0'),
                'min_transaction': Decimal('1'),
                'transfer_fee': Decimal('0'),
                'swap_fee': Decimal('0'),
                'is_mintable': True
            }
        ]
        
        for currency_data in currencies:
            if not cls.get_by_symbol(currency_data['symbol']):
                currency = cls(
                    name=currency_data['name'],
                    symbol=currency_data['symbol'],
                    total_supply=currency_data['total_supply'],
                    circulating_supply=currency_data['circulating_supply'],
                    min_transaction=currency_data['min_transaction']
                )
                currency.is_crypto = currency_data['is_crypto']
                currency.transfer_fee = currency_data['transfer_fee']
                currency.swap_fee = currency_data['swap_fee']
                currency.is_mintable = currency_data.get('is_mintable', False)
                
                db.session.add(currency)
                
        db.session.commit()
