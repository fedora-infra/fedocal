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
from test_calendar import Calendartests


class Meetingtests(Modeltests):
    """ Meeting tests. """

    def test_init_meeting(self):
        """ Test the Meeting init function. """
        caltest = Calendartests('test_init_calendar')
        caltest.session = self.session
        caltest.test_init_calendar()
        obj = model.Meeting(
            'Fedora-fr-test-meeting', 'pingou, shaiton',
            date.today(), time(19, 00), time(20, 00),
            'This is a test meeting',
            'test_calendar',
            None,
            None)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = model.Meeting(
            'test-meeting2', 'pingou',
            date.today() + timedelta(days=10), time(14, 00), time(16, 00),
            'This is another test meeting',
            'test_calendar',
            None, None)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Two meetings at the same time
        obj = model.Meeting(
            'test-meeting-st-1', 'test',
            date.today() + timedelta(days=1), time(14, 00), time(16, 00),
            'This is a test meeting at the same time',
            'test_calendar4',
            None, None, 'NA')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        obj = model.Meeting(
            'test-meeting-st-2', 'test',
            date.today() + timedelta(days=1), time(14, 00), time(16, 00),
            'This is a second test meeting at the same time',
            'test_calendar4',
            None, None, 'EMEA')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Meeting with a recursion
        recobj = model.Recursive('7', date.today() + timedelta(days=60))
        recobj.save(self.session)
        self.session.flush()
        obj = model.Meeting(
            'Another test meeting', 'pingou',
            date.today() + timedelta(days=10), time(2, 00), time(3, 00),
            'This is a test meeting with recursion',
            'test_calendar',
            None, recobj.recursion_id)
        obj.save(self.session)
        obj = model.Meeting(
            'Another test meeting2', 'pingou',
            date.today(), time(12, 00), time(13, 00),
            'This is a test meeting with recursion2',
            'test_calendar',
            None, recobj.recursion_id)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Meeting with a reminder
        remobj = model.Reminder('H-12', 'root@localhost',
            'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()
        obj = model.Meeting(
            'Test meeting with reminder', 'pingou',
            date.today() + timedelta(days=11), time(11, 00), time(12, 00),
            'This is a test meeting with reminder',
            'test_calendar',
            remobj.reminder_id, None)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Meeting with a recursion and reminder
        recobj = model.Recursive('7', date.today() + timedelta(days=60))
        recobj.save(self.session)
        self.session.flush()
        remobj = model.Reminder('H-12', 'root@localhost',
            'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()
        obj = model.Meeting(
            'Test meeting with reminder and recursion',
            'pingou',
            date.today() + timedelta(days=12),
            time(10, 00),
            time(11, 00),
            'This is a test meeting with recursion and reminder',
            'test_calendar',
            remobj.reminder_id,
            recobj.recursion_id)
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_repr_meeting(self):
        """ Test the Meeting string representation function. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertEqual(str(obj), '<Meeting(\'<Calendar(\'test_calendar\''\
            ')>\', \'Fedora-fr-test-meeting\', \'' + str(date.today()) \
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
        self.assertEqual(obj.recursion_id, obj2.recursion_id)

    def test_copy_meeting_to_existing(self):
        """ Test the Meeting copy function. """
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
            '}' % date.today()
        self.assertEqual(obj.to_json(), exp)

    def test_get_by_date(self):
        """ Test the query of a list of meetings between two dates. """
        self.test_init_meeting()
        week_day = date.today()
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
        week_day = date.today()
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

    def test_get_future_meetings_of_recursion(self):
        """ Test the Meeting get_future_meetings_of_recursion function.
        """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 5)
        self.assertNotEqual(obj, None)
        meetings = model.Meeting.get_future_meetings_of_recursion(
            self.session, obj)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name,
            'Another test meeting')
        self.assertEqual(meetings[0].meeting_information,
            'This is a test meeting with recursion')
        self.assertEqual(meetings[0].recursion_id, 1)

    def test_get_future_meetings_of_recursion_fail(self):
        """ Test the Meeting get_future_meetings_of_recursion function
        with a non-existant meeting. """
        obj = model.Meeting(
            'Fake test-meeting', 'pingou',
            date.today() + timedelta(days=90), time(19, 00), time(20, 00),
            'This is a fake test meeting', 'test_calendar', None, None)
        self.assertNotEqual(obj, None)
        meetings = model.Meeting.get_future_meetings_of_recursion(
            self.session, obj)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_last_meeting_of_recursion(self):
        """ Test the Meeting get_last_meeting_of_recursion function. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 5)
        self.assertNotEqual(obj, None)
        meeting = model.Meeting.get_last_meeting_of_recursion(
            self.session, obj)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name,
            'Another test meeting')
        self.assertEqual(meeting.meeting_information,
            'This is a test meeting with recursion')
        self.assertEqual(meeting.recursion_id, 1)

    def test_get_last_meeting_of_recursion_fail(self):
        """ Test the Meeting get_last_meeting_of_recursion function
        with a non-existant meeting. """
        obj = model.Meeting(
            'Fake test-meeting', 'pingou',
            date.today() + timedelta(days=90), time(19, 00), time(20, 00),
            'This is a fake test meeting', 'test_calendar', None, None)
        self.assertNotEqual(obj, None)
        meeting = model.Meeting.get_last_meeting_of_recursion(
            self.session, obj)
        self.assertEqual(meeting, None)

    def test_get_meetings_past_end_of_recursion(self):
        """ Test the Meeting get_meetings_past_end_of_recursion function.
        """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 5)
        self.assertNotEqual(obj, None)
        obj2 = obj.copy()
        obj2.meeting_date = date.today() + timedelta(days=90)
        obj2.save(self.session)
        self.session.flush()
        meetings = model.Meeting.get_meetings_past_end_of_recursion(
            self.session, obj2)
        self.assertNotEqual(meetings, None)
        self.assertNotEqual(meetings, [])
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name, obj.meeting_name)
        self.assertEqual(meetings[0].meeting_date, obj2.meeting_date)
        self.assertEqual(meetings[0].meeting_date,
            date.today() + timedelta(days=90))

    def test_get_meetings_past_end_of_recursion_fail(self):
        """ Test the Meeting get_meetings_past_end_of_recursion function.
        """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 5)
        self.assertNotEqual(obj, None)
        meetings = model.Meeting.get_meetings_past_end_of_recursion(
            self.session, obj)
        self.assertNotEqual(meetings, None)
        self.assertEqual(meetings, [])
        self.assertEqual(len(meetings), 0)

    def test_get_meetings_of_recursion(self):
        """ Test the Meeting get_meetings_of_recursion function. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 6)
        self.assertNotEqual(obj, None)
        meetings = model.Meeting.get_meetings_of_recursion(self.session,
            obj)
        self.assertNotEqual(meetings, None)
        self.assertNotEqual(meetings, [])
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name,
            'Another test meeting')
        self.assertEqual(meetings[0].meeting_information,
            'This is a test meeting with recursion')
        self.assertEqual(meetings[0].recursion_id, 1)

    def test_get_meetings_of_recursion_fail(self):
        """ Test the Meeting get_meetings_of_recursion function. """
        self.test_init_meeting()
        obj = model.Meeting.by_id(self.session, 5)
        self.assertNotEqual(obj, None)
        meetings = model.Meeting.get_meetings_of_recursion(self.session,
            obj)
        self.assertEqual(meetings, [])
        self.assertEqual(len(meetings), 0)

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
            date.today(), time(00, 00), time(23, 59))
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
            date.today() + timedelta(days=1), time(00, 00), time(23, 59))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_past_meeting_of_user(self):
        """ Test the Meeting get_past_meeting_of_user function. """
        self.test_init_meeting()
        meetings = model.Meeting.get_past_meeting_of_user(self.session,
            'pingou', date.today() + timedelta(days=1))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 2)
        self.assertEqual(meetings[1].meeting_name,
            'Another test meeting2')
        self.assertEqual(meetings[0].meeting_name,
            'Fedora-fr-test-meeting')

        meetings = model.Meeting.get_past_meeting_of_user(self.session,
            'shaiton', date.today() + timedelta(days=1))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name,
            'Fedora-fr-test-meeting')

    def test_get_past_meeting_of_user_fail(self):
        """ Test the Meeting get_past_meeting_of_user function when
        the user does not exists or there is nothing on that day. """
        self.test_init_meeting()
        meetings = model.Meeting.get_past_meeting_of_user(self.session,
            'fakeuser', date.today() + timedelta(days=1))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_past_meeting_of_user(self.session,
            'fakeuser', date.today() - timedelta(days=1))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_future_single_meeting_of_user(self):
        """ Test the Meeting get_future_single_meeting_of_user function.
        """
        self.test_init_meeting()
        meetings = model.Meeting.get_future_single_meeting_of_user(
            self.session, 'pingou', date.today())
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
            self.session, 'faikeuser', date.today())
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_future_single_meeting_of_user(
            self.session, 'pingou', date.today() + timedelta(days=100))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_future_regular_meeting_of_user(self):
        """ Test the Meeting get_future_regular_meeting_of_user function.
        """
        self.test_init_meeting()
        meetings = model.Meeting.get_future_regular_meeting_of_user(
            self.session, 'pingou', date.today())
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
            self.session, 'fakeuser', date.today())
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_future_regular_meeting_of_user(
            self.session, 'pingou', date.today() + timedelta(days=100))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_meeting_with_reminder(self):
        """ Test the Meeting get_meeting_with_reminder function. """
        self.test_init_meeting()
        meetings = model.Meeting.get_meeting_with_reminder(self.session,
            date.today() + timedelta(days=11), time(11, 00), 'H-12')
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
            date.today() + timedelta(days=11), time(11, 00), 'H-96')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_meeting_with_reminder(self.session,
            date.today() + timedelta(days=11), time(9, 00), 'H-12')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        meetings = model.Meeting.get_meeting_with_reminder(self.session,
            date.today() + timedelta(days=100), time(11, 00), 'H-12')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Meetingtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
