"""Add calendar contact field

Revision ID: 45d83da297e8
Revises: 2c5c36431061
Create Date: 2012-11-14 14:30:07.352865

"""

# revision identifiers, used by Alembic.
revision = '45d83da297e8'
down_revision = '2c5c36431061'

from alembic import op
import sqlalchemy as sa


def upgrade():
    """ Add the calendar_contact field to the calendar table. """
    op.add_column('calendars', sa.Column('calendar_contact', sa.String(80)))


def downgrade():
    """ Remove the calendar_contact field to the calendar table. """
    op.drop_column('calendars', 'calendar_contact')

