"""add announcements only

Revision ID: 006_add_announcements_only
Revises: 005_create_announcements
Create Date: 2025-02-17 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '006_add_announcements_only'
down_revision = '005_create_announcements'
branch_labels = None
depends_on = None

def has_table(table_name):
    """Check if a table exists"""
    conn = op.get_bind()
    insp = inspect(conn)
    return table_name in insp.get_table_names()

def upgrade():
    # No-op since announcements table is handled in 005_create_announcements
    pass

def downgrade():
    # No-op since announcements table is handled in 005_create_announcements
    pass
