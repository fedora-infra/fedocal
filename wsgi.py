import logging
import sys

gunicorn_logger = logging.getLogger('gunicorn.error')
gunicorn_logger.addHandler(logging.StreamHandler(sys.stdout))

from fedocal import APP as application
