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
from tests import Modeltests, TODAY
from test_calendar import Calendartests


class Meetingtests(Modeltests):
    """ Meeting tests. """

    def test_init_meeting(self):
        """ Test the Meeting init function. """
        caltest = Calendartests('test_init_calendar')
        caltest.session = self.session
        caltest.test_init_calendar()
        obj = model.Meeting(
            meeting_name='Fedora-fr-test-meeting',
            meeting_manager='pingou, shaiton',
            meeting_date=TODAY,
            meeting_date_end=TODAY,
            meeting_time_start=time(19, 00),
            meeting_time_stop=time(20, 00),
            meeting_information='This is a test meeting',
            calendar_name='test_calendar')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = model.Meeting(
            meeting_name='test-meeting2',
            meeting_manager='pingou',
            meeting_date=TODAY + timedelta(days=10),
            meeting_date_end=TODAY + timedelta(days=10),
            meeting_time_start=time(14, 00),
            meeting_time_stop=time(16, 00),
            meeting_information='This is another test meeting',
            calendar_name='test_calendar')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Meeting with end_recursion in the past
        obj = model.Meeting(
            meeting_name='test-meeting3',
            meeting_manager='test2',
            meeting_date=TODAY - timedelta(days=16),
            meeting_date_end=TODAY - timedelta(days=16),
            meeting_time_start=time(14, 00),
            meeting_time_stop=time(16, 00),
            meeting_information='Test meeting with past end_recursion.',
            calendar_name='test_calendar3',
            recursion_frequency=7,
            recursion_ends=TODAY - timedelta(days=7))
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Two meetings at the same time
        obj = model.Meeting(
            meeting_name='test-meeting-st-1',
            meeting_manager='test',
            meeting_date=TODAY + timedelta(days=1),
            meeting_date_end=TODAY + timedelta(days=1),
            meeting_time_start=time(14, 00),
            meeting_time_stop=time(16, 00),
            meeting_information='This is a test meeting at the same time',
            calendar_name='test_calendar4',
            meeting_region='NA')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = model.Meeting(
            meeting_name='test-meeting-st-2',
            meeting_manager='test',
            meeting_date=TODAY + timedelta(days=1),
            meeting_date_end=TODAY + timedelta(days=1),
            meeting_time_start=time(14, 00),
            meeting_time_stop=time(16, 00),
            meeting_information='This is a second test meeting at the same time',
            calendar_name='test_calendar4',
            meeting_region='EMEA')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Meeting with a recursion
        obj = model.Meeting(
            meeting_name='Another test meeting',
            meeting_manager='pingou',
            meeting_date=TODAY + timedelta(days=10),
            meeting_date_end=TODAY + timedelta(days=10),
            meeting_time_start=time(2, 00),
            meeting_time_stop=time(3, 00),
            meeting_information='This is a test meeting with recursion',
            calendar_name='test_calendar',
            recursion_frequency=7,
            recursion_ends=TODAY + timedelta(days=90))
        obj.save(self.session)
        obj = model.Meeting(
            meeting_name='Another test meeting2',
            meeting_manager='pingou',
            meeting_date=TODAY,
            meeting_date_end=TODAY,
            meeting_time_start=time(12, 00),
            meeting_time_stop=time(13, 00),
            meeting_information='This is a test meeting with recursion2',
            calendar_name='test_calendar',
            recursion_frequency=14,
            recursion_ends=TODAY + timedelta(days=90))
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Meeting with a reminder
        remobj = model.Reminder('H-12', 'root@localhost',
            'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()
        obj = model.Meeting(
            meeting_name='Test meeting with reminder',
            meeting_manager='pingou',
            meeting_date=TODAY + timedelta(days=11),
            meeting_date_end=TODAY + timedelta(days=11),
            meeting_time_start=time(11, 00),
            meeting_time_stop=time(12, 00),
            meeting_information='This is a test meeting with reminder',
            calendar_name='test_calendar',
            reminder_id=remobj.reminder_id)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Meeting with a recursion and reminder
        self.session.flush()
        remobj = model.Reminder('H-12', 'root@localhost',
            'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()
        obj = model.Meeting(
            meeting_name='Test meeting with reminder and recursion',
            meeting_manager='pingou',
            meeting_date=TODAY + timedelta(days=12),
            meeting_date_end=TODAY + timedelta(days=12),
            meeting_time_start=time(10, 00),
            meeting_time_stop=time(11, 00),
            meeting_information='This is a test meeting with recursion and reminder',
            calendar_name='test_calendar',
            reminder_id=remobj.reminder_id,
            recursion_frequency=7,
            recursion_ends=TODAY + timedelta(days=60))
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_repr_meeting(self):
        """ Test the Meeting string representation function. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertEqual(str(obj), '<Meeting(\'<Calendar(\'test_calendar\''\
            ')>\', \'Fedora-fr-test-meeting\', \'' + str(TODAY) \
            + '\')>')

    def test_delete_meeting(self):
        """ Test the Meeting delete function. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        obj.delete(self.session)
        self.session.commit()
        obj = model.Meeting.by_id(self.session, 1)
        self.assertEqual(obj, None)

    def test_copy_meeting(self):
        """ Test the Meeting copy function. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        obj2 = obj.copy()
        self.assertNotEqual(obj2, None)
        self.assertEqual(obj.meeting_name, obj2.meeting_name)
        self.assertEqual(obj.meeting_manager, obj2.meeting_manager)
        self.assertEqual(obj.meeting_date, obj2.meeting_date)
        self.assertEqual(obj.meeting_time_start, obj2.meeting_time_start)
        self.assertEqual(obj.meeting_time_stop, obj2.meeting_time_stop)
        self.assertEqual(obj.meeting_information, obj2.meeting_information)
        self.assertEqual(obj.calendar_name, obj2.calendar_name)
        self.assertEqual(obj.reminder_id, obj2.reminder_id)
        self.assertEqual(obj.meeting_region, obj2.meeting_region)
        self.assertEqual(obj.recursion_frequency, obj2.recursion_frequency)
        self.assertEqual(obj.recursion_ends, obj2.recursion_ends)

    def test_copy_meeting_to_existing(self):
        """ Test the Meeting copy existing function. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        obj2 = model.Meeting.by_id(self.session, 2)
        self.assertNotEqual(obj2, None)
        # Check that before the copy the object are different:
        self.assertNotEqual(obj.meeting_name, obj2.meeting_name)
        self.assertNotEqual(obj.meeting_manager, obj2.meeting_manager)
        self.assertNotEqual(obj.meeting_date, obj2.meeting_date)
        self.assertNotEqual(obj.meeting_time_start, obj2.meeting_time_start)
        self.assertNotEqual(obj.meeting_time_stop, obj2.meeting_time_stop)
        self.assertNotEqual(obj.meeting_information, obj2.meeting_information)
        self.assertEqual(obj.reminder_id, obj2.reminder_id)
        self.assertEqual(obj.meeting_region, obj2.meeting_region)
        self.assertEqual(obj.recursion_frequency, obj2.recursion_frequency)
        self.assertEqual(obj.recursion_ends, obj2.recursion_ends)

        obj.copy(obj2)
        # Check that after the copy the object are equal
        self.assertEqual(obj.meeting_name, obj2.meeting_name)
        self.assertEqual(obj.meeting_manager, obj2.meeting_manager)
        # The date remains not changed
        self.assertNotEqual(obj.meeting_date, obj2.meeting_date)
        self.assertEqual(obj.meeting_time_start, obj2.meeting_time_start)
        self.assertEqual(obj.meeting_time_stop, obj2.meeting_time_stop)
        # The meeting information remains also not changed
        self.assertNotEqual(obj.meeting_information, obj2.meeting_information)

    def test_get_meeting(self):
        """ Test the query of a meeting by its identifier. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.meeting_name, 'Fedora-fr-test-meeting')
        self.assertEqual(obj.meeting_manager, 'pingou, shaiton')
        self.assertEqual(obj.calendar.calendar_name, 'test_calendar')
        self.assertEqual(obj.calendar.calendar_description,
            'This is a test calendar')
        self.assertEqual(obj.reminder, None)

    def test_to_json_meeting(self):
        """ Test the to_json method a meeting. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 1)
        exp = u'{\n  '\
            '"meeting_name": "Fedora-fr-test-meeting",\n  '\
            '"meeting_manager": "pingou, shaiton",\n  '\
            '"meeting_date": "%s",\n  '\
            '"meeting_time_start": "19:00:00",\n  '\
            '"meeting_time_stop": "20:00:00",\n  '\
            '"meeting_information": "This is a test meeting",\n  '\
            '"meeting_region": "None",\n  '\
            '"calendar_name": "test_calendar"\n'\
            '}' % TODAY
        self.assertEqual(obj.to_json(), exp)

    def test_get_by_date(self):
        """ Test the query of a list of meetings between two dates. """
        self.test_init_meeting()
        week_day = TODAY
        week_start = week_day - timedelta(days=week_day.weekday())
        week_stop = week_day + timedelta(days=7)
        cal = model.Calendar.by_id(self.session, 'test_calendar')
        obj = model.Meeting.get_by_date(self.session, cal,
                week_start, week_stop)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj[0].meeting_name, 'Fedora-fr-test-meeting')
        self.assertEqual(obj[0].meeting_manager, 'pingou, shaiton')
        self.assertEqual(obj[0].calendar.calendar_name, 'test_calendar')
        self.assertEqual(obj[0].meeting_information,
            'This is a test meeting')
        self.assertEqual(obj[0].reminder, None)

        self.assertEqual(obj[1].meeting_name, 'Another test meeting2')
        self.assertEqual(obj[1].meeting_manager, 'pingou')
        self.assertEqual(obj[1].calendar.calendar_name, 'test_calendar')
        self.assertEqual(obj[1].meeting_information,
            'This is a test meeting with recursion2')
        self.assertEqual(obj[1].reminder, None)

        week_stop = week_day + timedelta(days=12)
        obj = model.Meeting.get_by_date(self.session, cal,
                week_start, week_stop)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 5)

    def test_get_by_date_and_region(self):
        """ Test the query of a list of meetings between two dates. """
        self.test_init_meeting()
        week_day = TODAY
        week_start = week_day - timedelta(days=week_day.weekday())
        week_stop = week_day + timedelta(days=2)
        cal = model.Calendar.by_id(self.session, 'test_calendar4')

        obj = model.Meeting.get_by_date_and_region(self.session, cal,
                week_start, week_stop, 'EMEA')

        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].meeting_name, 'test-meeting-st-2')
        self.assertEqual(obj[0].meeting_manager, 'test')
        self.assertEqual(obj[0].calendar.calendar_name, 'test_calendar4')
        self.assertEqual(obj[0].meeting_information,
            'This is a second test meeting at the same time')
        self.assertEqual(obj[0].reminder, None)

        obj = model.Meeting.get_by_date_and_region(self.session, cal,
                week_start, week_stop, 'NA')
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].meeting_name, 'test-meeting-st-1')
        self.assertEqual(obj[0].meeting_manager, 'test')
        self.assertEqual(obj[0].calendar.calendar_name, 'test_calendar4')
        self.assertEqual(obj[0].meeting_information,
            'This is a test meeting at the same time')
        self.assertEqual(obj[0].reminder, None)

        obj = model.Meeting.get_by_date_and_region(self.session, cal,
                week_start, week_stop, 'APAC')
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 0)

    def test_get_managers(self):
        """ Test the Meeting get_managers function. """
        self.test_init_meeting()
        obj = model.Meeting.get_managers(self.session, 2)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj, ['pingou'])
        # More than one manager
        obj = model.Meeting.get_managers(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 2)
        self.assertEqual(obj, ['pingou', 'shaiton'])

    def test_get_managers_fail(self):
        """ Test the Meeting get_managers function when the meeting
        does not exist. """
        self.test_init_meeting()
        obj = model.Meeting.get_managers(self.session, 12)
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 0)
        self.assertEqual(obj, [])

    def test_get_by_time(self):
        """ Test the Meeting get_by_time function. """
        self.test_init_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = model.Meeting.get_by_time(self.session, calendar,
            TODAY, time(00, 00), time(23, 59))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 2)
        self.assertEqual(meetings[1].meeting_name,
            'Another test meeting2')
        self.assertEqual(meetings[0].meeting_name,
            'Fedora-fr-test-meeting')

    def test_get_by_time_fail(self):
        """ Test the Meeting get_by_time function when there is nothing
        to return. """
        self.test_init_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = model.Meeting.get_by_time(self.session, calendar,
            TODAY + timedelta(days=1), time(00, 00), time(23, 59))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_past_meeting_of_user(self):
        """ Test the Meeting get_past_meeting_of_user function. """
        self.test_init_meeting()
        meetings = model.Meeting.get_past_meeting_of_user(self.session,
            'pingou', TODAY + timedelta(days=1))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 2)
        self.assertEqual(meetings[1].meeting_name,
            'Another test meeting2')
        self.assertEqual(meetings[0].meeting_name,
            'Fedora-fr-test-meeting')

        meetings = model.Meeting.get_past_meeting_of_user(self.session,
            'shaiton', TODAY + timedelta(days=1))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name,
            'Fedora-fr-test-meeting')

    def test_get_past_meeting_of_user_fail(self):
        """ Test the Meeting get_past_meeting_of_user function when
        the user does not exists or there is nothing on that day. """
        self.test_init_meeting()
        meetings = model.Meeting.get_past_meeting_of_user(self.session,
            'fakeuser', TODAY + timedelta(days=1))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_past_meeting_of_user(self.session,
            'fakeuser', TODAY - timedelta(days=1))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_future_single_meeting_of_user(self):
        """ Test the Meeting get_future_single_meeting_of_user function.
        """
        self.test_init_meeting()
        meetings = model.Meeting.get_future_single_meeting_of_user(
            self.session, 'pingou', TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 3)
        self.assertEqual(meetings[0].meeting_name,
            'Fedora-fr-test-meeting')
        self.assertEqual(meetings[1].meeting_name,
            'test-meeting2')
        self.assertEqual(meetings[2].meeting_name,
            'Test meeting with reminder')

    def test_get_future_single_meeting_of_user_fail(self):
        """ Test the Meeting get_future_single_meeting_of_user function
        when there is no such user or the date has simply nothing
        """
        self.test_init_meeting()
        meetings = model.Meeting.get_future_single_meeting_of_user(
            self.session, 'faikeuser', TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_future_single_meeting_of_user(
            self.session, 'pingou', TODAY + timedelta(days=100))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_future_regular_meeting_of_user(self):
        """ Test the Meeting get_future_regular_meeting_of_user function.
        """
        self.test_init_meeting()
        meetings = model.Meeting.get_future_regular_meeting_of_user(
            self.session, 'pingou', TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 3)
        self.assertEqual(meetings[0].meeting_name,
            'Another test meeting2')
        self.assertEqual(meetings[1].meeting_name,
            'Another test meeting')
        self.assertEqual(meetings[2].meeting_name,
            'Test meeting with reminder and recursion')

    def test_get_future_regular_meeting_of_user_fail(self):
        """ Test the Meeting get_future_regular_meeting_of_user function
        when the user does not exist or the date has simply nothing
        """
        self.test_init_meeting()
        meetings = model.Meeting.get_future_regular_meeting_of_user(
            self.session, 'fakeuser', TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_future_regular_meeting_of_user(
            self.session, 'pingou', TODAY + timedelta(days=100))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_meeting_with_reminder(self):
        """ Test the Meeting get_meeting_with_reminder function. """
        self.test_init_meeting()
        meetings = model.Meeting.get_meeting_with_reminder(self.session,
            TODAY + timedelta(days=11), time(11, 00), 'H-12')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name,
            'Test meeting with reminder')

    def test_get_meeting_with_reminder_fail(self):
        """ Test the Meeting get_meeting_with_reminder function
        when the offset is invalid or the time_start or the day have
        nothing.
        """
        self.test_init_meeting()
        meetings = model.Meeting.get_meeting_with_reminder(self.session,
            TODAY + timedelta(days=11), time(11, 00), 'H-96')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_meeting_with_reminder(self.session,
            TODAY + timedelta(days=11), time(9, 00), 'H-12')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_meeting_with_reminder(self.session,
            TODAY + timedelta(days=100), time(11, 00), 'H-12')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Meetingtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
