"""Add achievement and gate tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None

def upgrade():
    # Create achievements table
    op.create_table('achievements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.String(50)),
        sa.Column('reward_type', sa.String(50)),
        sa.Column('reward_amount', sa.Integer()),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('completed', sa.Boolean(), default=False),
        sa.Column('completed_at', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create gates table
    op.create_table('gates',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('difficulty', sa.String(50), nullable=False),
        sa.Column('level_requirement', sa.Integer(), nullable=False),
        sa.Column('max_players', sa.Integer()),
        sa.Column('rewards', postgresql.JSONB()),
        sa.Column('monster_types', postgresql.JSONB()),
        sa.Column('boss_data', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.PrimaryKeyConstraint('id')
    )

    # Create gate_clears table (many-to-many relationship between users and gates)
    op.create_table('gate_clears',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('gate_id', sa.Integer(), nullable=False),
        sa.Column('clear_time', sa.Integer()),  # in seconds
        sa.Column('damage_dealt', sa.BigInteger()),
        sa.Column('damage_taken', sa.BigInteger()),
        sa.Column('rewards_claimed', postgresql.JSONB()),
        sa.Column('party_members', postgresql.JSONB()),
        sa.Column('cleared_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['gate_id'], ['gates.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create guild_quests table
    op.create_table('guild_quests',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('description', sa.Text()),
        sa.Column('difficulty', sa.String(50)),
        sa.Column('reward_type', sa.String(50)),
        sa.Column('reward_amount', sa.Integer()),
        sa.Column('required_members', sa.Integer()),
        sa.Column('current_members', sa.Integer(), default=0),
        sa.Column('status', sa.String(50), default='active'),
        sa.Column('progress', sa.Integer(), default=0),
        sa.Column('deadline', sa.DateTime()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('completed_at', sa.DateTime()),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('guild_quests')
    op.drop_table('gate_clears')
    op.drop_table('gates')
    op.drop_table('achievements')
