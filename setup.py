#!/usr/bin/env python

"""
Setup script
"""

# Required to build on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

from setuptools import setup

from fedocal import __version__


def get_requirements(requirements_file='requirements.txt'):
    """Get the contents of a file listing the requirements.

    :arg requirements_file: path to a requirements file
    :type requirements_file: string
    :returns: the list of requirements, or an empty list if
              `requirements_file` could not be opened or read
    :return type: list
    """

    lines = open(requirements_file).readlines()

    return [
        line.strip().split('#')[0]
        for line in lines
        if not line.startswith('#')
    ]


setup(
    name='fedocal',
    description='fedocal is a web based calendar application for Fedora.',
    version=__version__,
    author='Pierre-Yves Chibon',
    author_email='pingou@pingoured.fr',
    maintainer='Pierre-Yves Chibon',
    maintainer_email='pingou@pingoured.fr',
    license='GPLv3+',
    download_url='https://fedorahosted.org/releases/f/e/fedocal/',
    url='https://fedorahosted.org/fedocal/',
    packages=['fedocal'],
    include_package_data=True,
    scripts=['fedocal_cron.py'],
    install_requires=get_requirements(),
)
