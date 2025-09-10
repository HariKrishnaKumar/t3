"""Create recommendations table

Revision ID: cafe5df41e54
Revises: 159831d97d89
Create Date: 2025-09-09 16:13:34.490589

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cafe5df41e54'
down_revision: Union[str, Sequence[str], None] = '159831d97d89'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # It tells the database to create a new table named 'recommendations'
    op.create_table('recommendations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('mobile_number', sa.String(length=15), nullable=False),
    sa.Column('recommendations', sa.JSON(), nullable=False),
    # This creates the link between the 'recommendations' and 'users' tables
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_recommendations_id'), 'recommendations', ['id'], unique=False)


# This function runs when you REVERT the migration
def downgrade() -> None:
    # It tells the database to safely remove the 'recommendations' table
    op.drop_index(op.f('ix_recommendations_id'), table_name='recommendations')
    op.drop_table('recommendations')
