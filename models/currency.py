from database import db
from datetime import datetime
from sqlalchemy.orm import relationship
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Enum, Numeric
import enum

class CurrencyType(enum.Enum):
    SOLANA = "Solana"  # Web3 currency
    EXONS = "Exons"    # Primary in-game currency
    CRYSTALS = "Crystals"  # Secondary in-game currency

class TransactionType(enum.Enum):
    EARN = "Earn"           # Earning from activities
    SPEND = "Spend"         # Spending on items/services
    TRANSFER = "Transfer"   # Transfer between players
    SWAP = "Swap"          # Currency swapping
    REFUND = "Refund"      # Refunds
    TAX = "Tax"            # Tax collection
    GUILD = "Guild"        # Guild-related transactions
    SYSTEM = "System"      # System operations
    DEATH = "Death"        # Currency lost on death
    QUEST = "Quest"        # Quest rewards
    GATE = "Gate"         # Gate rewards
    GAMBLING = "Gambling"  # Gambling transactions
    LOYALTY = "Loyalty"    # Loyalty rewards

class Currency(db.Model):
    __tablename__ = 'currencies'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Enum(CurrencyType), nullable=False)
    amount = Column(Numeric(precision=36, scale=18), default=0.0)  # High precision for blockchain currencies
    max_supply = Column(Numeric(precision=36, scale=18))  # Maximum supply limit
    is_gate_reward = Column(Boolean, default=False)  # Whether currency can be earned in gates
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Tax configuration
    base_tax_rate = Column(Float, default=0.13)  # 13% base tax
    guild_tax_rate = Column(Float, default=0.02)  # 2% additional guild tax
    admin_wallet = Column(String(100))  # Admin wallet for tax collection
    admin_username = Column(String(100))  # Admin username for tax collection

    # Relationships
    user = relationship('User', back_populates='currencies')
    transactions = relationship('Transaction', back_populates='currency')
    swaps = relationship('TokenSwap', back_populates='currency')

    def __repr__(self):
        return f'<Currency {self.type.value} ({self.amount})>'

    def calculate_tax(self, amount, include_guild_tax=False):
        """Calculate tax for a given amount"""
        base_tax = amount * self.base_tax_rate
        guild_tax = amount * self.guild_tax_rate if include_guild_tax else 0
        return base_tax + guild_tax

    def can_afford(self, amount):
        """Check if user has enough currency"""
        return self.amount >= amount

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = Column(Integer, primary_key=True)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    type = Column(Enum(TransactionType), nullable=False)
    amount = Column(Numeric(precision=36, scale=18), nullable=False)
    tax_amount = Column(Numeric(precision=36, scale=18), default=0)
    guild_tax_amount = Column(Numeric(precision=36, scale=18), default=0)
    description = Column(String(500))
    reference_id = Column(String(100))  # For tracking related transactions
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    currency = relationship('Currency', back_populates='transactions')
    user = relationship('User', back_populates='transactions')

    def __repr__(self):
        return f'<Transaction {self.type.value} {self.amount} ({self.description})>'

class TokenSwap(db.Model):
    __tablename__ = 'token_swaps'

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    currency_id = Column(Integer, ForeignKey('currencies.id'), nullable=False)
    from_currency = Column(Enum(CurrencyType), nullable=False)
    to_currency = Column(Enum(CurrencyType), nullable=False)
    from_amount = Column(Numeric(precision=36, scale=18), nullable=False)
    to_amount = Column(Numeric(precision=36, scale=18), nullable=False)
    rate = Column(Float, nullable=False)
    tax_amount = Column(Numeric(precision=36, scale=18), default=0)
    status = Column(String(20), default='pending')  # pending, completed, failed
    created_at = Column(DateTime, default=datetime.utcnow)
    completed_at = Column(DateTime)

    # Relationships
    user = relationship('User', back_populates='token_swaps')
    currency = relationship('Currency', back_populates='swaps')

    def __repr__(self):
        return f'<TokenSwap {self.from_currency.value} -> {self.to_currency.value} ({self.status})>'

# Initialize default currencies
def init_currencies(admin_wallet, admin_username):
    """Initialize default currencies with their configurations"""
    default_currencies = [
        {
            'type': CurrencyType.SOLANA,
            'max_supply': None,  # No max supply for SOLANA
            'is_gate_reward': False,
            'admin_wallet': admin_wallet,
            'admin_username': admin_username
        },
        {
            'type': CurrencyType.EXONS,
            'max_supply': None,  # Configurable through contract
            'is_gate_reward': False,
            'admin_wallet': admin_wallet,
            'admin_username': admin_username
        },
        {
            'type': CurrencyType.CRYSTALS,
            'max_supply': 100_000_000,  # 100M initial supply
            'is_gate_reward': True,
            'admin_wallet': admin_wallet,
            'admin_username': admin_username
        }
    ]
    
    for currency_data in default_currencies:
        currency = Currency.query.filter_by(type=currency_data['type']).first()
        if not currency:
            currency = Currency(**currency_data)
            db.session.add(currency)
    
    db.session.commit()
