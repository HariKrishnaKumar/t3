"""Add preference column to user table

Revision ID: 7106f658097a
Revises: 810bfc6f5909
Create Date: 2025-08-25 17:29:02.693004

"""
from alembic import op
import sqlalchemy as sa
from typing import Union, Sequence

# revision identifiers, used by Alembic.
revision = '7106f658097a'
down_revision = '810bfc6f5909'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('preference', sa.JSON(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'preference')