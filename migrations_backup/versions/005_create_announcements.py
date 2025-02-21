"""create announcements table

Revision ID: 005_create_announcements
Revises: 004_add_missing_tables
Create Date: 2025-02-17 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '005_create_announcements'
down_revision = '004_add_missing_tables'
branch_labels = None
depends_on = None

def has_table(table_name):
    """Check if a table exists"""
    conn = op.get_bind()
    insp = inspect(conn)
    return table_name in insp.get_table_names()

def upgrade():
    if not has_table('announcements'):
        op.create_table('announcements',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('title', sa.String(length=255), nullable=False),
            sa.Column('content', sa.Text(), nullable=False),
            sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
            sa.PrimaryKeyConstraint('id')
        )

def downgrade():
    if has_table('announcements'):
        op.drop_table('announcements')
