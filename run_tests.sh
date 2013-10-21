#!/bin/bash
FEDOCAL_CONFIG=`pwd`/tests/fedocal_test.cfg PYTHONPATH=fedocal ./nosetests \
    --with-coverage --cover-erase --cover-package=fedocal $*
