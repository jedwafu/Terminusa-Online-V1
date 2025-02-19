"""Add password_hash column to users table

Revision ID: 009_add_password_hash
Revises: 008_add_game_models
Create Date: 2024-02-19 14:45:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import text, exc

# revision identifiers, used by Alembic.
revision = '009_add_password_hash'
down_revision = '008_add_game_models'
branch_labels = None
depends_on = None

def execute_with_retry(statement, parameters=None):
    """Execute a statement with retry logic for transaction errors"""
    conn = op.get_bind()
    try:
        if parameters:
            conn.execute(text(statement), parameters)
        else:
            conn.execute(text(statement))
    except exc.DBAPIError as e:
        if 'current transaction is aborted' in str(e):
            # Rollback and retry once
            try:
                conn.execute(text('ROLLBACK'))
                if parameters:
                    conn.execute(text(statement), parameters)
                else:
                    conn.execute(text(statement))
            except Exception as retry_error:
                raise retry_error from e
        else:
            raise

def has_column(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        result = execute_with_retry(
            "SELECT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = :table AND column_name = :column)",
            {"table": table_name, "column": column_name}
        )
        return result.scalar()
    except Exception:
        return False

def upgrade():
    # First update alembic_version to prevent transaction issues
    execute_with_retry("""
        UPDATE alembic_version 
        SET version_num = '009_add_password_hash' 
        WHERE version_num = '008_add_game_models'
    """)

    # Add password_hash column if it doesn't exist
    if not has_column('users', 'password_hash'):
        execute_with_retry("""
            ALTER TABLE users 
            ADD COLUMN password_hash VARCHAR(128)
        """)

def downgrade():
    # First update alembic_version
    execute_with_retry("""
        UPDATE alembic_version 
        SET version_num = '008_add_game_models' 
        WHERE version_num = '009_add_password_hash'
    """)

    # Drop password_hash column if it exists
    if has_column('users', 'password_hash'):
        execute_with_retry("""
            ALTER TABLE users 
            DROP COLUMN password_hash
        """)
