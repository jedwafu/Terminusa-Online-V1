from datetime import datetime
from decimal import Decimal
from sqlalchemy.dialects.postgresql import NUMERIC
from database import db

class Transaction(db.Model):
    """Model for tracking currency transactions"""
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=True)
    type = db.Column(db.String(20), nullable=False)  # 'swap', 'transfer', 'reward', 'tax'
    from_currency = db.Column(db.String(20), nullable=True)  # For swaps
    to_currency = db.Column(db.String(20), nullable=True)    # For swaps
    amount = db.Column(NUMERIC(precision=18, scale=8), nullable=False)
    converted_amount = db.Column(NUMERIC(precision=18, scale=8), nullable=True)  # For swaps
    tax_amount = db.Column(NUMERIC(precision=18, scale=8), nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    # Relationships
    user = db.relationship('User', foreign_keys=[user_id], backref='transactions')
    recipient = db.relationship('User', foreign_keys=[recipient_id], backref='received_transactions')

    def __init__(self, **kwargs):
        super(Transaction, self).__init__(**kwargs)
        if isinstance(self.amount, (int, float)):
            self.amount = Decimal(str(self.amount))
        if isinstance(self.tax_amount, (int, float)):
            self.tax_amount = Decimal(str(self.tax_amount))
        if self.converted_amount and isinstance(self.converted_amount, (int, float)):
            self.converted_amount = Decimal(str(self.converted_amount))

    @property
    def net_amount(self):
        """Calculate net amount after tax"""
        return self.amount - self.tax_amount

    def to_dict(self):
        """Convert transaction to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recipient_id': self.recipient_id,
            'type': self.type,
            'from_currency': self.from_currency,
            'to_currency': self.to_currency,
            'amount': str(self.amount),
            'converted_amount': str(self.converted_amount) if self.converted_amount else None,
            'tax_amount': str(self.tax_amount),
            'net_amount': str(self.net_amount),
            'timestamp': self.timestamp.isoformat()
        }
