"""rename metadata columns

Revision ID: 001
Revises: 
Create Date: 2024-02-16

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import sqlite
from sqlalchemy import inspect

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def has_column(table_name, column_name):
    """Check if a column exists in a table"""
    conn = op.get_bind()
    insp = inspect(conn)
    columns = [c['name'] for c in insp.get_columns(table_name)]
    return column_name in columns

def upgrade():
    # Create temporary tables with new column names
    op.create_table('transactions_new',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('transaction_metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )

    op.create_table('chat_messages_new',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('message_metadata', sa.JSON())
    )

    # Copy data from old tables to new tables
    if has_column('transactions', 'metadata'):
        # Old column name exists
        op.execute('''
            INSERT INTO transactions_new 
            SELECT id, user_id, type, amount, currency, description, metadata, created_at 
            FROM transactions
        ''')
    else:
        # New column name exists
        op.execute('''
            INSERT INTO transactions_new 
            SELECT id, user_id, type, amount, currency, description, transaction_metadata, created_at 
            FROM transactions
        ''')

    if has_column('chat_messages', 'metadata'):
        # Old column name exists
        op.execute('''
            INSERT INTO chat_messages_new 
            SELECT id, sender_id, channel, content, created_at, metadata 
            FROM chat_messages
        ''')
    else:
        # New column name exists
        op.execute('''
            INSERT INTO chat_messages_new 
            SELECT id, sender_id, channel, content, created_at, message_metadata 
            FROM chat_messages
        ''')

    # Drop old tables
    op.drop_table('transactions')
    op.drop_table('chat_messages')

    # Rename new tables to original names
    op.rename_table('transactions_new', 'transactions')
    op.rename_table('chat_messages_new', 'chat_messages')

def downgrade():
    # Create temporary tables with old column names
    op.create_table('transactions_old',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('type', sa.String(), nullable=False),
        sa.Column('amount', sa.Float(), nullable=False),
        sa.Column('currency', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('metadata', sa.JSON()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now())
    )

    op.create_table('chat_messages_old',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('sender_id', sa.Integer(), sa.ForeignKey('users.id')),
        sa.Column('channel', sa.String(), nullable=False),
        sa.Column('content', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('metadata', sa.JSON())
    )

    # Copy data back
    op.execute('''
        INSERT INTO transactions_old 
        SELECT id, user_id, type, amount, currency, description, transaction_metadata, created_at 
        FROM transactions
    ''')

    op.execute('''
        INSERT INTO chat_messages_old 
        SELECT id, sender_id, channel, content, created_at, message_metadata 
        FROM chat_messages
    ''')

    # Drop current tables
    op.drop_table('transactions')
    op.drop_table('chat_messages')

    # Rename old tables to original names
    op.rename_table('transactions_old', 'transactions')
    op.rename_table('chat_messages_old', 'chat_messages')
