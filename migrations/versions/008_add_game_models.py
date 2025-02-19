"""Add game models

Revision ID: 008_add_game_models
Revises: 007_add_web3_and_announcements
Create Date: 2024-02-19 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '008_add_game_models'
down_revision = '007_add_web3_and_announcements'
branch_labels = None
depends_on = None

def has_table(table_name):
    """Check if a table exists"""
    conn = op.get_bind()
    insp = inspect(conn)
    return table_name in insp.get_table_names()

def has_column(table_name, column_name):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    insp = inspect(conn)
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns

def has_enum(enum_name):
    """Check if an enum type exists"""
    conn = op.get_bind()
    result = conn.execute(
        "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = %s)",
        (enum_name,)
    ).scalar()
    return result

def upgrade():
    # Create enums if they don't exist
    if not has_enum('hunterclass'):
        hunter_class = postgresql.ENUM('F', 'E', 'D', 'C', 'B', 'A', 'S', name='hunterclass')
        hunter_class.create(op.get_bind())

    if not has_enum('jobclass'):
        job_class = postgresql.ENUM('Fighter', 'Mage', 'Assassin', 'Archer', 'Healer', name='jobclass')
        job_class.create(op.get_bind())

    if not has_enum('gaterank'):
        gate_rank = postgresql.ENUM('E', 'D', 'C', 'B', 'A', 'S', 'Monarch', name='gaterank')
        gate_rank.create(op.get_bind())

    if not has_enum('itemrarity'):
        item_rarity = postgresql.ENUM('Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Immortal', name='itemrarity')
        item_rarity.create(op.get_bind())

    if not has_enum('mountpetrarity'):
        mount_pet_rarity = postgresql.ENUM('Basic', 'Intermediate', 'Excellent', 'Legendary', 'Immortal', name='mountpetrarity')
        mount_pet_rarity.create(op.get_bind())

    if not has_enum('healthstatus'):
        health_status = postgresql.ENUM('Normal', 'Burned', 'Poisoned', 'Frozen', 'Feared', 'Confused', 'Dismembered', 'Decapitated', 'Shadow', name='healthstatus')
        health_status.create(op.get_bind())

    # Add columns to users table if they don't exist
    if not has_column('users', 'level'):
        op.add_column('users', sa.Column('level', sa.Integer(), nullable=False, server_default='1'))
    if not has_column('users', 'exp'):
        op.add_column('users', sa.Column('exp', sa.BigInteger(), nullable=False, server_default='0'))
    if not has_column('users', 'job_class'):
        op.add_column('users', sa.Column('job_class', sa.Enum('Fighter', 'Mage', 'Assassin', 'Archer', 'Healer', name='jobclass')))
    if not has_column('users', 'job_level'):
        op.add_column('users', sa.Column('job_level', sa.Integer(), nullable=False, server_default='1'))
    if not has_column('users', 'strength'):
        op.add_column('users', sa.Column('strength', sa.Integer(), nullable=False, server_default='10'))
    if not has_column('users', 'agility'):
        op.add_column('users', sa.Column('agility', sa.Integer(), nullable=False, server_default='10'))
    if not has_column('users', 'intelligence'):
        op.add_column('users', sa.Column('intelligence', sa.Integer(), nullable=False, server_default='10'))
    if not has_column('users', 'vitality'):
        op.add_column('users', sa.Column('vitality', sa.Integer(), nullable=False, server_default='10'))
    if not has_column('users', 'luck'):
        op.add_column('users', sa.Column('luck', sa.Integer(), nullable=False, server_default='10'))
    if not has_column('users', 'hp'):
        op.add_column('users', sa.Column('hp', sa.Integer(), nullable=False, server_default='100'))
    if not has_column('users', 'max_hp'):
        op.add_column('users', sa.Column('max_hp', sa.Integer(), nullable=False, server_default='100'))
    if not has_column('users', 'mp'):
        op.add_column('users', sa.Column('mp', sa.Integer(), nullable=False, server_default='100'))
    if not has_column('users', 'max_mp'):
        op.add_column('users', sa.Column('max_mp', sa.Integer(), nullable=False, server_default='100'))

    # Create tables if they don't exist
    if not has_table('guilds'):
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

    if not has_table('parties'):
        op.create_table(
            'parties',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('leader_id', sa.Integer(), sa.ForeignKey('users.id')),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
            sa.Column('gate_id', sa.Integer()),
            sa.Column('is_in_combat', sa.Boolean(), nullable=False, server_default='false'),
            sa.PrimaryKeyConstraint('id')
        )

    if not has_table('gates'):
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

    if not has_table('magic_beasts'):
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

    if not has_table('items'):
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

    if not has_table('mounts'):
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

    if not has_table('pets'):
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

    if not has_table('skills'):
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

    if not has_table('quests'):
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

    if not has_table('guild_quests'):
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

    if not has_table('achievements'):
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

    # Add foreign key constraints if tables exist
    if has_table('users') and has_table('guilds'):
        try:
            op.create_foreign_key('fk_users_guild', 'users', 'guilds', ['guild_id'], ['id'])
        except Exception:
            pass  # Constraint might already exist

    if has_table('users') and has_table('parties'):
        try:
            op.create_foreign_key('fk_users_party', 'users', 'parties', ['party_id'], ['id'])
        except Exception:
            pass  # Constraint might already exist

    if has_table('parties') and has_table('gates'):
        try:
            op.create_foreign_key('fk_parties_gate', 'parties', 'gates', ['gate_id'], ['id'])
        except Exception:
            pass  # Constraint might already exist

def downgrade():
    # Drop foreign key constraints if they exist
    try:
        op.drop_constraint('fk_users_guild', 'users')
    except Exception:
        pass

    try:
        op.drop_constraint('fk_users_party', 'users')
    except Exception:
        pass

    try:
        op.drop_constraint('fk_parties_gate', 'parties')
    except Exception:
        pass

    # Drop tables if they exist
    tables_to_drop = [
        'transactions', 'achievements', 'guild_quests', 'quests',
        'skills', 'pets', 'mounts', 'inventory_items', 'items',
        'magic_beasts', 'gates', 'parties', 'guilds'
    ]
    for table in tables_to_drop:
        if has_table(table):
            op.drop_table(table)

    # Drop columns from users table if they exist
    columns_to_drop = [
        'level', 'exp', 'hunter_class', 'job_class', 'job_level',
        'solana_balance', 'exons_balance', 'crystals',
        'strength', 'agility', 'intelligence', 'vitality', 'luck',
        'hp', 'max_hp', 'mp', 'max_mp',
        'health_status', 'is_in_gate', 'is_in_party', 'inventory_slots',
        'guild_id', 'party_id'
    ]
    for column in columns_to_drop:
        if has_column('users', column):
            op.drop_column('users', column)

    # Drop enums if they exist
    enums_to_drop = [
        'hunterclass', 'jobclass', 'gaterank', 'itemrarity',
        'mountpetrarity', 'healthstatus'
    ]
    for enum in enums_to_drop:
        if has_enum(enum):
            op.execute(f'DROP TYPE {enum}')
