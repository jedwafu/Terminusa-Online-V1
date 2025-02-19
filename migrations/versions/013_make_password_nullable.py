"""Make password column nullable

Revision ID: 013_make_password_nullable
Revises: 012_add_user_stats_columns
Create Date: 2024-02-19 18:10:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '013_make_password_nullable'
down_revision = '012_add_user_stats_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Make password column nullable
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE users ALTER COLUMN password DROP NOT NULL;
        END$$;
    """)

def downgrade():
    # Make password column not nullable again
    op.execute("""
        DO $$
        BEGIN
            ALTER TABLE users ALTER COLUMN password SET NOT NULL;
        END$$;
    """)
