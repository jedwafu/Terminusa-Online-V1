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
            result = conn.execute(text(statement), parameters)
        else:
            result = conn.execute(text(statement))
        return result
    except exc.DBAPIError as e:
        if 'current transaction is aborted' in str(e):
            # Rollback and retry once
            try:
                conn.execute(text('ROLLBACK'))
                if parameters:
                    result = conn.execute(text(statement), parameters)
                else:
                    result = conn.execute(text(statement))
                return result
            except Exception as retry_error:
                raise retry_error from e
        else:
            raise

def has_column(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        result = execute_with_retry("""
            SELECT EXISTS (
                SELECT 1 
                FROM information_schema.columns 
                WHERE table_name = :table 
                AND column_name = :column
            )
        """, {"table": table_name, "column": column_name})
        return result.scalar()
    except Exception:
        return False

def upgrade():
    # First clean up alembic_version table
    execute_with_retry("DELETE FROM alembic_version")
    execute_with_retry(f"INSERT INTO alembic_version (version_num) VALUES ('{down_revision}')")

    # Check if column exists
    if not has_column('users', 'password_hash'):
        # Add password_hash column if it doesn't exist
        execute_with_retry("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(128)
        """)
        print("Added password_hash column")

    # Update version
    execute_with_retry(f"""
        UPDATE alembic_version 
        SET version_num = '{revision}'
        WHERE version_num = '{down_revision}'
    """)
    print("Updated version to 009_add_password_hash")

def downgrade():
    # First clean up alembic_version table
    execute_with_retry("DELETE FROM alembic_version")
    execute_with_retry(f"INSERT INTO alembic_version (version_num) VALUES ('{revision}')")

    # Drop password_hash column if it exists
    if has_column('users', 'password_hash'):
        execute_with_retry("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS password_hash
        """)
        print("Dropped password_hash column")

    # Update version
    execute_with_retry(f"""
        UPDATE alembic_version 
        SET version_num = '{down_revision}'
        WHERE version_num = '{revision}'
    """)
    print("Updated version to 008_add_game_models")
