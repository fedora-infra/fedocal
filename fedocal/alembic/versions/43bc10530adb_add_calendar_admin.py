"""Add calendar admin

Revision ID: 43bc10530adb
Revises: 2e5d25a095df
Create Date: 2013-05-27 18:17:12.891156

"""

# revision identifiers, used by Alembic.
revision = '43bc10530adb'
down_revision = '2e5d25a095df'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'calendars',
        sa.Column('calendar_admin_group', sa.String(100), nullable=True)
    )


def downgrade():
    op.drop_column('calendars', 'calendar_admin_group')
