"""Add remind_from field

Revision ID: 351329b8d7da
Revises: 4f8bd7cac829
Create Date: 2014-05-21 14:49:37.002055

"""

# revision identifiers, used by Alembic.
revision = '351329b8d7da'
down_revision = '4f8bd7cac829'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Add the reminder_from column to the reminders table '''
    op.add_column(
        'reminders',
        sa.Column('reminder_from', sa.String(100))
    )


def downgrade():
    ''' Drop the reminder_from column to the reminders table '''
    op.drop_column('reminders', 'reminder_from')
