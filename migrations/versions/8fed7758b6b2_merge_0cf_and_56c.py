"""Merge 0cf and 56c

Revision ID: 8fed7758b6b2
Revises: 0cfce1799c57, 56c9dc73440a
Create Date: 2017-10-03 01:04:50.571085

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8fed7758b6b2'
down_revision = ('0cfce1799c57', '56c9dc73440a')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
