"""Update User model

Revision ID: 018_update_user_model
Revises: 017_initialize_all_models
Create Date: 2024-02-20 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '018_update_user_model'
down_revision = '017_initialize_all_models'  # Make sure this matches your latest migration
branch_labels = None
depends_on = None

def upgrade():
    # Rename password_hash to password if it exists
    with op.batch_alter_table('users') as batch_op:
        # Check if password_hash exists
        if 'password_hash' in [col['name'] for col in sa.inspect(op.get_bind()).get_columns('users')]:
            batch_op.alter_column('password_hash',
                                new_column_name='password',
                                existing_type=sa.String(length=128))
        
        # Add new columns if they don't exist
        columns = [col['name'] for col in sa.inspect(op.get_bind()).get_columns('users')]
        
        if 'salt' not in columns:
            batch_op.add_column(sa.Column('salt', sa.String(length=128), nullable=True))
        if 'role' not in columns:
            batch_op.add_column(sa.Column('role', sa.String(length=20), server_default='player'))
        if 'is_email_verified' not in columns:
            batch_op.add_column(sa.Column('is_email_verified', sa.Boolean(), server_default='false'))
        if 'last_login' not in columns:
            batch_op.add_column(sa.Column('last_login', sa.DateTime(), nullable=True))

def downgrade():
    # Remove new columns
    with op.batch_alter_table('users') as batch_op:
        batch_op.drop_column('last_login')
        batch_op.drop_column('is_email_verified')
        batch_op.drop_column('role')
        batch_op.drop_column('salt')
        
        # Rename password back to password_hash
        batch_op.alter_column('password',
                            new_column_name='password_hash',
                            existing_type=sa.String(length=128))
