#!/usr/bin/env python

"""
Setup script
"""

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
    include_package_data = True,
    exclude_package_data={'': ['tests/*']},
    install_requires=['Flask']
    )
