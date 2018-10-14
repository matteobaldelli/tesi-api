"""empty message

Revision ID: 528a88a08c26
Revises: 0c26e8e401d1
Create Date: 2018-10-14 18:40:58.933988

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '528a88a08c26'
down_revision = '0c26e8e401d1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('metrics',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=255), nullable=True),
    sa.Column('weight', sa.Integer(), nullable=True),
    sa.Column('unit_label', sa.String(length=255), nullable=True),
    sa.Column('total_range_min', sa.Integer(), nullable=True),
    sa.Column('total_range_max', sa.Integer(), nullable=True),
    sa.Column('healthy_range_min', sa.Integer(), nullable=True),
    sa.Column('healthy_range_max', sa.Integer(), nullable=True),
    sa.Column('gender', sa.String(length=255), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.add_column(u'users', sa.Column('gender', sa.String(length=255), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column(u'users', 'gender')
    op.drop_table('metrics')
    # ### end Alembic commands ###
