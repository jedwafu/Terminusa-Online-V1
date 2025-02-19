"""Add remaining user columns

Revision ID: 011_add_remaining_user_columns
Revises: 010_add_missing_user_columns
Create Date: 2024-02-19 17:15:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '011_add_remaining_user_columns'
down_revision = '010_add_missing_user_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add remaining columns to users table
    op.execute("""
        DO $$
        BEGIN
            -- Character stats
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'job_class') THEN
                ALTER TABLE users ADD COLUMN job_class VARCHAR(50);
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'job_level') THEN
                ALTER TABLE users ADD COLUMN job_level INTEGER NOT NULL DEFAULT 1;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'solana_balance') THEN
                ALTER TABLE users ADD COLUMN solana_balance FLOAT NOT NULL DEFAULT 0.0;
            END IF;
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
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'job_class') THEN
                ALTER TABLE users DROP COLUMN job_class;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'job_level') THEN
                ALTER TABLE users DROP COLUMN job_level;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'solana_balance') THEN
                ALTER TABLE users DROP COLUMN solana_balance;
            END IF;
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
