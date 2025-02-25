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
    # Drop all tables and recreate
    db.drop_all()
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
