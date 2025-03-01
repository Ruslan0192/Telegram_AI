"""empty message

Revision ID: efc7d0485269
Revises: 6496c5eb3f6f
Create Date: 2025-03-01 14:40:12.218259

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'efc7d0485269'
down_revision: Union[str, None] = '6496c5eb3f6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
