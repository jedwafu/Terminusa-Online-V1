"""Initial schema with ordered tables

Revision ID: 001
Revises: 
Create Date: 2024-01-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    # Create users table first (no foreign key dependencies)
    op.create_table('users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('username', sa.String(20), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('password_hash', sa.LargeBinary(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('is_admin', sa.Boolean(), default=False),
        sa.Column('is_banned', sa.Boolean(), default=False),
        sa.Column('ban_reason', sa.String(255)),
        sa.Column('ban_expires', sa.DateTime()),
        sa.Column('last_login', sa.DateTime()),
        sa.Column('last_ip', sa.String(45)),
        sa.Column('failed_login_attempts', sa.Integer(), default=0),
        sa.Column('last_failed_login', sa.DateTime()),
        sa.Column('settings', postgresql.JSONB(), nullable=False),
        sa.Column('friends', postgresql.JSONB(), nullable=False),
        sa.Column('blocked_users', postgresql.JSONB(), nullable=False),
        sa.Column('guild_rank', sa.String(20)),
        sa.Column('solana_balance', sa.Numeric(precision=18, scale=9), default=0),
        sa.Column('exons_balance', sa.Numeric(precision=18, scale=9), default=0),
        sa.Column('crystals', sa.BigInteger(), default=0),
        sa.Column('registered_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('username'),
        sa.UniqueConstraint('email')
    )

    # Create guilds table
    op.create_table('guilds',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.String(500)),
        sa.Column('leader_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer()),
        sa.Column('experience', sa.BigInteger()),
        sa.Column('reputation', sa.Integer()),
        sa.Column('crystal_balance', sa.BigInteger()),
        sa.Column('exon_balance', sa.Numeric(precision=18, scale=9)),
        sa.Column('crystal_tax_rate', sa.Integer()),
        sa.Column('exon_tax_rate', sa.Integer()),
        sa.Column('max_members', sa.Integer()),
        sa.Column('max_quests', sa.Integer()),
        sa.Column('total_members', sa.Integer()),
        sa.Column('active_members', sa.Integer()),
        sa.Column('total_gates_cleared', sa.Integer()),
        sa.Column('total_quests_completed', sa.Integer()),
        sa.Column('recruitment_status', sa.String(20)),
        sa.Column('min_level_requirement', sa.Integer()),
        sa.Column('settings', postgresql.JSONB(), nullable=False),
        sa.Column('created_at', sa.DateTime()),
        sa.Column('updated_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['leader_id'], ['users.id'], deferrable=True, initially='DEFERRED'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('name')
    )

    # Add guild_id to users table after guilds table is created
    op.add_column('users',
        sa.Column('guild_id', sa.Integer(), sa.ForeignKey('guilds.id', deferrable=True, initially='DEFERRED'))
    )

def downgrade():
    # Drop tables in reverse order
    op.drop_column('users', 'guild_id')
    op.drop_table('guilds')
    op.drop_table('users')
