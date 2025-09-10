"""Changes in preference column to String

Revision ID: 159831d97d89
Revises: 7106f658097a
Create Date: 2025-09-09 12:24:55.357488

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '159831d97d89'
down_revision: Union[str, Sequence[str], None] = '7106f658097a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('users', 'preference',
               existing_type=sa.JSON(),
               type_=sa.String(length=255),
               existing_nullable=True)


def downgrade() -> None:
    op.alter_column('users', 'preference',
               existing_type=sa.String(length=255),
               type_=sa.JSON(),
               existing_nullable=True)