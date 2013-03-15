"""Add boolean to Meeting for full-day meeting

Revision ID: 2e5d25a095df
Revises: 45d83da297e8
Create Date: 2012-12-12 08:46:15.378554

"""

# revision identifiers, used by Alembic.
revision = '2e5d25a095df'
down_revision = '45d83da297e8'

from alembic import op
import sqlalchemy as sa


def upgrade():
    op.add_column('meetings', sa.Column('full_day',
        sa.Boolean, default=False))


def downgrade():
    op.drop_column('meetings', 'full_day')
