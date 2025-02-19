"""Add password_hash column to users table

Revision ID: 009_add_password_hash
Revises: 008_add_game_models
Create Date: 2024-02-19 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '009_add_password_hash'
down_revision = '008_add_game_models'
branch_labels = None
depends_on = None

def upgrade():
    # Add password_hash column to users table
    op.add_column('users', sa.Column('password_hash', sa.String(128)))

def downgrade():
    # Remove password_hash column from users table
    op.drop_column('users', 'password_hash')
