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


class Calendartests(Modeltests):
    """ Calendar tests. """

    def test_init_calendar(self):
        """ Test the Calendar init function. """
        obj = model.Calendar('test_calendar', 'This is a test calendar',
            'fi-apprentice', True)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = model.Calendar('test_calendar2',
            'This is another test calendar',
            'packager', False)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_repr_calendar(self):
        """ Test the Calendar string representation function. """
        self.test_init_calendar()
        obj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(obj, None)
        self.assertEqual(str(obj), '<Calendar(\'test_calendar\')>')

    def test_get_calendar(self):
        """ Test the query of a calendar by its name. """
        self.test_init_calendar()
        obj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.calendar_name, 'test_calendar')
        self.assertEqual(obj.calendar_description, 'This is a test calendar')
        self.assertEqual(obj.calendar_manager_group, 'fi-apprentice')

    def test_get_calendar_inexistant(self):
        """ Test by_id query of a non-existant Calendar. """
        self.test_init_calendar()
        obj = model.Calendar.by_id(self.session, 'unknonwn')
        self.assertEqual(obj, None)

    def test_get_manager_groups(self):
        """ Test the Calendar get_manager_groups function. """
        self.test_init_calendar()
        obj = model.Calendar.get_manager_groups(self.session, 'test_calendar')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj, ['fi-apprentice'])

    def test_get_manager_groups_inexistant_calendar(self):
        """ Test the Calendar get_manager_groups function for a non
        existant Calendar.
        """
        self.test_init_calendar()
        obj = model.Calendar.get_manager_groups(self.session, 'unknown')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj, [])

    def test_get_all_calendar(self):
        """ Test the Calendar get_all function. """
        self.test_init_calendar()
        obj = model.Calendar.get_all(self.session)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0].calendar_name, 'test_calendar')
        self.assertEqual(obj[1].calendar_name, 'test_calendar2')

    def test_get_all_calendar_empty_db(self):
        """ Test the Calendar get_all function when the DB is empty. """
        obj = model.Calendar.get_all(self.session)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 0)
        self.assertEqual(obj, [])

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Calendartests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
