from app import db
from datetime import datetime
from enum import Enum

class CurrencyType(Enum):
    SOLANA = "solana"
    EXON = "exon"
    CRYSTAL = "crystal"

class Currency(db.Model):
    """Currency configuration model"""
    __tablename__ = 'currencies'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    symbol = db.Column(db.String(10), unique=True, nullable=False)
    type = db.Column(db.Enum(CurrencyType), nullable=False)
    contract_address = db.Column(db.String(64), unique=True, nullable=True)  # For blockchain tokens
    max_supply = db.Column(db.BigInteger, nullable=True)
    current_supply = db.Column(db.BigInteger, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    can_earn_in_gates = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Tax configuration
    base_tax_rate = db.Column(db.Float, default=0.13)  # 13% base tax
    guild_tax_rate = db.Column(db.Float, default=0.02)  # 2% additional guild tax
    admin_wallet = db.Column(db.String(64), nullable=True)  # For blockchain currencies
    admin_username = db.Column(db.String(50), nullable=True)  # For in-game currencies

    def __repr__(self):
        return f"<Currency {self.symbol}>"

class Wallet(db.Model):
    """Player wallet model"""
    __tablename__ = 'wallets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    address = db.Column(db.String(64), unique=True, nullable=False)
    encrypted_privkey = db.Column(db.String(256), nullable=True)  # For blockchain wallets
    iv = db.Column(db.String(32), nullable=True)  # For encryption
    sol_balance = db.Column(db.Float, default=0.0)
    exon_balance = db.Column(db.BigInteger, default=0)
    crystal_balance = db.Column(db.BigInteger, default=20)  # Starting crystals
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_loyalty_reward = db.Column(db.DateTime, nullable=True)

    # Relationships
    user = db.relationship('User', backref=db.backref('wallet', uselist=False))
    transactions = db.relationship('Transaction', backref='wallet', lazy='dynamic')

    def __repr__(self):
        return f"<Wallet {self.address}>"

class Transaction(db.Model):
    """Transaction history model"""
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=False)
    tx_type = db.Column(db.String(20), nullable=False)  # send, receive, swap, tax, reward
    amount = db.Column(db.BigInteger, nullable=False)
    fee = db.Column(db.BigInteger, default=0)
    tx_hash = db.Column(db.String(64), unique=True, nullable=True)  # For blockchain transactions
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Optional references for different transaction types
    gate_id = db.Column(db.Integer, db.ForeignKey('gates.id'), nullable=True)
    trade_id = db.Column(db.Integer, db.ForeignKey('trades.id'), nullable=True)
    shop_transaction_id = db.Column(db.Integer, db.ForeignKey('shop_transactions.id'), nullable=True)

    def __repr__(self):
        return f"<Transaction {self.tx_hash}>"

class TokenSwap(db.Model):
    """Token swap history model"""
    __tablename__ = 'token_swaps'

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    from_currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=False)
    to_currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=False)
    from_amount = db.Column(db.BigInteger, nullable=False)
    to_amount = db.Column(db.BigInteger, nullable=False)
    rate = db.Column(db.Float, nullable=False)
    fee = db.Column(db.BigInteger, default=0)
    tx_hash = db.Column(db.String(64), unique=True, nullable=True)
    status = db.Column(db.String(20), default='pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __repr__(self):
        return f"<TokenSwap {self.tx_hash}>"

class LoyaltyReward(db.Model):
    """Loyalty reward history model"""
    __tablename__ = 'loyalty_rewards'

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    currency_id = db.Column(db.Integer, db.ForeignKey('currencies.id'), nullable=False)
    amount = db.Column(db.BigInteger, nullable=False)
    percentage = db.Column(db.Float, nullable=False)  # Percentage of blockchain held
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f"<LoyaltyReward {self.id}>"
