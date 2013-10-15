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

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from fedocal.fedocallib import model
from tests import Modeltests


class Calendartests(Modeltests):
    """ Calendar tests. """

    def test_init_calendar(self):
        """ Test the Calendar init function. """
        obj = model.Calendar(
            calendar_name='test_calendar',
            calendar_contact='test@example.com',
            calendar_description='This is a test calendar',
            calendar_editor_group='fi-apprentice',
            calendar_admin_group='infrastructure-main',
            calendar_multiple_meetings=False)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = model.Calendar(
            calendar_name='test_calendar2',
            calendar_contact='test2@example.com',
            calendar_description='This is another test calendar',
            calendar_editor_group='packager',
            calendar_multiple_meetings=True)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = model.Calendar(
            calendar_name='test_calendar3',
            calendar_contact='test3@example.com',
            calendar_description='This is the third test calendar',
            calendar_editor_group='packager',
            calendar_multiple_meetings=True)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = model.Calendar(
            calendar_name='test_calendar4',
            calendar_contact='test4@example.com',
            calendar_description='This is yet another test calendar',
            calendar_editor_group='packager',
            calendar_multiple_meetings=True,
            calendar_regional_meetings=True)
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
        self.assertEqual(obj.calendar_editor_group, 'fi-apprentice')
        self.assertEqual(obj.calendar_admin_group, 'infrastructure-main')

    def test_get_calendar_inexistant(self):
        """ Test by_id query of a non-existant Calendar. """
        self.test_init_calendar()
        obj = model.Calendar.by_id(self.session, 'unknonwn')
        self.assertEqual(obj, None)

    def test_get_editor_groups(self):
        """ Test the Calendar get_editor_groups function. """
        self.test_init_calendar()
        obj = model.Calendar.get_editor_groups(self.session, 'test_calendar')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj, ['fi-apprentice'])

    def test_get_admin_groups(self):
        """ Test the Calendar get_admin_groups function. """
        self.test_init_calendar()
        obj = model.Calendar.get_admin_groups(self.session, 'test_calendar')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj, ['infrastructure-main'])

    # pylint: disable=C0103
    def test_get_editor_groups_inexistant_calendar(self):
        """ Test the Calendar get_editor_groups function for a non
        existant Calendar.
        """
        self.test_init_calendar()
        obj = model.Calendar.get_editor_groups(self.session, 'unknown')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj, [])

    # pylint: disable=C0103
    def test_get_admin_groups_inexistant_calendar(self):
        """ Test the Calendar get_admin_groups function for a non
        existant Calendar.
        """
        self.test_init_calendar()
        obj = model.Calendar.get_admin_groups(self.session, 'unknown')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj, [])

    # pylint: disable=C0103
    def test_get_admin_groups_no_admin_set(self):
        """ Test the Calendar get_admin_groups function for a non
        existant Calendar.
        """
        self.test_init_calendar()
        obj = model.Calendar.get_admin_groups(self.session, 'test_calendar3')
        self.assertNotEqual(obj, None)
        self.assertEqual(obj, [])

    def test_get_all_calendar(self):
        """ Test the Calendar get_all function. """
        self.test_init_calendar()
        obj = model.Calendar.get_all(self.session)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 4)
        self.assertEqual(obj[0].calendar_name, 'test_calendar')
        self.assertEqual(obj[1].calendar_name, 'test_calendar2')
        self.assertEqual(obj[2].calendar_name, 'test_calendar3')
        self.assertEqual(obj[3].calendar_name, 'test_calendar4')

    def test_get_all_calendar_empty_db(self):
        """ Test the Calendar get_all function when the DB is empty. """
        obj = model.Calendar.get_all(self.session)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 0)
        self.assertEqual(obj, [])

    def test_delete(self):
        """ Test the Calendar.delete method. """
        self.test_init_calendar()
        obj = model.Calendar.get_all(self.session)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 4)
        obj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(obj, None)

        obj.delete(self.session)
        self.session.commit()

        obj = model.Calendar.get_all(self.session)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 3)
        obj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertEqual(obj, None)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Calendartests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
