"""Add game models

Revision ID: 008_add_game_models
Revises: 007_add_web3_and_announcements
Create Date: 2024-02-19 10:30:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from sqlalchemy import inspect, text
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '008_add_game_models'
down_revision = '007_add_web3_and_announcements'
branch_labels = None
depends_on = None

def has_table(table_name):
    """Check if a table exists"""
    try:
        conn = op.get_bind()
        result = conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = :table)"
        ), {"table": table_name})
        return result.scalar()
    except Exception:
        return False

def has_column(table_name, column_name):
    """Check if a column exists in a table"""
    try:
        conn = op.get_bind()
        result = conn.execute(text(
            "SELECT EXISTS (SELECT FROM information_schema.columns WHERE table_name = :table AND column_name = :column)"
        ), {"table": table_name, "column": column_name})
        return result.scalar()
    except Exception:
        return False

def has_enum(enum_name):
    """Check if an enum type exists"""
    try:
        conn = op.get_bind()
        result = conn.execute(text(
            "SELECT EXISTS (SELECT 1 FROM pg_type WHERE typname = :enum)"
        ), {"enum": enum_name})
        return result.scalar()
    except Exception:
        return False

def create_enum_if_not_exists(name, values):
    """Create enum if it doesn't exist"""
    if not has_enum(name):
        try:
            enum = postgresql.ENUM(*values, name=name)
            enum.create(op.get_bind())
        except Exception:
            # If creation fails, the enum might have been created in a parallel transaction
            pass

def upgrade():
    # Create enums if they don't exist
    create_enum_if_not_exists('hunterclass', ['F', 'E', 'D', 'C', 'B', 'A', 'S'])
    create_enum_if_not_exists('jobclass', ['Fighter', 'Mage', 'Assassin', 'Archer', 'Healer'])
    create_enum_if_not_exists('gaterank', ['E', 'D', 'C', 'B', 'A', 'S', 'Monarch'])
    create_enum_if_not_exists('itemrarity', ['Common', 'Uncommon', 'Rare', 'Epic', 'Legendary', 'Immortal'])
    create_enum_if_not_exists('mountpetrarity', ['Basic', 'Intermediate', 'Excellent', 'Legendary', 'Immortal'])
    create_enum_if_not_exists('healthstatus', ['Normal', 'Burned', 'Poisoned', 'Frozen', 'Feared', 'Confused', 'Dismembered', 'Decapitated', 'Shadow'])

    # Add columns to users table if they don't exist
    if has_table('users'):
        columns_to_add = [
            ('level', sa.Integer(), False, '1'),
            ('exp', sa.BigInteger(), False, '0'),
            ('job_class', sa.Enum('Fighter', 'Mage', 'Assassin', 'Archer', 'Healer', name='jobclass'), True, None),
            ('job_level', sa.Integer(), False, '1'),
            ('strength', sa.Integer(), False, '10'),
            ('agility', sa.Integer(), False, '10'),
            ('intelligence', sa.Integer(), False, '10'),
            ('vitality', sa.Integer(), False, '10'),
            ('luck', sa.Integer(), False, '10'),
            ('hp', sa.Integer(), False, '100'),
            ('max_hp', sa.Integer(), False, '100'),
            ('mp', sa.Integer(), False, '100'),
            ('max_mp', sa.Integer(), False, '100')
        ]
        
        for col_name, col_type, nullable, default in columns_to_add:
            if not has_column('users', col_name):
                try:
                    if default is not None:
                        op.add_column('users', sa.Column(col_name, col_type, nullable=nullable, server_default=default))
                    else:
                        op.add_column('users', sa.Column(col_name, col_type, nullable=nullable))
                except Exception:
                    # Column might have been added in a parallel transaction
                    pass

    # Create tables if they don't exist
    if not has_table('guilds'):
        try:
            op.create_table(
                'guilds',
                sa.Column('id', sa.Integer(), nullable=False),
                sa.Column('name', sa.String(100), nullable=False),
                sa.Column('leader_id', sa.Integer(), sa.ForeignKey('users.id')),
                sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
                sa.Column('level', sa.Integer(), nullable=False, server_default='1'),
                sa.Column('exp', sa.BigInteger(), nullable=False, server_default='0'),
                sa.Column('crystals', sa.Integer(), nullable=False, server_default='0'),
                sa.Column('exons_balance', sa.Float(), nullable=False, server_default='0.0'),
                sa.PrimaryKeyConstraint('id'),
                sa.UniqueConstraint('name')
            )
        except Exception:
            pass

    # Add foreign key constraints if tables exist
    if has_table('users') and has_table('guilds'):
        try:
            op.create_foreign_key('fk_users_guild', 'users', 'guilds', ['guild_id'], ['id'])
        except Exception:
            pass

def downgrade():
    # Drop foreign key constraints if they exist
    try:
        op.drop_constraint('fk_users_guild', 'users')
    except Exception:
        pass

    # Drop tables if they exist
    if has_table('guilds'):
        try:
            op.drop_table('guilds')
        except Exception:
            pass

    # Drop columns from users table if they exist
    columns_to_drop = [
        'level', 'exp', 'job_class', 'job_level',
        'strength', 'agility', 'intelligence', 'vitality', 'luck',
        'hp', 'max_hp', 'mp', 'max_mp'
    ]
    for column in columns_to_drop:
        if has_column('users', column):
            try:
                op.drop_column('users', column)
            except Exception:
                pass

    # Drop enums if they exist
    enums_to_drop = [
        'hunterclass', 'jobclass', 'gaterank', 'itemrarity',
        'mountpetrarity', 'healthstatus'
    ]
    for enum in enums_to_drop:
        if has_enum(enum):
            try:
                op.execute(text(f'DROP TYPE IF EXISTS {enum}'))
            except Exception:
                pass
