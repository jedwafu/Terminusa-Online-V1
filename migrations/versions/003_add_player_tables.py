"""Add player-related tables

Revision ID: 003_add_player_tables
Revises: 002_add_game_tables
Create Date: 2024-01-21

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '003_add_player_tables'
down_revision = '002_add_game_tables'
branch_labels = None
depends_on = None

def upgrade():
    # Create players table
    op.create_table('players',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('level', sa.Integer(), default=1),
        sa.Column('experience', sa.BigInteger(), default=0),
        sa.Column('class_type', sa.String(50)),
        sa.Column('job_type', sa.String(50)),
        sa.Column('stats', postgresql.JSONB()),
        sa.Column('equipment', postgresql.JSONB()),
        sa.Column('achievements', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create player_progress table
    op.create_table('player_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('quests_completed', sa.Integer(), default=0),
        sa.Column('dungeons_cleared', sa.Integer(), default=0),
        sa.Column('bosses_defeated', sa.Integer(), default=0),
        sa.Column('achievements_earned', sa.Integer(), default=0),
        sa.Column('items_crafted', sa.Integer(), default=0),
        sa.Column('monsters_killed', sa.Integer(), default=0),
        sa.Column('pvp_wins', sa.Integer(), default=0),
        sa.Column('pvp_losses', sa.Integer(), default=0),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create class_progress table
    op.create_table('class_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('class_type', sa.String(50), nullable=False),
        sa.Column('level', sa.Integer(), default=1),
        sa.Column('experience', sa.BigInteger(), default=0),
        sa.Column('skills_unlocked', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create job_progress table
    op.create_table('job_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('job_type', sa.String(50), nullable=False),
        sa.Column('level', sa.Integer(), default=1),
        sa.Column('experience', sa.BigInteger(), default=0),
        sa.Column('skills_unlocked', postgresql.JSONB()),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), default=sa.func.now(), onupdate=sa.func.now()),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create parties table
    op.create_table('parties',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('leader_id', sa.Integer(), nullable=False),
        sa.Column('max_size', sa.Integer(), default=4),
        sa.Column('is_private', sa.Boolean(), default=False),
        sa.Column('created_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['leader_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Create party_members table
    op.create_table('party_members',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('party_id', sa.Integer(), nullable=False),
        sa.Column('player_id', sa.Integer(), nullable=False),
        sa.Column('role', sa.String(50)),
        sa.Column('joined_at', sa.DateTime(), default=sa.func.now()),
        sa.ForeignKeyConstraint(['party_id'], ['parties.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['player_id'], ['players.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

def downgrade():
    op.drop_table('party_members')
    op.drop_table('parties')
    op.drop_table('job_progress')
    op.drop_table('class_progress')
    op.drop_table('player_progress')
    op.drop_table('players')
