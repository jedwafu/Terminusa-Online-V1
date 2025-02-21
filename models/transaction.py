"""
Transaction model for Terminusa Online
"""
from typing import Dict, Optional, List
from datetime import datetime
from enum import Enum
from decimal import Decimal
from sqlalchemy.dialects.postgresql import JSONB

from models import db

class TransactionType(Enum):
    # Currency Transactions
    DEPOSIT = "deposit"
    WITHDRAW = "withdraw"
    TRANSFER = "transfer"
    SWAP = "swap"
    
    # Market Transactions
    BUY = "buy"
    SELL = "sell"
    TRADE = "trade"
    AUCTION = "auction"
    
    # Game Transactions
    QUEST_REWARD = "quest_reward"
    GATE_REWARD = "gate_reward"
    ACHIEVEMENT_REWARD = "achievement_reward"
    GUILD_REWARD = "guild_reward"
    
    # Special Transactions
    GACHA_MOUNT = "mount_gacha"
    GACHA_PET = "pet_gacha"
    CRAFT = "craft"
    ENCHANT = "enchant"

class TransactionStatus(Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Transaction Details
    type = db.Column(db.Enum(TransactionType), nullable=False)
    status = db.Column(db.Enum(TransactionStatus), nullable=False, default=TransactionStatus.PENDING)
    
    # Currency Information
    currency = db.Column(db.String(20), nullable=False)  # 'solana', 'exons', 'crystals'
    amount = db.Column(db.Numeric(precision=18, scale=9), nullable=False)
    fee = db.Column(db.Numeric(precision=18, scale=9), default=0)
    tax = db.Column(db.Numeric(precision=18, scale=9), default=0)
    
    # For Currency Swaps
    from_currency = db.Column(db.String(20), nullable=True)
    to_currency = db.Column(db.String(20), nullable=True)
    conversion_rate = db.Column(db.Numeric(precision=18, scale=9), nullable=True)
    
    # Transaction Data
    details = db.Column(JSONB, nullable=False, default={})
    metadata = db.Column(JSONB, nullable=False, default={})
    
    # Error Handling
    error_code = db.Column(db.String(50), nullable=True)
    error_message = db.Column(db.String(255), nullable=True)
    
    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    def __init__(self, user_id: int, type: TransactionType, currency: str, 
                 amount: Decimal, details: Dict = None):
        self.user_id = user_id
        self.type = type
        self.currency = currency
        self.amount = amount
        self.details = details or {}

    def complete(self, metadata: Dict = None) -> bool:
        """Complete the transaction"""
        try:
            if self.status != TransactionStatus.PENDING:
                return False
                
            self.status = TransactionStatus.COMPLETED
            self.completed_at = datetime.utcnow()
            
            if metadata:
                self.metadata.update(metadata)
                
            db.session.commit()
            return True
            
        except Exception:
            db.session.rollback()
            return False

    def fail(self, error_code: str, error_message: str) -> bool:
        """Mark transaction as failed"""
        try:
            if self.status != TransactionStatus.PENDING:
                return False
                
            self.status = TransactionStatus.FAILED
            self.error_code = error_code
            self.error_message = error_message
            
            db.session.commit()
            return True
            
        except Exception:
            db.session.rollback()
            return False

    def cancel(self, reason: str = None) -> bool:
        """Cancel the transaction"""
        try:
            if self.status != TransactionStatus.PENDING:
                return False
                
            self.status = TransactionStatus.CANCELLED
            if reason:
                self.metadata['cancel_reason'] = reason
                
            db.session.commit()
            return True
            
        except Exception:
            db.session.rollback()
            return False

    def refund(self, reason: str = None) -> bool:
        """Refund the transaction"""
        try:
            if self.status != TransactionStatus.COMPLETED:
                return False
                
            self.status = TransactionStatus.REFUNDED
            if reason:
                self.metadata['refund_reason'] = reason
                
            # Create refund transaction
            refund = Transaction(
                user_id=self.user_id,
                type=self.type,
                currency=self.currency,
                amount=self.amount,
                details={
                    'refund_for': self.id,
                    'reason': reason
                }
            )
            db.session.add(refund)
            
            db.session.commit()
            return True
            
        except Exception:
            db.session.rollback()
            return False

    def calculate_total(self) -> Decimal:
        """Calculate total amount including fees and tax"""
        return self.amount + self.fee + self.tax

    def get_conversion_amount(self) -> Optional[Decimal]:
        """Get converted amount for currency swaps"""
        if self.type != TransactionType.SWAP or not self.conversion_rate:
            return None
        return self.amount * self.conversion_rate

    def to_dict(self) -> Dict:
        """Convert transaction data to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'recipient_id': self.recipient_id,
            'type': self.type.value,
            'status': self.status.value,
            'currency': self.currency,
            'amount': str(self.amount),
            'fee': str(self.fee),
            'tax': str(self.tax),
            'total': str(self.calculate_total()),
            'conversion': {
                'from_currency': self.from_currency,
                'to_currency': self.to_currency,
                'rate': str(self.conversion_rate) if self.conversion_rate else None,
                'converted_amount': str(self.get_conversion_amount()) if self.get_conversion_amount() else None
            } if self.type == TransactionType.SWAP else None,
            'details': self.details,
            'metadata': self.metadata,
            'error': {
                'code': self.error_code,
                'message': self.error_message
            } if self.error_code else None,
            'timestamps': {
                'created': self.created_at.isoformat(),
                'updated': self.updated_at.isoformat(),
                'completed': self.completed_at.isoformat() if self.completed_at else None
            }
        }

    @classmethod
    def get_user_transactions(cls, user_id: int, 
                            transaction_type: Optional[TransactionType] = None,
                            status: Optional[TransactionStatus] = None,
                            limit: int = 100) -> List['Transaction']:
        """Get user's transactions with optional filters"""
        query = cls.query.filter_by(user_id=user_id)
        
        if transaction_type:
            query = query.filter_by(type=transaction_type)
            
        if status:
            query = query.filter_by(status=status)
            
        return query.order_by(cls.created_at.desc()).limit(limit).all()

    @classmethod
    def get_transaction_summary(cls, user_id: int, 
                              start_date: Optional[datetime] = None,
                              end_date: Optional[datetime] = None) -> Dict:
        """Get summary of user's transactions"""
        query = cls.query.filter_by(
            user_id=user_id,
            status=TransactionStatus.COMPLETED
        )
        
        if start_date:
            query = query.filter(cls.created_at >= start_date)
        if end_date:
            query = query.filter(cls.created_at <= end_date)
            
        transactions = query.all()
        
        summary = {
            'total_transactions': len(transactions),
            'by_type': {},
            'by_currency': {},
            'fees_paid': Decimal('0'),
            'tax_paid': Decimal('0')
        }
        
        for tx in transactions:
            # Count by type
            tx_type = tx.type.value
            if tx_type not in summary['by_type']:
                summary['by_type'][tx_type] = {
                    'count': 0,
                    'total_amount': Decimal('0')
                }
            summary['by_type'][tx_type]['count'] += 1
            summary['by_type'][tx_type]['total_amount'] += tx.amount
            
            # Count by currency
            if tx.currency not in summary['by_currency']:
                summary['by_currency'][tx.currency] = Decimal('0')
            summary['by_currency'][tx.currency] += tx.amount
            
            # Add fees and tax
            summary['fees_paid'] += tx.fee
            summary['tax_paid'] += tx.tax
            
        return summary
