from datetime import datetime
from enum import Enum
from models import db

class ListingType(Enum):
    ITEM = 'Item'
    CURRENCY = 'Currency'
    SERVICE = 'Service'

class ListingStatus(Enum):
    ACTIVE = 'Active'
    SOLD = 'Sold'
    EXPIRED = 'Expired'
    CANCELLED = 'Cancelled'

class MarketplaceListing(db.Model):
    __tablename__ = 'marketplace_listings'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    listing_type = db.Column(db.Enum(ListingType), nullable=False)
    status = db.Column(db.Enum(ListingStatus), default=ListingStatus.ACTIVE)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Listing Details
    item_id = db.Column(db.Integer)  # Reference to item system
    quantity = db.Column(db.Integer, default=1)
    price_exons = db.Column(db.Numeric(precision=18, scale=9), default=0)
    price_crystals = db.Column(db.BigInteger, default=0)
    
    # Transaction Details
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    sold_at = db.Column(db.DateTime)
    
    # Relationships
    seller = db.relationship('User', foreign_keys=[seller_id])
    buyer = db.relationship('User', foreign_keys=[buyer_id])

class TradeOffer(db.Model):
    __tablename__ = 'trade_offers'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    status = db.Column(db.String(20), default='Pending')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Offer Details
    offered_items = db.Column(db.JSON, default={})
    requested_items = db.Column(db.JSON, default={})
    
    # Relationships
    sender = db.relationship('User', foreign_keys=[sender_id])
    receiver = db.relationship('User', foreign_keys=[receiver_id])
