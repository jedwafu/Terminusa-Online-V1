"""add announcements only

Revision ID: 006_add_announcements_only
Revises: 005_create_announcements
Create Date: 2025-02-17 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006_add_announcements_only'
down_revision = '005_create_announcements'
branch_labels = None
depends_on = None

def upgrade():
    # Create announcements table if it doesn't exist
    op.create_table('announcements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('announcements')
