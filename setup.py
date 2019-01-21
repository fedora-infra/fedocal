#!/usr/bin/env python

"""
Setup script
"""

import os
import re

from setuptools import setup


here = os.path.abspath(os.path.dirname(__file__))

with open(os.path.join(here, "fedocal", "__init__.py")) as fd:
    match = re.search(r"^__version__ = '([^']+)'$", fd.read(), re.MULTILINE)
    VERSION = match.group(1)


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
    version=VERSION,
    author='Pierre-Yves Chibon',
    author_email='pingou@pingoured.fr',
    maintainer='Pierre-Yves Chibon',
    maintainer_email='pingou@pingoured.fr',
    license='GPLv3+',
    download_url='https://pagure.io/fedocal/releases/',
    url='https://pagure.io/fedocal/',
    packages=['fedocal'],
    include_package_data=True,
    scripts=['fedocal_cron.py'],
    install_requires=get_requirements(),
)
