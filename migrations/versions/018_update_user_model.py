"""Update User model

Revision ID: 018_update_user_model
Revises: 017_initialize_all_models
Create Date: 2024-02-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '018_update_user_model'
down_revision = '017_initialize_all_models'
branch_labels = None
depends_on = None

def upgrade():
    # Rename password_hash to password
    op.alter_column('users', 'password_hash',
                    new_column_name='password',
                    existing_type=sa.String(length=128))
    
    # Add new columns
    op.add_column('users', sa.Column('salt', sa.String(length=128), nullable=True))
    op.add_column('users', sa.Column('role', sa.String(length=20), server_default='player'))
    op.add_column('users', sa.Column('is_email_verified', sa.Boolean(), server_default='false'))
    op.add_column('users', sa.Column('last_login', sa.DateTime(), nullable=True))

def downgrade():
    # Remove new columns
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'is_email_verified')
    op.drop_column('users', 'role')
    op.drop_column('users', 'salt')
    
    # Rename password back to password_hash
    op.alter_column('users', 'password',
                    new_column_name='password_hash',
                    existing_type=sa.String(length=128))
