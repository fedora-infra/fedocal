#!/bin/sh

PYTHONPATH=fedocal pylint -f parseable fedocal | tee pylint.out

#pep8 fedocal/*.py fedocal/*/*.py | tee pep8.out
