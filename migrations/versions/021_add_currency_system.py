"""Add currency system

Revision ID: 021_add_currency_system
Revises: 020_update_announcement_model
Create Date: 2024-01-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '021_add_currency_system'
down_revision = '020_update_announcement_model'
branch_labels = None
depends_on = None

def upgrade():
    # Add currency columns to user table
    op.add_column('user', sa.Column('solana_balance', sa.Numeric(precision=18, scale=8), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('exons_balance', sa.Numeric(precision=18, scale=8), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('crystals', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('user', sa.Column('web3_wallet', sa.String(length=44), nullable=True))

    # Create transaction table
    op.create_table(
        'transaction',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('recipient_id', sa.Integer(), nullable=True),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('from_currency', sa.String(length=20), nullable=True),
        sa.Column('to_currency', sa.String(length=20), nullable=True),
        sa.Column('amount', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('converted_amount', sa.Numeric(precision=18, scale=8), nullable=True),
        sa.Column('tax_amount', sa.Numeric(precision=18, scale=8), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.ForeignKeyConstraint(['recipient_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_transaction_timestamp', 'transaction', ['timestamp'])
    op.create_index('ix_transaction_user_id', 'transaction', ['user_id'])
    op.create_index('ix_transaction_recipient_id', 'transaction', ['recipient_id'])

    # Add currency columns to guild table
    op.add_column('guild', sa.Column('crystals', sa.BigInteger(), nullable=False, server_default='0'))
    op.add_column('guild', sa.Column('exons_balance', sa.Numeric(precision=18, scale=8), nullable=False, server_default='0'))

def downgrade():
    # Remove currency columns from user table
    op.drop_column('user', 'solana_balance')
    op.drop_column('user', 'exons_balance')
    op.drop_column('user', 'crystals')
    op.drop_column('user', 'web3_wallet')

    # Drop transaction table and indexes
    op.drop_index('ix_transaction_timestamp')
    op.drop_index('ix_transaction_user_id')
    op.drop_index('ix_transaction_recipient_id')
    op.drop_table('transaction')

    # Remove currency columns from guild table
    op.drop_column('guild', 'crystals')
    op.drop_column('guild', 'exons_balance')
