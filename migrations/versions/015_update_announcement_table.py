"""Update announcement table

Revision ID: 015_update_announcement_table
Revises: 014_make_salt_nullable
Create Date: 2024-02-19 18:45:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '015_update_announcement_table'
down_revision = '014_make_salt_nullable'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns to announcements table
    op.execute("""
        DO $$
        BEGIN
            -- Add author_id column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'announcements' AND column_name = 'author_id'
            ) THEN
                ALTER TABLE announcements ADD COLUMN author_id INTEGER REFERENCES users(id);
            END IF;

            -- Add updated_at column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'announcements' AND column_name = 'updated_at'
            ) THEN
                ALTER TABLE announcements ADD COLUMN updated_at TIMESTAMP WITHOUT TIME ZONE DEFAULT CURRENT_TIMESTAMP;
            END IF;

            -- Add is_active column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'announcements' AND column_name = 'is_active'
            ) THEN
                ALTER TABLE announcements ADD COLUMN is_active BOOLEAN DEFAULT true;
            END IF;

            -- Add priority column if it doesn't exist
            IF NOT EXISTS (
                SELECT FROM information_schema.columns 
                WHERE table_name = 'announcements' AND column_name = 'priority'
            ) THEN
                ALTER TABLE announcements ADD COLUMN priority INTEGER DEFAULT 0;
            END IF;

            -- Set NOT NULL constraints
            ALTER TABLE announcements ALTER COLUMN created_at SET NOT NULL;
            ALTER TABLE announcements ALTER COLUMN updated_at SET NOT NULL;
            ALTER TABLE announcements ALTER COLUMN is_active SET NOT NULL;
            ALTER TABLE announcements ALTER COLUMN priority SET NOT NULL;

            -- Update title column length if needed
            ALTER TABLE announcements ALTER COLUMN title TYPE VARCHAR(200);
        END$$;
    """)

def downgrade():
    # Remove added columns from announcements table
    op.execute("""
        DO $$
        BEGIN
            -- Remove columns if they exist
            ALTER TABLE announcements 
                DROP COLUMN IF EXISTS author_id,
                DROP COLUMN IF EXISTS updated_at,
                DROP COLUMN IF EXISTS is_active,
                DROP COLUMN IF EXISTS priority;

            -- Revert title column length
            ALTER TABLE announcements ALTER COLUMN title TYPE VARCHAR(255);
        END$$;
    """)
