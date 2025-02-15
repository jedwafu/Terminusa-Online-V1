"""rename metadata columns

Revision ID: 001
Revises: 
Create Date: 2024-02-16

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Rename metadata column in transactions table
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column('metadata', new_column_name='transaction_metadata')

    # Rename metadata column in chat_messages table
    with op.batch_alter_table('chat_messages') as batch_op:
        batch_op.alter_column('metadata', new_column_name='message_metadata')

def downgrade():
    # Revert changes if needed
    with op.batch_alter_table('transactions') as batch_op:
        batch_op.alter_column('transaction_metadata', new_column_name='metadata')

    with op.batch_alter_table('chat_messages') as batch_op:
        batch_op.alter_column('message_metadata', new_column_name='metadata')
