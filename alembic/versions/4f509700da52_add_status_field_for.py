"""Add the calendar_status table

Revision ID: 4f509700da52
Revises: 2a554683048e
Create Date: 2013-10-15 11:21:34.353817

"""

# revision identifiers, used by Alembic.
revision = '4f509700da52'
down_revision = '43bc10530adb'

from alembic import op
import sqlalchemy as sa

status = sa.sql.table(
    'calendar_status',
    sa.sql.column('status', sa.String(50))
)


def upgrade():
    op.create_table(
        'calendar_status',
        sa.Column('status', sa.String(50), primary_key=True),
    )

    for str_status in ['Enabled', 'Disabled']:
        ins = "INSERT INTO calendar_status (status) VALUES ('%s');" % (
            str_status)
        op.execute(ins)


def downgrade():
    op.drop_table('calendar_status')
