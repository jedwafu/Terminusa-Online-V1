"""add user model

Revision ID: 003_add_user_model
Revises: 002_update_gate_model
Create Date: 2025-02-17 14:15:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect

# revision identifiers, used by Alembic.
revision = '003_add_user_model'
down_revision = '002_update_gate_model'
branch_labels = None
depends_on = None

def has_table(table_name):
    """Check if a table exists"""
    conn = op.get_bind()
    insp = inspect(conn)
    return table_name in insp.get_table_names()

def upgrade():
    if not has_table('users'):
        op.create_table('users',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('username', sa.String(length=80), nullable=False),
            sa.Column('email', sa.String(length=120), nullable=False),
            sa.Column('password_hash', sa.String(length=128), nullable=False),
            sa.Column('is_admin', sa.Boolean(), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True),
            sa.PrimaryKeyConstraint('id'),
            sa.UniqueConstraint('email'),
            sa.UniqueConstraint('username')
        )
    else:
        # If table exists, ensure password_hash column exists
        conn = op.get_bind()
        insp = inspect(conn)
        columns = [c['name'] for c in insp.get_columns('users')]
        if 'password_hash' not in columns:
            op.add_column('users', sa.Column('password_hash', sa.String(length=128)))

def downgrade():
    if has_table('users'):
        op.drop_table('users')
