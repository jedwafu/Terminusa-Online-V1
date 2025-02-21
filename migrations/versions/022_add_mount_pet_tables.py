"""Add mount and pet tables

Revision ID: 022_add_mount_pet_tables
Revises: 021_add_currency_system
Create Date: 2024-01-20 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '022_add_mount_pet_tables'
down_revision = '021_add_currency_system'
branch_labels = None
depends_on = None

def upgrade():
    # Create mount table
    op.create_table(
        'mount',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('rarity', sa.String(length=20), nullable=False),
        sa.Column('level_requirement', sa.Integer(), nullable=False),
        sa.Column('stats', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_equipped', sa.Boolean(), default=False),
        sa.Column('is_tradeable', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_mount_user_id', 'mount', ['user_id'])
    op.create_index('ix_mount_rarity', 'mount', ['rarity'])

    # Create pet table
    op.create_table(
        'pet',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('rarity', sa.String(length=20), nullable=False),
        sa.Column('level_requirement', sa.Integer(), nullable=False),
        sa.Column('abilities', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=False),
        sa.Column('is_tradeable', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('last_ability_use', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('ability_cooldowns', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_pet_user_id', 'pet', ['user_id'])
    op.create_index('ix_pet_rarity', 'pet', ['rarity'])

def downgrade():
    op.drop_index('ix_mount_rarity')
    op.drop_index('ix_mount_user_id')
    op.drop_table('mount')
    
    op.drop_index('ix_pet_rarity')
    op.drop_index('ix_pet_user_id')
    op.drop_table('pet')
