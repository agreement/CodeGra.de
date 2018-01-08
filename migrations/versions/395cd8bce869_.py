"""Merge revisions d41ea8185e11 and d327cb111bb1

Revision ID: 395cd8bce869
Revises: d41ea8185e11, d327cb111bb1
Create Date: 2018-01-03 16:08:21.235476

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '395cd8bce869'
down_revision = ('d41ea8185e11', 'd327cb111bb1')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
