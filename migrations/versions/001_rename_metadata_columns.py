"""rename metadata columns

Revision ID: 001
Revises: 
Create Date: 2024-02-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create transactions table with the correct column name
    op.create_table('transactions',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('transaction_metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )

    # Create chat_messages table with the correct column name
    op.create_table('chat_messages',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('message_metadata', sa.JSON())
    )

def downgrade():
    op.drop_table('chat_messages')
    op.drop_table('transactions')
