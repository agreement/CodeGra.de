"""empty message

Revision ID: 1b14f6bef6a1
Revises: 918751ff462f
Create Date: 2017-09-06 01:31:30.964980

"""
import sqlalchemy as sa
from alembic import op
from sqlalchemy.sql import text

# revision identifiers, used by Alembic.
revision = '1b14f6bef6a1'
down_revision = '918751ff462f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    conn = op.get_bind()
    conn.execute(text("""
    INSERT INTO "Permission" (name, default_value, course_permission)
    SELECT 'can_manage_site_users', false, false WHERE NOT EXISTS
        (SELECT 1 FROM "Permission" WHERE name = 'can_manage_site_users')
    """))
    pass
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    pass
    # ### end Alembic commands ###
