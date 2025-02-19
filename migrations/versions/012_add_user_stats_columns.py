"""Add user stats columns

Revision ID: 012_add_user_stats_columns
Revises: 011_add_remaining_user_columns
Create Date: 2024-02-19 17:35:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '012_add_user_stats_columns'
down_revision = '011_add_remaining_user_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add missing columns to users table
    op.execute("""
        DO $$
        BEGIN
            -- Stats
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'strength') THEN
                ALTER TABLE users ADD COLUMN strength INTEGER NOT NULL DEFAULT 10;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'agility') THEN
                ALTER TABLE users ADD COLUMN agility INTEGER NOT NULL DEFAULT 10;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'intelligence') THEN
                ALTER TABLE users ADD COLUMN intelligence INTEGER NOT NULL DEFAULT 10;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'vitality') THEN
                ALTER TABLE users ADD COLUMN vitality INTEGER NOT NULL DEFAULT 10;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'luck') THEN
                ALTER TABLE users ADD COLUMN luck INTEGER NOT NULL DEFAULT 10;
            END IF;
            
            -- Combat stats
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'hp') THEN
                ALTER TABLE users ADD COLUMN hp INTEGER NOT NULL DEFAULT 100;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'max_hp') THEN
                ALTER TABLE users ADD COLUMN max_hp INTEGER NOT NULL DEFAULT 100;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'mp') THEN
                ALTER TABLE users ADD COLUMN mp INTEGER NOT NULL DEFAULT 100;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'max_mp') THEN
                ALTER TABLE users ADD COLUMN max_mp INTEGER NOT NULL DEFAULT 100;
            END IF;
        END$$;
    """)

def downgrade():
    # Drop added columns
    op.execute("""
        DO $$
        BEGIN
            -- Drop columns if they exist
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'strength') THEN
                ALTER TABLE users DROP COLUMN strength;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'agility') THEN
                ALTER TABLE users DROP COLUMN agility;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'intelligence') THEN
                ALTER TABLE users DROP COLUMN intelligence;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'vitality') THEN
                ALTER TABLE users DROP COLUMN vitality;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'luck') THEN
                ALTER TABLE users DROP COLUMN luck;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'hp') THEN
                ALTER TABLE users DROP COLUMN hp;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'max_hp') THEN
                ALTER TABLE users DROP COLUMN max_hp;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'mp') THEN
                ALTER TABLE users DROP COLUMN mp;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'max_mp') THEN
                ALTER TABLE users DROP COLUMN max_mp;
            END IF;
        END$$;
    """)
