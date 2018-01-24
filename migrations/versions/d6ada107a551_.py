"""Merge two migrations

Revision ID: d6ada107a551
Revises: 7b03e3da9996, 10ad986794e4
Create Date: 2018-01-22 02:06:39.524460

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = 'd6ada107a551'
down_revision = ('7b03e3da9996', '10ad986794e4')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
