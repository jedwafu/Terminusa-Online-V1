"""
Transaction models for Terminusa Online
"""
from datetime import datetime
from models import db

class Transaction(db.Model):
    __tablename__ = 'transactions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # transfer, deposit, withdrawal
    currency = db.Column(db.String(20), nullable=False)  # solana, exons, crystals
    amount = db.Column(db.Numeric(precision=18, scale=9), nullable=False)
    net_amount = db.Column(db.Numeric(precision=18, scale=9), nullable=False)
    tax_amount = db.Column(db.Numeric(precision=18, scale=9), default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class SwapTransaction(db.Model):
    __tablename__ = 'swap_transactions'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    wallet_id = db.Column(db.Integer, db.ForeignKey('wallets.id'), nullable=False)
    from_currency = db.Column(db.String(20), nullable=False)
    to_currency = db.Column(db.String(20), nullable=False)
    amount = db.Column(db.Numeric(precision=18, scale=9), nullable=False)
    rate = db.Column(db.Numeric(precision=18, scale=9), nullable=False)
    fee = db.Column(db.Numeric(precision=18, scale=9), default=0)
    status = db.Column(db.String(20), default='pending')  # pending, completed, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

class TaxConfig(db.Model):
    __tablename__ = 'tax_configs'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    currency_type = db.Column(db.String(20), nullable=False, unique=True)
    base_tax = db.Column(db.Float, default=0.01)  # 1% base tax
    guild_tax = db.Column(db.Float, default=0.005)  # 0.5% additional tax for guild transactions
    admin_wallet = db.Column(db.String(255), nullable=False)  # Wallet to receive tax payments
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
