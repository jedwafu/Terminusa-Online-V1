"""Add game-related tables

Revision ID: 002_add_game_tables
Revises: 001_initial_schema
Create Date: 2024-01-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_add_game_tables'
down_revision = '001_initial_schema'
branch_labels = None
depends_on = None

def upgrade():
    # Create items table
    op.create_table('items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('rarity', sa.String(50), nullable=False),
        sa.Column('level_requirement', sa.Integer()),
        sa.Column('stats', postgresql.JSONB()),
        sa.Column('is_tradeable', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create inventory table
    op.create_table('inventories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('is_equipped', sa.Boolean(), default=False),
        sa.Column('acquired_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['item_id'], ['items.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create transactions table
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('amount', sa.Numeric(18, 9), nullable=False),
        sa.Column('currency', sa.String(20), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create currencies table
    op.create_table('currencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('symbol', sa.String(10), nullable=False),
        sa.Column('decimals', sa.Integer(), nullable=False),
        sa.Column('is_blockchain', sa.Boolean(), default=False),
        sa.Column('contract_address', sa.String(100)),
        sa.Column('metadata', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name'),
        sa.UniqueConstraint('symbol')
    )

    # Create mounts table
    op.create_table('mounts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rarity', sa.String(50), nullable=False),
        sa.Column('level_requirement', sa.Integer()),
        sa.Column('stats', postgresql.JSONB()),
        sa.Column('is_tradeable', sa.Boolean(), default=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create pets table
    op.create_table('pets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('rarity', sa.String(50), nullable=False),
        sa.Column('level_requirement', sa.Integer()),
        sa.Column('abilities', postgresql.JSONB()),
        sa.Column('is_tradeable', sa.Boolean(), default=True),
        sa.Column('owner_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['owner_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('pets')
    op.drop_table('mounts')
    op.drop_table('currencies')
    op.drop_table('transactions')
    op.drop_table('inventories')
    op.drop_table('items')
