"""add missing tables

Revision ID: 004
Revises: 003
Create Date: 2025-02-17 17:30:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    # Create any missing tables that might be needed
    # This is an empty migration to fix the chain
    pass

def downgrade():
    pass
