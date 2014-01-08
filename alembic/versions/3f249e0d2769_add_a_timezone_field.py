"""Add a timezone field

Revision ID: 3f249e0d2769
Revises: 2a554683048e
Create Date: 2014-01-07 18:27:03.957521

"""

# revision identifiers, used by Alembic.
revision = '3f249e0d2769'
down_revision = '2a554683048e'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column(
        'meetings',
        sa.Column('meeting_timezone', sa.Text, default='UTC')
    )
    ins = "UPDATE meetings SET meeting_timezone='UTC';"
    op.execute(ins)

    op.alter_column('meetings',
                    column_name='meeting_timezone',
                    nullable=False,
                    existing_nullable=True,
                    )


def downgrade():
    op.drop_column('meetings', 'meeting_timezone')
