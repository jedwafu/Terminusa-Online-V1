"""add guild war tables

Revision ID: 023_add_guild_war_tables
Revises: 022_add_mount_pet_tables
Create Date: 2024-01-20 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


# revision identifiers, used by Alembic.
revision = '023_add_guild_war_tables'
down_revision = '022_add_mount_pet_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create guild_wars table
    op.create_table(
        'guild_wars',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('challenger_id', sa.Integer(), nullable=False),
        sa.Column('target_id', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('start_time', sa.DateTime(), nullable=False),
        sa.Column('end_time', sa.DateTime(), nullable=False),
        sa.Column('winner_id', sa.Integer(), nullable=True),
        sa.Column('participants', JSONB(), nullable=True),
        sa.Column('scores', JSONB(), nullable=True),
        sa.Column('rewards', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['challenger_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['target_id'], ['guilds.id'], ),
        sa.ForeignKeyConstraint(['winner_id'], ['guilds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create war_territories table
    op.create_table(
        'war_territories',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('war_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('type', sa.String(20), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('controller_id', sa.Integer(), nullable=True),
        sa.Column('position_x', sa.Float(), nullable=False),
        sa.Column('position_y', sa.Float(), nullable=False),
        sa.Column('bonuses', JSONB(), nullable=True),
        sa.Column('defense_data', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['war_id'], ['guild_wars.id'], ),
        sa.ForeignKeyConstraint(['controller_id'], ['guilds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create war_events table
    op.create_table(
        'war_events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('war_id', sa.Integer(), nullable=False),
        sa.Column('type', sa.String(50), nullable=False),
        sa.Column('initiator_id', sa.Integer(), nullable=True),
        sa.Column('target_id', sa.Integer(), nullable=True),
        sa.Column('points', sa.Integer(), nullable=False),
        sa.Column('details', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['war_id'], ['guild_wars.id'], ),
        sa.ForeignKeyConstraint(['initiator_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create war_participants table
    op.create_table(
        'war_participants',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('war_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('guild_id', sa.Integer(), nullable=False),
        sa.Column('points_contributed', sa.Integer(), nullable=False),
        sa.Column('kills', sa.Integer(), nullable=False),
        sa.Column('deaths', sa.Integer(), nullable=False),
        sa.Column('territories_captured', sa.Integer(), nullable=False),
        sa.Column('stats', JSONB(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['war_id'], ['guild_wars.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['guild_id'], ['guilds.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes
    op.create_index(
        'ix_guild_wars_status',
        'guild_wars',
        ['status']
    )
    op.create_index(
        'ix_guild_wars_start_time',
        'guild_wars',
        ['start_time']
    )
    op.create_index(
        'ix_war_territories_war_id',
        'war_territories',
        ['war_id']
    )
    op.create_index(
        'ix_war_territories_controller_id',
        'war_territories',
        ['controller_id']
    )
    op.create_index(
        'ix_war_events_war_id',
        'war_events',
        ['war_id']
    )
    op.create_index(
        'ix_war_events_initiator_id',
        'war_events',
        ['initiator_id']
    )
    op.create_index(
        'ix_war_participants_war_id',
        'war_participants',
        ['war_id']
    )
    op.create_index(
        'ix_war_participants_user_id',
        'war_participants',
        ['user_id']
    )
    op.create_index(
        'ix_war_participants_guild_id',
        'war_participants',
        ['guild_id']
    )

    # Add guild war stats columns to guilds table
    op.add_column('guilds', sa.Column('wars_won', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('guilds', sa.Column('wars_lost', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('guilds', sa.Column('total_war_points', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('guilds', sa.Column('territories_controlled', sa.Integer(), nullable=False, server_default='0'))


def downgrade():
    # Drop indexes
    op.drop_index('ix_war_participants_guild_id')
    op.drop_index('ix_war_participants_user_id')
    op.drop_index('ix_war_participants_war_id')
    op.drop_index('ix_war_events_initiator_id')
    op.drop_index('ix_war_events_war_id')
    op.drop_index('ix_war_territories_controller_id')
    op.drop_index('ix_war_territories_war_id')
    op.drop_index('ix_guild_wars_start_time')
    op.drop_index('ix_guild_wars_status')

    # Drop guild war stats columns from guilds table
    op.drop_column('guilds', 'territories_controlled')
    op.drop_column('guilds', 'total_war_points')
    op.drop_column('guilds', 'wars_lost')
    op.drop_column('guilds', 'wars_won')

    # Drop tables
    op.drop_table('war_participants')
    op.drop_table('war_events')
    op.drop_table('war_territories')
    op.drop_table('guild_wars')
