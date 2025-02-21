"""
Database initialization script for Terminusa Online
"""
import os
from datetime import datetime
from decimal import Decimal

from flask import Flask
from models import db, init_models
from models.user import User
from models.player import Player, PlayerClass, JobType
from models.inventory import Inventory, ItemType, ItemRarity
from models.currency import Currency
from models.achievement import Achievement, AchievementType, AchievementTier
from models.mount_pet import Mount, Pet, MountType, PetType
from models.guild import Guild, GuildRank
from models.gate import Gate, GateType, GateRank

def create_app():
    """Create Flask application"""
    app = Flask(__name__)
    
    # Database configuration
    app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
        'DATABASE_URL',
        'postgresql://postgres:postgres@localhost:5432/terminusa'
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize database
    db.init_app(app)
    
    return app

def init_database():
    """Initialize database with required tables and initial data"""
    print("Initializing database...")
    
    # Create all tables
    db.create_all()
    
    # Initialize models (setup relationships)
    init_models()
    
    # Create initial data
    create_currencies()
    create_admin_user()
    create_initial_achievements()
    create_sample_gates()
    
    print("Database initialization complete!")

def create_currencies():
    """Create game currencies"""
    print("Creating currencies...")
    
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
        if not Currency.get_by_symbol(currency_data['symbol']):
            currency = Currency(
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
    print("Currencies created!")

def create_admin_user():
    """Create admin user"""
    print("Creating admin user...")
    
    # Check if admin exists
    admin = User.query.filter_by(username='admin').first()
    if admin:
        return
    
    # Create admin user
    admin = User(
        username='admin',
        email='admin@terminusa.online',
        password_hash=b'admin_hash'  # This should be properly hashed in production
    )
    admin.is_admin = True
    db.session.add(admin)
    db.session.flush()  # Get admin.id
    
    # Create admin player
    player = Player(
        user_id=admin.id,
        name='Admin',
        player_class=PlayerClass.WARRIOR
    )
    db.session.add(player)
    
    # Create admin inventory
    inventory = Inventory(user_id=admin.id)
    db.session.add(inventory)
    
    db.session.commit()
    print("Admin user created!")

def create_initial_achievements():
    """Create initial achievements"""
    print("Creating achievements...")
    
    achievements = [
        # Combat Achievements
        {
            'name': 'First Blood',
            'description': 'Defeat your first monster',
            'type': AchievementType.COMBAT,
            'tier': AchievementTier.BRONZE,
            'target': 1,
            'rewards': {'crystals': 100}
        },
        {
            'name': 'Monster Hunter',
            'description': 'Defeat 100 monsters',
            'type': AchievementType.COMBAT,
            'tier': AchievementTier.SILVER,
            'target': 100,
            'rewards': {'crystals': 1000}
        },
        
        # Exploration Achievements
        {
            'name': 'Gate Opener',
            'description': 'Clear your first gate',
            'type': AchievementType.EXPLORATION,
            'tier': AchievementTier.BRONZE,
            'target': 1,
            'rewards': {'crystals': 100}
        },
        {
            'name': 'Gate Master',
            'description': 'Clear 50 gates',
            'type': AchievementType.EXPLORATION,
            'tier': AchievementTier.GOLD,
            'target': 50,
            'rewards': {'crystals': 5000}
        },
        
        # Social Achievements
        {
            'name': 'First Friend',
            'description': 'Make your first friend',
            'type': AchievementType.SOCIAL,
            'tier': AchievementTier.BRONZE,
            'target': 1,
            'rewards': {'crystals': 100}
        },
        {
            'name': 'Guild Leader',
            'description': 'Create a guild',
            'type': AchievementType.SOCIAL,
            'tier': AchievementTier.SILVER,
            'target': 1,
            'rewards': {'crystals': 1000}
        }
    ]
    
    for achievement_data in achievements:
        achievement = Achievement(
            user_id=1,  # Admin user
            name=achievement_data['name'],
            description=achievement_data['description'],
            type=achievement_data['type'],
            tier=achievement_data['tier'],
            target_progress=achievement_data['target'],
            rewards=achievement_data['rewards']
        )
        db.session.add(achievement)
    
    db.session.commit()
    print("Achievements created!")

def create_sample_gates():
    """Create sample gates"""
    print("Creating sample gates...")
    
    gates = [
        {
            'name': 'Training Ground',
            'description': 'A basic gate for new hunters',
            'type': GateType.NORMAL,
            'rank': GateRank.E,
            'level_requirement': 1,
            'total_floors': 3,
            'difficulty': 0.5
        },
        {
            'name': 'Forest of Trials',
            'description': 'A challenging gate with multiple paths',
            'type': GateType.ELITE,
            'rank': GateRank.D,
            'level_requirement': 5,
            'total_floors': 5,
            'difficulty': 1.0
        },
        {
            'name': 'Dragon\'s Lair',
            'description': 'A dangerous gate with a powerful boss',
            'type': GateType.BOSS,
            'rank': GateRank.C,
            'level_requirement': 10,
            'total_floors': 4,
            'difficulty': 1.5
        }
    ]
    
    for gate_data in gates:
        gate = Gate(
            name=gate_data['name'],
            description=gate_data['description'],
            type=gate_data['type'],
            rank=gate_data['rank'],
            level_requirement=gate_data['level_requirement'],
            total_floors=gate_data['total_floors'],
            difficulty=gate_data['difficulty']
        )
        db.session.add(gate)
    
    db.session.commit()
    print("Sample gates created!")

if __name__ == '__main__':
    app = create_app()
    
    with app.app_context():
        init_database()
