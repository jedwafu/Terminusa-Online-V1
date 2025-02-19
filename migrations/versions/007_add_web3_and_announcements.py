"""Add web3 wallet and announcements

Revision ID: 007_add_web3_and_announcements
Revises: 006_add_announcements_only
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '007_add_web3_and_announcements'
down_revision = '006_add_announcements_only'
branch_labels = None
depends_on = None

def upgrade():
    # Add web3_wallet column to users table
    op.add_column('users', sa.Column('web3_wallet', sa.String(64), nullable=True))
    op.add_column('users', sa.Column('crystals', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('users', sa.Column('exons_balance', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('users', sa.Column('hunter_class', sa.String(50), nullable=True))
    op.add_column('users', sa.Column('hunter_level', sa.Integer(), nullable=False, server_default='1'))

    # Create announcements table
    op.create_table(
        'announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('updated_at', sa.DateTime(), nullable=True, onupdate=datetime.utcnow),
        sa.Column('author_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('priority', sa.Integer(), nullable=False, default=0),
        sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create inventory_items table
    op.create_table(
        'inventory_items',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('item_type', sa.String(50), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('rarity', sa.String(20), nullable=True),
        sa.Column('level_requirement', sa.Integer(), nullable=False, default=1),
        sa.Column('is_tradeable', sa.Boolean(), nullable=False, default=True),
        sa.Column('market_price', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create market_listings table
    op.create_table(
        'market_listings',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('price', sa.Float(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False, default=1),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create transactions table
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('seller_id', sa.Integer(), nullable=False),
        sa.Column('buyer_id', sa.Integer(), nullable=False),
        sa.Column('item_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('price_per_unit', sa.Float(), nullable=False),
        sa.Column('total_price', sa.Float(), nullable=False),
        sa.Column('transaction_hash', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, default=datetime.utcnow),
        sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('idx_users_web3_wallet', 'users', ['web3_wallet'])
    op.create_index('idx_announcements_created_at', 'announcements', ['created_at'])
    op.create_index('idx_announcements_priority', 'announcements', ['priority'])
    op.create_index('idx_inventory_user_id', 'inventory_items', ['user_id'])
    op.create_index('idx_market_seller_id', 'market_listings', ['seller_id'])
    op.create_index('idx_market_created_at', 'market_listings', ['created_at'])
    op.create_index('idx_transactions_created_at', 'transactions', ['created_at'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_transactions_created_at')
    op.drop_index('idx_market_created_at')
    op.drop_index('idx_market_seller_id')
    op.drop_index('idx_inventory_user_id')
    op.drop_index('idx_announcements_priority')
    op.drop_index('idx_announcements_created_at')
    op.drop_index('idx_users_web3_wallet')

    # Drop tables
    op.drop_table('transactions')
    op.drop_table('market_listings')
    op.drop_table('inventory_items')
    op.drop_table('announcements')

    # Drop columns from users table
    op.drop_column('users', 'hunter_level')
    op.drop_column('users', 'hunter_class')
    op.drop_column('users', 'exons_balance')
    op.drop_column('users', 'crystals')
    op.drop_column('users', 'web3_wallet')
