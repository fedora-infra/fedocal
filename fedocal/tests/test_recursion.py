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

from fedocallib import model
from tests import Modeltests


class Recursiontests(Modeltests):
    """ Recursion tests. """

    def test_init_recursion(self):
        """ Test the Recursion init function. """
        obj = model.Recursive('14',
            date.today() + timedelta(days=7))
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.recursion_frequency, '14')
        self.assertEqual(obj.recursion_ends, date.today() + timedelta(days=7))

    def test_init_recursion_fail(self):
        """ Test the Recursion init function. """
        obj = model.Recursive('28',
            date.today() + timedelta(days=7))
        obj.save(self.session)
        try:
            self.session.commit()
        except IntegrityError, error:
            self.assertEqual(error.message, '(IntegrityError) constraint failed')
            self.assertTrue(str(error).startswith("(IntegrityError) constraint"\
            " failed u'INSERT INTO recursivity (recursion_frequency, "\
            "recursion_start, recursion_ends)"))

    def test_repr_recursion(self):
        """ Test the Recursive string representation function. """
        self.test_init_recursion()
        obj = model.Recursive.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertEqual(str(obj), '<Recursion(From \'%s\' to \'%s\' '\
            'every \'14\')>' % (date.today(), date.today() + timedelta(days=7)))

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Recursiontests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
