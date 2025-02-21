"""Update model relationships

Revision ID: 019_update_model_relationships
Revises: 018_update_user_model
Create Date: 2024-02-20 14:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '019_update_model_relationships'
down_revision = '018_update_user_model'
branch_labels = None
depends_on = None

def upgrade():
    # Create currencies table if it doesn't exist
    op.create_table(
        'currencies',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.Enum('SOLANA', 'EXONS', 'CRYSTALS', name='currencytype'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=36, scale=18), default=0.0),
        sa.Column('max_supply', sa.Numeric(precision=36, scale=18)),
        sa.Column('is_gate_reward', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.Column('base_tax_rate', sa.Float(), default=0.13),
        sa.Column('guild_tax_rate', sa.Float(), default=0.02),
        sa.Column('admin_wallet', sa.String(100)),
        sa.Column('admin_username', sa.String(100)),
        sa.PrimaryKeyConstraint('id')
    )

    # Create transactions table if it doesn't exist
    op.create_table(
        'transactions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('currency_id', sa.Integer(), sa.ForeignKey('currencies.id'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('type', sa.Enum('EARN', 'SPEND', 'TRANSFER', 'SWAP', 'REFUND', 'TAX', 'GUILD', 'SYSTEM', 'DEATH', 'QUEST', 'GATE', 'GAMBLING', 'LOYALTY', name='transactiontype'), nullable=False),
        sa.Column('amount', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=36, scale=18), default=0),
        sa.Column('guild_tax_amount', sa.Numeric(precision=36, scale=18), default=0),
        sa.Column('description', sa.String(500)),
        sa.Column('reference_id', sa.String(100)),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create token_swaps table if it doesn't exist
    op.create_table(
        'token_swaps',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('currency_id', sa.Integer(), sa.ForeignKey('currencies.id'), nullable=False),
        sa.Column('from_currency', sa.Enum('SOLANA', 'EXONS', 'CRYSTALS', name='currencytype'), nullable=False),
        sa.Column('to_currency', sa.Enum('SOLANA', 'EXONS', 'CRYSTALS', name='currencytype'), nullable=False),
        sa.Column('from_amount', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('to_amount', sa.Numeric(precision=36, scale=18), nullable=False),
        sa.Column('rate', sa.Float(), nullable=False),
        sa.Column('tax_amount', sa.Numeric(precision=36, scale=18), default=0),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index('ix_currencies_user_id', 'currencies', ['user_id'])
    op.create_index('ix_transactions_user_id', 'transactions', ['user_id'])
    op.create_index('ix_transactions_currency_id', 'transactions', ['currency_id'])
    op.create_index('ix_token_swaps_user_id', 'token_swaps', ['user_id'])
    op.create_index('ix_token_swaps_currency_id', 'token_swaps', ['currency_id'])

def downgrade():
    # Drop indexes
    op.drop_index('ix_token_swaps_currency_id')
    op.drop_index('ix_token_swaps_user_id')
    op.drop_index('ix_transactions_currency_id')
    op.drop_index('ix_transactions_user_id')
    op.drop_index('ix_currencies_user_id')

    # Drop tables
    op.drop_table('token_swaps')
    op.drop_table('transactions')
    op.drop_table('currencies')

    # Drop enums
    op.execute('DROP TYPE IF EXISTS currencytype')
    op.execute('DROP TYPE IF EXISTS transactiontype')
