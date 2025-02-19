"""Add missing user columns

Revision ID: 010_add_missing_user_columns
Revises: 009_add_password_hash
Create Date: 2024-02-19 17:05:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '010_add_missing_user_columns'
down_revision = '009_add_password_hash'
branch_labels = None
depends_on = None

def upgrade():
    # Add missing columns to users table
    op.execute("""
        DO $$
        BEGIN
            -- Basic stats
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'level') THEN
                ALTER TABLE users ADD COLUMN level INTEGER NOT NULL DEFAULT 1;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'exp') THEN
                ALTER TABLE users ADD COLUMN exp BIGINT NOT NULL DEFAULT 0;
            END IF;
            
            -- Game stats
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'solana_balance') THEN
                ALTER TABLE users ADD COLUMN solana_balance FLOAT NOT NULL DEFAULT 0.0;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'health_status') THEN
                ALTER TABLE users ADD COLUMN health_status VARCHAR(50) NOT NULL DEFAULT 'Normal';
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_in_gate') THEN
                ALTER TABLE users ADD COLUMN is_in_gate BOOLEAN NOT NULL DEFAULT false;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_in_party') THEN
                ALTER TABLE users ADD COLUMN is_in_party BOOLEAN NOT NULL DEFAULT false;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'inventory_slots') THEN
                ALTER TABLE users ADD COLUMN inventory_slots INTEGER NOT NULL DEFAULT 20;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'party_id') THEN
                ALTER TABLE users ADD COLUMN party_id INTEGER;
            END IF;
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'guild_id') THEN
                ALTER TABLE users ADD COLUMN guild_id INTEGER;
            END IF;
            
            -- Last activity tracking
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'last_login') THEN
                ALTER TABLE users ADD COLUMN last_login TIMESTAMP;
            END IF;
            
            -- Role management
            IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role') THEN
                ALTER TABLE users ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user';
            END IF;
        END$$;
    """)

def downgrade():
    # Drop added columns
    op.execute("""
        DO $$
        BEGIN
            -- Drop columns if they exist
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'level') THEN
                ALTER TABLE users DROP COLUMN level;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'exp') THEN
                ALTER TABLE users DROP COLUMN exp;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'solana_balance') THEN
                ALTER TABLE users DROP COLUMN solana_balance;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'health_status') THEN
                ALTER TABLE users DROP COLUMN health_status;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_in_gate') THEN
                ALTER TABLE users DROP COLUMN is_in_gate;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'is_in_party') THEN
                ALTER TABLE users DROP COLUMN is_in_party;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'inventory_slots') THEN
                ALTER TABLE users DROP COLUMN inventory_slots;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'party_id') THEN
                ALTER TABLE users DROP COLUMN party_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'guild_id') THEN
                ALTER TABLE users DROP COLUMN guild_id;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'last_login') THEN
                ALTER TABLE users DROP COLUMN last_login;
            END IF;
            IF EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'users' AND column_name = 'role') THEN
                ALTER TABLE users DROP COLUMN role;
            END IF;
        END$$;
    """)
