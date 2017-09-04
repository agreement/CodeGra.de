"""empty message

Revision ID: c3e982f6b17b
Revises: 6b72d26d1ab0
Create Date: 2017-08-30 12:27:20.340051

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = 'c3e982f6b17b'
down_revision = '6b72d26d1ab0'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    conn.execute(text("""
    UPDATE "File"
    SET name =
    CASE
        WHEN extension = '' THEN name
        ELSE name || '.' || extension
    END
    WHERE is_directory = false;
    """))
    op.drop_column('File', 'extension')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('File', sa.Column('extension', sa.VARCHAR(), autoincrement=False, nullable=True))
    # ### end Alembic commands ###