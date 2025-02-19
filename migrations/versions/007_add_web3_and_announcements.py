"""Add web3 wallet and announcements

Revision ID: 007_add_web3_and_announcements
Revises: 006_add_announcements_only
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '007_add_web3_and_announcements'
down_revision = '006_add_announcements_only'
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

def upgrade():
    # Add columns to users table if they don't exist
    if not has_column('users', 'web3_wallet'):
        op.add_column('users', sa.Column('web3_wallet', sa.String(64), nullable=True))
    if not has_column('users', 'crystals'):
        op.add_column('users', sa.Column('crystals', sa.Integer(), nullable=False, server_default='0'))
    if not has_column('users', 'exons_balance'):
        op.add_column('users', sa.Column('exons_balance', sa.Float(), nullable=False, server_default='0.0'))
    if not has_column('users', 'hunter_class'):
        op.add_column('users', sa.Column('hunter_class', sa.String(50), nullable=True))
    if not has_column('users', 'hunter_level'):
        op.add_column('users', sa.Column('hunter_level', sa.Integer(), nullable=False, server_default='1'))

    # Create inventory_items table if it doesn't exist
    if not has_table('inventory_items'):
        op.create_table(
            'inventory_items',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('item_type', sa.String(50), nullable=False),
            sa.Column('name', sa.String(100), nullable=False),
            sa.Column('description', sa.Text(), nullable=True),
            sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('rarity', sa.String(20), nullable=True),
            sa.Column('level_requirement', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('is_tradeable', sa.Boolean(), nullable=False, server_default='true'),
            sa.Column('market_price', sa.Float(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create market_listings table if it doesn't exist
    if not has_table('market_listings'):
        op.create_table(
            'market_listings',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('seller_id', sa.Integer(), nullable=False),
            sa.Column('item_id', sa.Integer(), nullable=False),
            sa.Column('price', sa.Float(), nullable=False),
            sa.Column('quantity', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.Column('expires_at', sa.DateTime(), nullable=True),
            sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
            sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create transactions table if it doesn't exist
    if not has_table('transactions'):
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
            sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.ForeignKeyConstraint(['seller_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['buyer_id'], ['users.id'], ),
            sa.ForeignKeyConstraint(['item_id'], ['inventory_items.id'], ),
            sa.PrimaryKeyConstraint('id')
        )

    # Create indexes if they don't exist
    conn = op.get_bind()
    insp = inspect(conn)
    
    def create_index_if_not_exists(index_name, table_name, columns):
        if index_name not in [i['name'] for i in insp.get_indexes(table_name)]:
            op.create_index(index_name, table_name, columns)

    create_index_if_not_exists('idx_users_web3_wallet', 'users', ['web3_wallet'])
    if has_table('announcements'):
        create_index_if_not_exists('idx_announcements_created_at', 'announcements', ['created_at'])
        create_index_if_not_exists('idx_announcements_priority', 'announcements', ['priority'])
    create_index_if_not_exists('idx_inventory_user_id', 'inventory_items', ['user_id'])
    create_index_if_not_exists('idx_market_seller_id', 'market_listings', ['seller_id'])
    create_index_if_not_exists('idx_market_created_at', 'market_listings', ['created_at'])
    create_index_if_not_exists('idx_transactions_created_at', 'transactions', ['created_at'])

def downgrade():
    # Drop indexes
    op.drop_index('idx_transactions_created_at')
    op.drop_index('idx_market_created_at')
    op.drop_index('idx_market_seller_id')
    op.drop_index('idx_inventory_user_id')
    if has_table('announcements'):
        op.drop_index('idx_announcements_priority')
        op.drop_index('idx_announcements_created_at')
    op.drop_index('idx_users_web3_wallet')

    # Drop tables
    if has_table('transactions'):
        op.drop_table('transactions')
    if has_table('market_listings'):
        op.drop_table('market_listings')
    if has_table('inventory_items'):
        op.drop_table('inventory_items')

    # Drop columns from users table
    for column in ['hunter_level', 'hunter_class', 'exons_balance', 'crystals', 'web3_wallet']:
        if has_column('users', column):
            op.drop_column('users', column)
