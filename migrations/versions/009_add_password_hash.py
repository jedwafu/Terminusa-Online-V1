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
    # First check current state
    conn = op.get_bind()
    
    # Check alembic_version
    result = conn.execute("SELECT version_num FROM alembic_version")
    current_version = result.scalar()
    print(f"Current version: {current_version}")
    
    # Check if password_hash column exists
    result = conn.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'password_hash'
        )
    """)
    has_password_hash = result.scalar()
    print(f"Has password_hash column: {has_password_hash}")
    
    # Add password_hash column if it doesn't exist
    if not has_password_hash:
        op.execute("""
            ALTER TABLE users 
            ADD COLUMN IF NOT EXISTS password_hash VARCHAR(128)
        """)
        print("Added password_hash column")
    
    # Clean up alembic_version table
    op.execute("DELETE FROM alembic_version")
    op.execute(f"INSERT INTO alembic_version (version_num) VALUES ('{revision}')")
    print(f"Updated version to {revision}")

def downgrade():
    # First check current state
    conn = op.get_bind()
    
    # Check alembic_version
    result = conn.execute("SELECT version_num FROM alembic_version")
    current_version = result.scalar()
    print(f"Current version: {current_version}")
    
    # Check if password_hash column exists
    result = conn.execute("""
        SELECT EXISTS (
            SELECT 1 
            FROM information_schema.columns 
            WHERE table_name = 'users' 
            AND column_name = 'password_hash'
        )
    """)
    has_password_hash = result.scalar()
    print(f"Has password_hash column: {has_password_hash}")
    
    # Drop password_hash column if it exists
    if has_password_hash:
        op.execute("""
            ALTER TABLE users 
            DROP COLUMN IF EXISTS password_hash
        """)
        print("Dropped password_hash column")
    
    # Clean up alembic_version table
    op.execute("DELETE FROM alembic_version")
    op.execute(f"INSERT INTO alembic_version (version_num) VALUES ('{down_revision}')")
    print(f"Updated version to {down_revision}")
