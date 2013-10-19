"""Rename managers as editors


Revision ID: 2a554683048e
Revises: 43bc10530adb
Create Date: 2013-10-15 10:28:27.642713

"""

# revision identifiers, used by Alembic.
revision = '2a554683048e'
down_revision = '43bc10530adb'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.alter_column('calendars', column_name='calendar_manager_group',
                    name='calendar_editor_group')


def downgrade():
    op.alter_column('calendars', column_name='calendar_editor_group',
                    name='calendar_manager_group')
