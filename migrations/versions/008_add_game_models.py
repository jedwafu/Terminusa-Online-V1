"""Add game models

Revision ID: 008_add_game_models
Revises: 007_add_web3_and_announcements
Create Date: 2024-02-19 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '008_add_game_models'
down_revision = '007_add_web3_and_announcements'
branch_labels = None
depends_on = None

def upgrade():
    # Create enums
    hunter_class = postgresql.ENUM('F', 'E', 'D', 'C', 'B', 'A', 'S', name='hunterclass')
    job_class = postgresql.ENUM('Fighter', 'Mage', 'Assassin', 'Archer', 'Healer', name='jobclass')
    gate_rank = postgresql.ENUM('E', 'D', 'C', 'B', 'A', 'S', 'Monarch', name='gaterank')
    item_rarity = postgresql.ENUM('Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Immortal', name='itemrarity')
    mount_pet_rarity = postgresql.ENUM('Basic', 'Intermediate', 'Excellent', 'Legendary', 'Immortal', name='mountpetrarity')
    health_status = postgresql.ENUM('Normal', 'Burned', 'Poisoned', 'Frozen', 'Feared', 'Confused', 'Dismembered', 'Decapitated', 'Shadow', name='healthstatus')
    
    hunter_class.create(op.get_bind())
    job_class.create(op.get_bind())
    gate_rank.create(op.get_bind())
    item_rarity.create(op.get_bind())
    mount_pet_rarity.create(op.get_bind())
    health_status.create(op.get_bind())

    # Add columns to users table
    op.add_column('users', sa.Column('level', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('exp', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('hunter_class', sa.Enum('F', 'E', 'D', 'C', 'B', 'A', 'S', name='hunterclass'), nullable=False, server_default='F'))
    op.add_column('users', sa.Column('job_class', sa.Enum('Fighter', 'Mage', 'Assassin', 'Archer', 'Healer', name='jobclass')))
    op.add_column('users', sa.Column('job_level', sa.Integer(), nullable=False, server_default='1'))
    op.add_column('users', sa.Column('solana_balance', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('users', sa.Column('exons_balance', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('users', sa.Column('crystals', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('users', sa.Column('strength', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('users', sa.Column('agility', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('users', sa.Column('intelligence', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('users', sa.Column('vitality', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('users', sa.Column('luck', sa.Integer(), nullable=False, server_default='10'))
    op.add_column('users', sa.Column('hp', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('users', sa.Column('max_hp', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('users', sa.Column('mp', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('users', sa.Column('max_mp', sa.Integer(), nullable=False, server_default='100'))
    op.add_column('users', sa.Column('health_status', sa.Enum('Normal', 'Burned', 'Poisoned', 'Frozen', 'Feared', 'Confused', 'Dismembered', 'Decapitated', 'Shadow', name='healthstatus'), nullable=False, server_default='Normal'))
    op.add_column('users', sa.Column('is_in_gate', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('is_in_party', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('users', sa.Column('inventory_slots', sa.Integer(), nullable=False, server_default='20'))
    op.add_column('users', sa.Column('guild_id', sa.Integer()))
    op.add_column('users', sa.Column('party_id', sa.Integer()))

    # Create guilds table
    op.create_table(
        'guilds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('leader_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('exp', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('crystals', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('exons_balance', sa.Float(), nullable=False, server_default='0.0'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Create parties table
    op.create_table(
        'parties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('leader_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('gate_id', sa.Integer()),
        sa.Column('is_in_combat', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create gates table
    op.create_table(
        'gates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rank', sa.Enum('E', 'D', 'C', 'B', 'A', 'S', 'Monarch', name='gaterank'), nullable=False),
        sa.Column('min_level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('min_hunter_class', sa.Enum('F', 'E', 'D', 'C', 'B', 'A', 'S', name='hunterclass'), nullable=False, server_default='F'),
        sa.Column('crystal_reward_min', sa.Integer()),
        sa.Column('crystal_reward_max', sa.Integer()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create magic_beasts table
    op.create_table(
        'magic_beasts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('gate_id', sa.Integer(), sa.ForeignKey('gates.id')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('rank', sa.Enum('E', 'D', 'C', 'B', 'A', 'S', 'Monarch', name='gaterank')),
        sa.Column('hp', sa.Integer()),
        sa.Column('max_hp', sa.Integer()),
        sa.Column('mp', sa.Integer()),
        sa.Column('max_mp', sa.Integer()),
        sa.Column('is_monarch', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_shadow', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('shadow_owner_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create items table
    op.create_table(
        'items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('type', sa.String(50)),
        sa.Column('rarity', sa.Enum('Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Immortal', name='itemrarity')),
        sa.Column('level_requirement', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('price_crystals', sa.Integer()),
        sa.Column('price_exons', sa.Float()),
        sa.Column('is_tradeable', sa.Boolean(), nullable=False, server_default='true'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create inventory_items table
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('item_id', sa.Integer(), sa.ForeignKey('items.id')),
        sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('durability', sa.Integer(), nullable=False, server_default='100'),
        sa.Column('is_equipped', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create mounts table
    op.create_table(
        'mounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rarity', sa.Enum('Basic', 'Intermediate', 'Excellent', 'Legendary', 'Immortal', name='mountpetrarity')),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('exp', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create pets table
    op.create_table(
        'pets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rarity', sa.Enum('Basic', 'Intermediate', 'Excellent', 'Legendary', 'Immortal', name='mountpetrarity')),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('exp', sa.BigInteger(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create skills table
    op.create_table(
        'skills',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('mp_cost', sa.Integer()),
        sa.Column('cooldown', sa.Integer()),
        sa.Column('damage', sa.Integer()),
        sa.Column('heal', sa.Integer()),
        sa.Column('status_effect', sa.Enum('Normal', 'Burned', 'Poisoned', 'Frozen', 'Feared', 'Confused', 'Dismembered', 'Decapitated', 'Shadow', name='healthstatus')),
        sa.Column('is_resurrection', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('is_arise', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create quests table
    op.create_table(
        'quests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('requirements', postgresql.JSON()),
        sa.Column('rewards', postgresql.JSON()),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime()),
        sa.Column('is_job_quest', sa.Boolean(), nullable=False, server_default='false'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create guild_quests table
    op.create_table(
        'guild_quests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), sa.ForeignKey('guilds.id')),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('requirements', postgresql.JSON()),
        sa.Column('rewards', postgresql.JSON()),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('expires_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create achievements table
    op.create_table(
        'achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('requirements', postgresql.JSON()),
        sa.Column('rewards', postgresql.JSON()),
        sa.Column('is_completed', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('completed_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('from_user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('to_user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('currency_type', sa.String(20), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Float(), nullable=False),
        sa.Column('transaction_type', sa.String(50), nullable=False),
        sa.Column('transaction_hash', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id')
    )

    # Add foreign key constraints
    op.create_foreign_key('fk_users_guild', 'users', 'guilds', ['guild_id'], ['id'])
    op.create_foreign_key('fk_users_party', 'users', 'parties', ['party_id'], ['id'])
    op.create_foreign_key('fk_parties_gate', 'parties', 'gates', ['gate_id'], ['id'])

def downgrade():
    # Drop foreign key constraints
    op.drop_constraint('fk_users_guild', 'users')
    op.drop_constraint('fk_users_party', 'users')
    op.drop_constraint('fk_parties_gate', 'parties')

    # Drop tables
    op.drop_table('transactions')
    op.drop_table('achievements')
    op.drop_table('guild_quests')
    op.drop_table('quests')
    op.drop_table('skills')
    op.drop_table('pets')
    op.drop_table('mounts')
    op.drop_table('inventory_items')
    op.drop_table('items')
    op.drop_table('magic_beasts')
    op.drop_table('gates')
    op.drop_table('parties')
    op.drop_table('guilds')

    # Drop columns from users table
    columns_to_drop = [
        'level', 'exp', 'hunter_class', 'job_class', 'job_level',
        'solana_balance', 'exons_balance', 'crystals',
        'strength', 'agility', 'intelligence', 'vitality', 'luck',
        'hp', 'max_hp', 'mp', 'max_mp',
        'health_status', 'is_in_gate', 'is_in_party', 'inventory_slots',
        'guild_id', 'party_id'
    ]
    for column in columns_to_drop:
        op.drop_column('users', column)

    # Drop enums
    op.execute('DROP TYPE hunterclass')
    op.execute('DROP TYPE jobclass')
    op.execute('DROP TYPE gaterank')
    op.execute('DROP TYPE itemrarity')
    op.execute('DROP TYPE mountpetrarity')
    op.execute('DROP TYPE healthstatus')
