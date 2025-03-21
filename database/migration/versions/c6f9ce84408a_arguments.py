"""arguments

Revision ID: c6f9ce84408a
Revises: 6558e5226370
Create Date: 2025-03-06 17:45:21.921603

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c6f9ce84408a'
down_revision: Union[str, None] = '6558e5226370'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('location', sa.String(length=50), nullable=False))
    op.add_column('Users', sa.Column('unit', sa.String(length=20), nullable=False))
    op.drop_column('Users', 'characteristic')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Users', sa.Column('characteristic', sa.TEXT(), autoincrement=False, nullable=False))
    op.drop_column('Users', 'unit')
    op.drop_column('Users', 'location')
    # ### end Alembic commands ###
