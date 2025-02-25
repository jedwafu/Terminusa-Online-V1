from models import db
from models.user import User
from models.guild import Guild
from models.party import Party
from models.mount_pet import Mount, Pet
from models.quest import Quest, QuestProgress
from models.combat import CombatResult, CombatLog
from models.marketplace import MarketplaceListing, TradeOffer
from models.ai_agent import AIAgent, PlayerBehavior, AIRecommendation
from models.economy import GamblingRecord, ReferralRecord, LoyaltyRecord

def initialize_database():
    # Clean up existing metadata
    db.metadata.clear()
    
    # Drop all tables
    db.drop_all()
    
    # Create tables in explicit dependency order
    from models.user import User
    from models.currency import Wallet
    from models.player import PlayerCharacter
    from models.announcement import Announcement
    
    # Create users table first and commit
    User.__table__.create(bind=db.engine, checkfirst=True)
    db.session.commit()
    
    # Create remaining tables
    Wallet.__table__.create(bind=db.engine, checkfirst=True)
    PlayerCharacter.__table__.create(bind=db.engine, checkfirst=True)
    Announcement.__table__.create(bind=db.engine, checkfirst=True)


    
    # Create remaining tables
    db.create_all()



    
    # Create initial admin user
    admin = User(
        username='adminbb',
        email='admin@terminusa.online',
        password_hash=b'admin123'  # Should be hashed properly
    )
    db.session.add(admin)
    
    # Create initial AI agents
    agents = [
        AIAgent(agent_type='quest', parameters={'learning_rate': 0.01}),
        AIAgent(agent_type='gacha', parameters={'learning_rate': 0.02}),
        AIAgent(agent_type='gambling', parameters={'learning_rate': 0.03}),
    ]
    db.session.add_all(agents)
    
    db.session.commit()
    print("Database initialized successfully!")
