"""Initialize all models

Revision ID: 017_initialize_all_models
Revises: 016_initialize_game_models
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '017_initialize_all_models'
down_revision = '016_initialize_game_models'
branch_labels = None
depends_on = None

def upgrade():
    # Create enums first
    op.execute("CREATE TYPE currency_type AS ENUM ('SOLANA', 'EXONS', 'CRYSTALS')")
    op.execute("CREATE TYPE transaction_type AS ENUM ('EARN', 'SPEND', 'TRANSFER', 'SWAP', 'REFUND', 'TAX', 'GUILD', 'SYSTEM', 'DEATH', 'QUEST', 'GATE', 'GAMBLING', 'LOYALTY')")
    op.execute("CREATE TYPE item_type AS ENUM ('WEAPON', 'ARMOR', 'ACCESSORY', 'CONSUMABLE', 'MATERIAL', 'LICENSE', 'SPECIAL')")
    op.execute("CREATE TYPE item_rarity AS ENUM ('BASIC', 'INTERMEDIATE', 'EXCELLENT', 'LEGENDARY', 'IMMORTAL')")
    op.execute("CREATE TYPE equipment_type AS ENUM ('SWORD', 'STAFF', 'DAGGER', 'BOW', 'WAND', 'HELMET', 'CHEST', 'GLOVES', 'BOOTS', 'SHIELD', 'RING', 'NECKLACE', 'EARRING', 'BELT')")
    op.execute("CREATE TYPE equipment_slot AS ENUM ('MAIN_HAND', 'OFF_HAND', 'HEAD', 'CHEST', 'HANDS', 'FEET', 'RING_1', 'RING_2', 'NECKLACE', 'EARRING_1', 'EARRING_2', 'BELT')")
    op.execute("CREATE TYPE hunter_class AS ENUM ('NOVICE', 'FIGHTER', 'RANGER', 'MAGE', 'TANK', 'HEALER', 'ASSASSIN', 'SUMMONER')")
    op.execute("CREATE TYPE base_job AS ENUM ('NONE', 'WARRIOR', 'ARCHER', 'WIZARD', 'KNIGHT', 'PRIEST', 'ROGUE', 'TAMER')")
    op.execute("CREATE TYPE health_status AS ENUM ('HEALTHY', 'INJURED', 'CRITICAL', 'EXHAUSTED', 'RECOVERING')")
    op.execute("CREATE TYPE gate_grade AS ENUM ('F', 'E', 'D', 'C', 'B', 'A', 'S', 'SS', 'SSS')")
    op.execute("CREATE TYPE magic_beast_type AS ENUM ('NORMAL', 'ELITE', 'BOSS', 'RAID', 'EVENT')")
    op.execute("CREATE TYPE guild_rank AS ENUM ('MASTER', 'VICE_MASTER', 'ELDER', 'VETERAN', 'MEMBER', 'RECRUIT')")
    op.execute("CREATE TYPE party_role AS ENUM ('LEADER', 'MEMBER')")
    op.execute("CREATE TYPE friend_status AS ENUM ('PENDING', 'ACCEPTED', 'BLOCKED')")
    op.execute("CREATE TYPE achievement_type AS ENUM ('COMBAT', 'EXPLORATION', 'SOCIAL', 'COLLECTION', 'PROGRESSION', 'SPECIAL', 'EVENT')")
    op.execute("CREATE TYPE quest_type AS ENUM ('MAIN', 'SIDE', 'DAILY', 'WEEKLY', 'GUILD', 'EVENT', 'JOB', 'CLASS')")
    op.execute("CREATE TYPE quest_status AS ENUM ('AVAILABLE', 'ACCEPTED', 'IN_PROGRESS', 'COMPLETED', 'FAILED', 'EXPIRED')")
    op.execute("CREATE TYPE milestone_type AS ENUM ('LEVEL', 'GATE', 'QUEST', 'ACHIEVEMENT', 'COLLECTION', 'SOCIAL')")
    op.execute("CREATE TYPE ai_metric AS ENUM ('ACCURACY', 'PRECISION', 'RECALL', 'F1_SCORE', 'AUC_ROC')")
    op.execute("CREATE TYPE activity_type AS ENUM ('GATE_HUNTING', 'GAMBLING', 'TRADING', 'CRAFTING', 'SOCIAL', 'QUESTING', 'COMBAT')")

    # Create tables
    op.create_table(
        'currencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('SOLANA', 'EXONS', 'CRYSTALS', name='currency_type'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=36, scale=18), nullable=False, default=0),
        sa.Column('max_supply', sa.Numeric(precision=36, scale=18), nullable=True),
        sa.Column('is_gate_reward', sa.Boolean(), nullable=False, default=False),
        sa.Column('base_tax_rate', sa.Float(), nullable=False, default=0.13),
        sa.Column('guild_tax_rate', sa.Float(), nullable=False, default=0.02),
        sa.Column('admin_wallet', sa.String(100), nullable=True),
        sa.Column('admin_username', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Add more table creation statements for other models...

    # Create indexes
    op.create_index(op.f('ix_currencies_user_id'), 'currencies', ['user_id'], unique=False)
    op.create_index(op.f('ix_currencies_type'), 'currencies', ['type'], unique=False)

    # Add more index creation statements...

def downgrade():
    # Drop tables in reverse order
    op.drop_table('currencies')
    # Drop other tables...

    # Drop enums in reverse order
    op.execute("DROP TYPE IF EXISTS activity_type")
    op.execute("DROP TYPE IF EXISTS ai_metric")
    op.execute("DROP TYPE IF EXISTS milestone_type")
    op.execute("DROP TYPE IF EXISTS quest_status")
    op.execute("DROP TYPE IF EXISTS quest_type")
    op.execute("DROP TYPE IF EXISTS achievement_type")
    op.execute("DROP TYPE IF EXISTS friend_status")
    op.execute("DROP TYPE IF EXISTS party_role")
    op.execute("DROP TYPE IF EXISTS guild_rank")
    op.execute("DROP TYPE IF EXISTS magic_beast_type")
    op.execute("DROP TYPE IF EXISTS gate_grade")
    op.execute("DROP TYPE IF EXISTS health_status")
    op.execute("DROP TYPE IF EXISTS base_job")
    op.execute("DROP TYPE IF EXISTS hunter_class")
    op.execute("DROP TYPE IF EXISTS equipment_slot")
    op.execute("DROP TYPE IF EXISTS equipment_type")
    op.execute("DROP TYPE IF EXISTS item_rarity")
    op.execute("DROP TYPE IF EXISTS item_type")
    op.execute("DROP TYPE IF EXISTS transaction_type")
    op.execute("DROP TYPE IF EXISTS currency_type")
