"""Make salt column nullable

Revision ID: 014_make_salt_nullable
Revises: 013_make_password_nullable
Create Date: 2024-02-19 18:25:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '014_make_salt_nullable'
down_revision = '013_make_password_nullable'
branch_labels = None
depends_on = None

def upgrade():
    # Make salt column nullable
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE users ALTER COLUMN salt DROP NOT NULL;
        END$$;
    """)

def downgrade():
    # Make salt column not nullable again
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE users ALTER COLUMN salt SET NOT NULL;
        END$$;
    """)
