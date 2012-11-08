"""Add the meeting_date_end field to the meetings table

Revision ID: 2c5c36431061
Revises: None
Create Date: 2012-11-08 08:24:43.044403

"""

# revision identifiers, used by Alembic.
revision = '2c5c36431061'
down_revision = None

from alembic import op
import sqlalchemy as sa
from datetime import datetime


def upgrade():
    ''' Add the meeting_date_end column to the meetings table '''
    op.add_column('meetings', sa.Column('meeting_date_end', sa.Date,
				default=datetime.utcnow().date()))


def downgrade():
    ''' Drop the meeting_date_end column to the meetings table '''
    op.drop_column('meetings', 'meeting_date_end')
