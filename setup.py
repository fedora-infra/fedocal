#!/usr/bin/env python

"""
Setup script
"""

# Required to build on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from setuptools import setup
from fedocal import __version__


setup(
    name = 'fedocal',
    description = 'fedocal is a web based calendar application for Fedora.',
    version = __version__,
    author = 'Pierre-Yves Chibon',
    author_email = 'pingou@pingoured.fr',
    maintainer = 'Pierre-Yves Chibon',
    maintainer_email = 'pingou@pingoured.fr',
    license = 'GPLv3+',
    download_url = 'https://fedorahosted.org/releases/f/e/fedocal/',
    url = 'https://fedorahosted.org/fedocal/',
    packages=['fedocal'],
    include_package_data=True,
    scripts=['fedocal_cron.py'],
    install_requires=['Flask', 'SQLAlchemy>=0.6', 'wtforms', 'flask-wtf',
    'vobject', 'kitchen', 'python-fedora', 'pytz', 'python-dateutil<=1.5',
    'alembic', 'Markdown'],
    )
