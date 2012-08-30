#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
 (c) 2011, 2012 - Copyright Pierre-Yves Chibon

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

from datetime import date
from datetime import time
import unittest
import sys
import os

from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.abspath('../'))

from fedocallib import model


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        self.session = model.create_tables('sqlite:///:memory:')

    def test_init_calendar(self):
        """ Test the Calendar init function. """
        obj = model.Calendar('test_calendar', 'This is a test calendar',
        'fi-apprentice')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_get_calendar(self):
        """ Test the query of a calendar by its name. """
        self.test_init_calendar()
        obj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(obj, None)
        self.assertTrue(obj.calendar_name, 'test_calendar')
        self.assertTrue(obj.calendar_description, 'This is a test calendar')
        self.assertTrue(obj.calendar_manager_group, 'fi-apprentice')

    def test_init_reminder(self):
        """ Test the Reminder init function. """
        obj = model.Reminder('H-12',
            'fi-apprentice@lists.fedoraproject.org,'\
            'ambassadors@lists.fedoraproject.org',
            'This is your friendly reminder')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_init_reminder_failed(self):
        """ Test the Reminder init function. """
        obj = model.Reminder('H-36',
            'fi-apprentice@lists.fedoraproject.org,'\
            'ambassadors@lists.fedoraproject.org',
            'This is your friendly reminder')
        obj.save(self.session)
        try:
            self.session.flush()
        except IntegrityError:
            obj = None
        self.assertEqual(obj, None)

    def test_get_reminder(self):
        """ Test the query of a reminder by its identifier. """
        self.test_init_reminder()
        obj = model.Reminder.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertTrue(obj.reminder_offset, 'H-12')
        self.assertTrue(obj.reminder_to,
            'fi-apprentice@lists.fedoraproject.org,'\
            'ambassadors@lists.fedoraproject.org')
        self.assertTrue(obj.reminder_text, 'This is your friendly reminder')

    def test_init_meeting(self):
        """ Test the Meeting init function. """
        self.test_init_calendar()
        obj = model.Meeting(
            'Fedora-fr-test-meeting',
            'pingou, shaiton',
            date(2012, 9, 3),
            date(2012, 9, 3),
            time(19,00),
            time(20,00),
            'test_calendar',
            None)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_init_meeting(self):
        """ Test the Meeting init function. """
        self.test_init_calendar()
        obj = model.Meeting(
            'Fedora-fr-test-meeting',
            'pingou, shaiton',
            date.today(),
            date.today(),
            time(19,00),
            time(20,00),
            'test_calendar',
            None)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_get_meeting(self):
        """ Test the query of a meeting by its identifier. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertTrue(obj.meeting_name, 'Fedora-fr-test-meeting')
        self.assertTrue(obj.meeting_manager, 'pingou, shaiton')
        self.assertTrue(obj.calendar.calendar_name, 'test_calendar')
        self.assertTrue(obj.calendar.calendar_description, 'This is a test calendar')
        self.assertEqual(obj.reminder, None)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
