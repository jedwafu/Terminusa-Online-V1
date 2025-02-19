"""Add game models

Revision ID: 008_add_game_models
Revises: 007_add_web3_and_announcements
Create Date: 2024-02-19 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import text, exc
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '008_add_game_models'
down_revision = '007_add_web3_and_announcements'
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

def has_enum(enum_name):
    """Check if an enum type exists"""
    try:
        result = execute_with_retry(
            "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :enum)",
            {"enum": enum_name}
        )
        return result.scalar()
    except Exception:
        return False

def create_enum_if_not_exists(name, values):
    """Create enum if it doesn't exist"""
    if not has_enum(name):
        values_str = "', '".join(values)
        execute_with_retry(f"CREATE TYPE {name} AS ENUM ('{values_str}')")

def upgrade():
    # Create enums if they don't exist
    create_enum_if_not_exists('hunterclass', ['F', 'E', 'D', 'C', 'B', 'A', 'S'])
    create_enum_if_not_exists('jobclass', ['Fighter', 'Mage', 'Assassin', 'Archer', 'Healer'])
    create_enum_if_not_exists('gaterank', ['E', 'D', 'C', 'B', 'A', 'S', 'Monarch'])
    create_enum_if_not_exists('itemrarity', ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Immortal'])
    create_enum_if_not_exists('mountpetrarity', ['Basic', 'Intermediate', 'Excellent', 'Legendary', 'Immortal'])
    create_enum_if_not_exists('healthstatus', ['Normal', 'Burned', 'Poisoned', 'Frozen', 'Feared', 'Confused', 'Dismembered', 'Decapitated', 'Shadow'])

    # Add columns to users table if they don't exist
    columns_to_add = [
        ('level', 'INTEGER NOT NULL DEFAULT 1'),
        ('exp', 'BIGINT NOT NULL DEFAULT 0'),
        ('job_class', 'jobclass'),
        ('job_level', 'INTEGER NOT NULL DEFAULT 1'),
        ('strength', 'INTEGER NOT NULL DEFAULT 10'),
        ('agility', 'INTEGER NOT NULL DEFAULT 10'),
        ('intelligence', 'INTEGER NOT NULL DEFAULT 10'),
        ('vitality', 'INTEGER NOT NULL DEFAULT 10'),
        ('luck', 'INTEGER NOT NULL DEFAULT 10'),
        ('hp', 'INTEGER NOT NULL DEFAULT 100'),
        ('max_hp', 'INTEGER NOT NULL DEFAULT 100'),
        ('mp', 'INTEGER NOT NULL DEFAULT 100'),
        ('max_mp', 'INTEGER NOT NULL DEFAULT 100')
    ]

    for col_name, col_type in columns_to_add:
        try:
            execute_with_retry(
                f"ALTER TABLE users ADD COLUMN IF NOT EXISTS {col_name} {col_type}"
            )
        except Exception:
            # Column might already exist
            pass

    # Create guilds table if it doesn't exist
    execute_with_retry("""
        CREATE TABLE IF NOT EXISTS guilds (
            id SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL UNIQUE,
            leader_id INTEGER REFERENCES users(id),
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            level INTEGER NOT NULL DEFAULT 1,
            exp BIGINT NOT NULL DEFAULT 0,
            crystals INTEGER NOT NULL DEFAULT 0,
            exons_balance FLOAT NOT NULL DEFAULT 0.0
        )
    """)

    # Add foreign key constraints if they don't exist
    try:
        execute_with_retry("""
            ALTER TABLE users 
            ADD CONSTRAINT fk_users_guild 
            FOREIGN KEY (guild_id) REFERENCES guilds(id)
        """)
    except Exception:
        # Constraint might already exist
        pass

def downgrade():
    # Drop foreign key constraints if they exist
    try:
        execute_with_retry("ALTER TABLE users DROP CONSTRAINT IF EXISTS fk_users_guild")
    except Exception:
        pass

    # Drop tables if they exist
    execute_with_retry("DROP TABLE IF EXISTS guilds")

    # Drop columns from users table if they exist
    columns_to_drop = [
        'level', 'exp', 'job_class', 'job_level',
        'strength', 'agility', 'intelligence', 'vitality', 'luck',
        'hp', 'max_hp', 'mp', 'max_mp'
    ]
    for column in columns_to_drop:
        try:
            execute_with_retry(f"ALTER TABLE users DROP COLUMN IF EXISTS {column}")
        except Exception:
            pass

    # Drop enums if they exist
    enums_to_drop = [
        'hunterclass', 'jobclass', 'gaterank', 'itemrarity',
        'mountpetrarity', 'healthstatus'
    ]
    for enum in enums_to_drop:
        try:
            execute_with_retry(f"DROP TYPE IF EXISTS {enum}")
        except Exception:
            pass
