from models import (
    db, User, Guild, Party, Mount, Pet, Quest, GuildQuest, Achievement,
    MagicBeast, InventoryItem, Item, Skill, Wallet, Transaction, 
    SwapTransaction, MarketplaceListing, GachaRoll, GamblingSession,
    Referral, LoyaltyReward, EquipmentUpgrade, TaxConfig, AIAgentData
)

def initialize_database():
    # Clean up existing metadata
    db.metadata.clear()
    
    # Drop all tables
    db.drop_all()
    
    # Create tables in explicit dependency order
    User.__table__.create(bind=db.engine, checkfirst=True)
    db.create_all()  # Create all tables after User
    Wallet.__table__.create(bind=db.engine, checkfirst=True)







    
    # Create initial admin user
    admin = User(
        username='adminbb',
        email='admin@terminusa.online',
        password_hash=b'admin123',  # Should be hashed properly
        role='admin',
        web3_wallet='FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw'
    )
    db.session.add(admin)
    
    # Create initial tax configuration
    tax_configs = [
        TaxConfig(
            currency_type='crystals',
            base_tax=0.13,
            guild_tax=0.02,
            admin_wallet='FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw',
            admin_account='adminbb'
        ),
        TaxConfig(
            currency_type='exons',
            base_tax=0.13,
            guild_tax=0.02,
            admin_wallet='FNEdD3PWMLwbNKxtaHy3W2NVfRJ7wqDNx4M9je8Xc6Mw',
            admin_account='adminbb'
        )
    ]
    db.session.add_all(tax_configs)
    
    db.session.commit()
    print("Database initialized successfully!")
