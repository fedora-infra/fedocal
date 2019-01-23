#!/bin/bash

pip install alembic
alembic -c /opt/app-root/config/alembic.ini upgrade head
