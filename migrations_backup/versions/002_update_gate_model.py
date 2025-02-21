"""update gate model

Revision ID: 002_update_gate_model
Revises: 001_rename_metadata_columns
Create Date: 2025-02-17 04:18:43.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002_update_gate_model'
down_revision = '001_rename_metadata_columns'
branch_labels = None
depends_on = None

def upgrade():
    # Add new columns
    op.add_column('gates', sa.Column('grade', sa.String(), nullable=False, server_default='E'))
    op.add_column('gates', sa.Column('crystal_reward', sa.Integer(), nullable=False, server_default='0'))
    
    # Rename level_requirement to min_level
    op.alter_column('gates', 'level_requirement', new_column_name='min_level')
    
    # Create gate_magic_beasts association table
    op.create_table('gate_magic_beasts',
        sa.Column('gate_id', sa.Integer(), nullable=False),
        sa.Column('magic_beast_id', sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(['gate_id'], ['gates.id'], ),
        sa.ForeignKeyConstraint(['magic_beast_id'], ['magic_beasts.id'], ),
        sa.PrimaryKeyConstraint('gate_id', 'magic_beast_id')
    )

def downgrade():
    # Drop gate_magic_beasts table
    op.drop_table('gate_magic_beasts')
    
    # Rename min_level back to level_requirement
    op.alter_column('gates', 'min_level', new_column_name='level_requirement')
    
    # Drop new columns
    op.drop_column('gates', 'crystal_reward')
    op.drop_column('gates', 'grade')
