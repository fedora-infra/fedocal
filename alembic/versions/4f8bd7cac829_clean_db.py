"""Clean db

Revision ID: 4f8bd7cac829
Revises: 3f249e0d2769
Create Date: 2014-01-09 14:03:13.997656

"""

# revision identifiers, used by Alembic.
revision = '4f8bd7cac829'
down_revision = '3f249e0d2769'

from alembic import op
import sqlalchemy as sa


def upgrade():
    ''' Drop the columns calendar_multiple_meetings and
    calendar_regional_meetings and rename meeting_region into
    meeting_location.
    '''
    op.drop_column('calendars', 'calendar_multiple_meetings')
    op.drop_column('calendars', 'calendar_regional_meetings')
    op.alter_column(
        'meetings',
        column_name='meeting_region',
        new_column_name='meeting_location',
        type_=sa.Text,
        existing_type=sa.String(100))


def downgrade():
    ''' Add the columns calendar_multiple_meetings and
    calendar_regional_meetings and rename meeting_location into
    meeting_region.
    '''
    op.add_column(
        'calendars',
        sa.Column(
            'calendar_multiple_meetings',
            sa.Boolean, default=False,
            nullable=False
        )
    )
    op.add_column(
        'calendars',
        sa.Column(
            'calendar_regional_meetings',
            sa.Boolean, default=False,
            nullable=False
        )
    )
    op.alter_column(
        'meetings',
        column_name='meeting_location',
        new_column_name='meeting_region',
        type_=sa.String(100),
        existing_type=sa.Text)
