from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128))
    web3_wallet = db.Column(db.String(64))  # Store public wallet address
    role = db.Column(db.String(20), default='user')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Game-specific fields
    crystals = db.Column(db.Integer, default=0)
    exons_balance = db.Column(db.Float, default=0.0)
    hunter_class = db.Column(db.String(50))
    hunter_level = db.Column(db.Integer, default=1)
    
    # Relationships
    announcements = db.relationship('Announcement', backref='author', lazy=True)
    inventory_items = db.relationship('InventoryItem', backref='owner', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def is_admin(self):
        return self.role == 'admin'

class Announcement(db.Model):
    __tablename__ = 'announcements'
    
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    is_active = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)  # Higher number = higher priority

class InventoryItem(db.Model):
    __tablename__ = 'inventory_items'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item_type = db.Column(db.String(50), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    quantity = db.Column(db.Integer, default=1)
    rarity = db.Column(db.String(20))
    level_requirement = db.Column(db.Integer, default=1)
    is_tradeable = db.Column(db.Boolean, default=True)
    market_price = db.Column(db.Float)  # Price in Exons
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class MarketListing(db.Model):
    __tablename__ = 'market_listings'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    price = db.Column(db.Float, nullable=False)  # Price in Exons
    quantity = db.Column(db.Integer, default=1)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    is_active = db.Column(db.Boolean, default=True)
    
    seller = db.relationship('User', backref='market_listings')
    item = db.relationship('InventoryItem')

class Transaction(db.Model):
    __tablename__ = 'transactions'
    
    id = db.Column(db.Integer, primary_key=True)
    seller_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    buyer_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    item_id = db.Column(db.Integer, db.ForeignKey('inventory_items.id'))
    quantity = db.Column(db.Integer, nullable=False)
    price_per_unit = db.Column(db.Float, nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    transaction_hash = db.Column(db.String(100))  # Solana transaction hash
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    seller = db.relationship('User', foreign_keys=[seller_id], backref='sales')
    buyer = db.relationship('User', foreign_keys=[buyer_id], backref='purchases')
    item = db.relationship('InventoryItem')

def init_db(app):
    db.init_app(app)
    with app.app_context():
        db.create_all()
