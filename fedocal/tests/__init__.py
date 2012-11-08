#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
 (c) 2012 - Copyright Pierre-Yves Chibon
 Author: Pierre-Yves Chibon <pingou@pingoured.fr>

 Distributed under License GPLv3 or later
 You can find a copy of this license on the website
 http://www.gnu.org/licenses/gpl.html

 This program is free software; you can redistribute it and/or modify
 it under the terms of the GNU General Public License as published by
 the Free Software Foundation; either version 3 of the License, or
 (at your option) any later version.

 This program is distributed in the hope that it will be useful,
 but WITHOUT ANY WARRANTY; without even the implied warranty of
 MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
 GNU General Public License for more details.

 You should have received a copy of the GNU General Public License
 along with this program; if not, write to the Free Software
 Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
 MA 02110-1301, USA.

 fedocal.model test script
"""

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

from datetime import date
from datetime import time
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from fedocallib import model, get_start_week

DB_PATH = '%s/test.db' % (os.path.dirname(
                                    os.path.abspath(__file__)))

TODAY = get_start_week(date.today().year, date.today().month,
    date.today().day) + timedelta(days=2)


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        self.session = model.create_tables('sqlite:///%s' % DB_PATH)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
