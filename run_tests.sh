#!/bin/bash
FEDOCAL_CONFIG=../tests/fedocal_test.cfg PYTHONPATH=fedocal nosetests --with-coverage --cover-erase --cover-package=fedocal $*
