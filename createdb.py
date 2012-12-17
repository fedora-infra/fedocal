#!/usr/bin/python

from fedocal import APP
from fedocal.fedocallib import model

model.create_tables(APP.config['DB_URL'],
    APP.config['PATH_ALEMBIC_INI'], True)
