"""Add status field for calendars

Revision ID: 322997a7a41b
Revises: 4f509700da52
Create Date: 2013-10-15 11:52:16.185994

"""

# revision identifiers, used by Alembic.
revision = '322997a7a41b'
down_revision = '4f509700da52'

from alembic import op
import sqlalchemy as sa


def upgrade():
    try:
        op.add_column(
            'calendars',
            sa.Column('calendar_status',
                      sa.String(50),
                      sa.ForeignKey('calendar_status.status'),
                      nullable=False,
                      server_default='Enabled')
            )
    except Exception as e:
        print e


def downgrade():
    op.drop_column('calendars', 'calendar_status')
