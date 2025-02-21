"""Update announcement model

Revision ID: 020_update_announcement_model
Revises: 019_update_model_relationships
Create Date: 2024-02-20 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '020_update_announcement_model'
down_revision = '019_update_model_relationships'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to announcements table
    with op.batch_alter_table('announcements') as batch_op:
        batch_op.add_column(sa.Column('priority', sa.Integer(), server_default='0'))
        batch_op.add_column(sa.Column('is_active', sa.Boolean(), server_default='true'))
        batch_op.add_column(sa.Column('author_id', sa.Integer(), sa.ForeignKey('users.id')))

    # Create index for author_id
    op.create_index('ix_announcements_author_id', 'announcements', ['author_id'])

    # Create index for priority and created_at for efficient sorting
    op.create_index('ix_announcements_priority_created', 'announcements', ['priority', 'created_at'])

def downgrade():
    # Drop indexes
    op.drop_index('ix_announcements_priority_created')
    op.drop_index('ix_announcements_author_id')

    # Remove columns
    with op.batch_alter_table('announcements') as batch_op:
        batch_op.drop_column('author_id')
        batch_op.drop_column('is_active')
        batch_op.drop_column('priority')
