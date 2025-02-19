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
    # Add password_hash column if it doesn't exist
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'password_hash'
            ) THEN
                ALTER TABLE users 
                ADD COLUMN password_hash VARCHAR(128);
            END IF;
        END$$;
    """)

def downgrade():
    # Drop password_hash column if it exists
    op.execute("""
        DO $$
        BEGIN
            IF EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = 'users' 
                AND column_name = 'password_hash'
            ) THEN
                ALTER TABLE users 
                DROP COLUMN password_hash;
            END IF;
        END$$;
    """)
