"""Make sure grade histories are deleted if an assignment is deleted

Revision ID: 3b8c7d61ece8
Revises: 5fce393529d2
Create Date: 2017-09-22 18:56:24.250060

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '3b8c7d61ece8'
down_revision = '5fce393529d2'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('GradeHistory_Work_id_fkey', 'GradeHistory', type_='foreignkey')
    op.create_foreign_key('GradeHistory_Work_id_fkey', 'GradeHistory', 'Work', ['Work_id'], ['id'], ondelete='CASCADE')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint('GradeHistory_Work_id_fkey', 'GradeHistory', type_='foreignkey')
    op.create_foreign_key('GradeHistory_Work_id_fkey', 'GradeHistory', 'Work', ['Work_id'], ['id'])
    # ### end Alembic commands ###
