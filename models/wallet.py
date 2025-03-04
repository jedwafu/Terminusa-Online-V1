"""
Wallet model for Terminusa Online
"""
from datetime import datetime
from decimal import Decimal
from sqlalchemy.orm import relationship
from models import db

class Wallet(db.Model):
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    solana_address = db.Column(db.String(44), unique=True)  # Solana addresses are 44 characters
    
    # Currency Balances
    solana_balance = db.Column(db.Numeric(precision=36, scale=18), default=0)
    exons_balance = db.Column(db.Numeric(precision=36, scale=18), default=0)
    crystals_balance = db.Column(db.Integer, default=0)  # Crystals are whole numbers
    
    # Transaction History
    transactions = relationship('Transaction', 
                              foreign_keys='Transaction.wallet_id',
                              backref='wallet', 
                              lazy='dynamic')
    swap_transactions = relationship('SwapTransaction', backref='wallet', lazy='dynamic')
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_transaction = db.Column(db.DateTime)

    def __init__(self, user_id: int, solana_address: str = None):
        self.user_id = user_id
        self.solana_address = solana_address

    def update_balance(self, currency: str, amount: Decimal, operation: str = 'add') -> bool:
        """Update wallet balance
        
        Args:
            currency: Currency to update ('solana', 'exons', or 'crystals')
            amount: Amount to add or subtract
            operation: 'add' or 'subtract'
            
        Returns:
            bool: True if successful
        """
        try:
            if operation not in ['add', 'subtract']:
                return False

            if currency == 'solana':
                if operation == 'subtract' and self.solana_balance < amount:
                    return False
                self.solana_balance = self.solana_balance + amount if operation == 'add' else self.solana_balance - amount
            
            elif currency == 'exons':
                if operation == 'subtract' and self.exons_balance < amount:
                    return False
                self.exons_balance = self.exons_balance + amount if operation == 'add' else self.exons_balance - amount
            
            elif currency == 'crystals':
                amount = int(amount)  # Ensure whole number for crystals
                if operation == 'subtract' and self.crystals_balance < amount:
                    return False
                self.crystals_balance = self.crystals_balance + amount if operation == 'add' else self.crystals_balance - amount
            
            else:
                return False

            self.last_transaction = datetime.utcnow()
            db.session.commit()
            return True

        except Exception:
            db.session.rollback()
            return False

    def get_balance(self, currency: str) -> Decimal:
        """Get current balance for specified currency"""
        if currency == 'solana':
            return self.solana_balance
        elif currency == 'exons':
            return self.exons_balance
        elif currency == 'crystals':
            return Decimal(self.crystals_balance)
        return Decimal('0')

    def has_sufficient_balance(self, currency: str, amount: Decimal) -> bool:
        """Check if wallet has sufficient balance"""
        current_balance = self.get_balance(currency)
        return current_balance >= amount

    def to_dict(self) -> dict:
        """Convert wallet data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'solana_address': self.solana_address,
            'balances': {
                'solana': str(self.solana_balance),
                'exons': str(self.exons_balance),
                'crystals': self.crystals_balance
            },
            'timestamps': {
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat(),
                'last_transaction': self.last_transaction.isoformat() if self.last_transaction else None
            }
        }

class SwapTransaction(db.Model):
    __tablename__ = 'swap_transactions'

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    
    from_currency = db.Column(db.String(10), nullable=False)
    to_currency = db.Column(db.String(10), nullable=False)
    amount = db.Column(db.Numeric(precision=36, scale=18), nullable=False)
    rate = db.Column(db.Numeric(precision=36, scale=18), nullable=False)
    fee = db.Column(db.Numeric(precision=36, scale=18), nullable=False)
    
    status = db.Column(db.String(20), default='pending')  # 'pending', 'completed', 'failed'
    metadata = db.Column(db.JSON)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def to_dict(self) -> dict:
        """Convert swap transaction data to dictionary"""
        return {
            'id': self.id,
            'wallet_id': self.wallet_id,
            'from_currency': self.from_currency,
            'to_currency': self.to_currency,
            'amount': str(self.amount),
            'rate': str(self.rate),
            'fee': str(self.fee),
            'status': self.status,
            'metadata': self.metadata,
            'timestamps': {
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat()
            }
        }

class TaxConfig(db.Model):
    __tablename__ = 'tax_configs'

    id = db.Column(db.Integer, primary_key=True)
    currency_type = db.Column(db.String(10), nullable=False, unique=True)
    base_tax = db.Column(db.Numeric(precision=5, scale=2), nullable=False)  # Base tax rate (13%)
    guild_tax = db.Column(db.Numeric(precision=5, scale=2), nullable=False)  # Additional guild tax (2%)
    admin_wallet = db.Column(db.String(44), nullable=False)  # Admin wallet to receive taxes
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    @classmethod
    def initialize_tax_configs(cls):
        """Initialize default tax configurations"""
        configs = [
            {
                'currency_type': 'solana',
                'base_tax': Decimal('13.00'),
                'guild_tax': Decimal('2.00'),
                'admin_wallet': 'FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw'
            },
            {
                'currency_type': 'exons',
                'base_tax': Decimal('13.00'),
                'guild_tax': Decimal('2.00'),
                'admin_wallet': 'FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw'
            },
            {
                'currency_type': 'crystals',
                'base_tax': Decimal('13.00'),
                'guild_tax': Decimal('2.00'),
                'admin_wallet': 'FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw'
            }
        ]
        
        for config in configs:
            if not cls.query.filter_by(currency_type=config['currency_type']).first():
                tax_config = cls(
                    currency_type=config['currency_type'],
                    base_tax=config['base_tax'],
                    guild_tax=config['guild_tax'],
                    admin_wallet=config['admin_wallet']
                )
                db.session.add(tax_config)
        
        db.session.commit()
