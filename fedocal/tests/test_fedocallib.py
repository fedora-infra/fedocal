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
from datetime import datetime
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedocallib
from fedocallib import model
from tests import Modeltests


class FakeUser(object):
    """ Fake user used to test the fedocallib library. """

    def __init__(self, groups):
        """ Constructor.
        :arg groups: list of the groups in which this fake user is
            supposed to be.
        """
        self.groups = groups


class Fedocallibtests(Modeltests):
    """ Fedocallib tests. """

    def __setup_calendar(self):
        from test_calendar import Calendartests
        cal = Calendartests('test_init_calendar')
        cal.session = self.session
        cal.test_init_calendar()

    def __setup_meeting(self):
        from test_meeting import Meetingtests
        meeting = Meetingtests('test_init_meeting')
        meeting.session = self.session
        meeting.test_init_meeting()

    def test_create_session(self):
        """ Test the create_session function. """
        session = fedocallib.create_session('sqlite:///:memory:')
        self.assertNotEqual(session, None)

    def test_get_calendars(self):
        """ Test the get_calendars function. """
        calendars = fedocallib.get_calendars(self.session)
        self.assertNotEqual(calendars, None)
        self.assertEqual(calendars, [])
        self.assertEqual(len(calendars), 0)

        self.__setup_calendar()
        calendars = fedocallib.get_calendars(self.session)
        self.assertNotEqual(calendars, None)
        self.assertEqual(len(calendars), 3)
        self.assertEqual(calendars[0].calendar_name, 'test_calendar')
        self.assertEqual(calendars[0].calendar_manager_group,
            'fi-apprentice')
        self.assertEqual(calendars[1].calendar_name, 'test_calendar2')
        self.assertEqual(calendars[1].calendar_manager_group,
            'packager')

    def test_get_start_week(self):
        """ Test the get_start_week function. """
        expectday = date(2012, 10, 1)
        day = fedocallib.get_start_week(2012, 10, 7)
        self.assertNotEqual(day, None)
        self.assertEqual(day, expectday)

    def test_get_stop_week(self):
        """ Test the get_stop_week function. """
        expectday = date(2012, 10, 7)
        day = fedocallib.get_stop_week(2012, 10, 1)
        self.assertNotEqual(day, None)
        self.assertEqual(day, expectday)

    def test_get_next_week(self):
        """ Test the get_next_week function. """
        expectday = date(2012, 10, 8)
        day = fedocallib.get_next_week(2012, 10, 1)
        self.assertNotEqual(day, None)
        self.assertEqual(day, expectday)

    def test_get_previous_week(self):
        """ Test the get_previous_week function. """
        expectday = date(2012, 10, 1)
        day = fedocallib.get_previous_week(2012, 10, 8)
        self.assertNotEqual(day, None)
        self.assertEqual(day, expectday)

    def test_get_week(self):
        """ Test the get_week function. """
        self.__setup_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        week = fedocallib.get_week(self.session, calendar)
        self.assertNotEqual(week, None)
        self.assertEqual(week.calendar.calendar_name, 'test_calendar')
        self.assertNotEqual(week.meetings, None)
        self.assertEqual(len(week.meetings), 2)
        self.assertEqual(week.meetings[1].meeting_name,
            'Another test meeting2')
        self.assertEqual(week.meetings[1].meeting_information,
            'This is a test meeting with recursion2')
        self.assertEqual(week.meetings[0].meeting_name,
            'Fedora-fr-test-meeting')
        self.assertEqual(week.meetings[0].meeting_information,
            'This is a test meeting')

    def test_get_week_empty(self):
        """ Test the get_week function with no meetings. """
        self.__setup_calendar()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        week = fedocallib.get_week(self.session, calendar)
        self.assertNotEqual(week, None)
        self.assertEqual(week.calendar.calendar_name, 'test_calendar')
        self.assertNotEqual(week.meetings, None)
        self.assertEqual(week.meetings, [])

    def test_get_week_days(self):
        """ Test the get_week_days function. """
        expectdays = ['Monday 1', 'Tuesday 2', 'Wednesday 3',
            'Thursday 4', 'Friday 5', 'Saturday 6', 'Sunday 7']
        days = fedocallib.get_week_days(2012, 10, 3)
        self.assertNotEqual(days, None)
        self.assertEqual(days, expectdays)

    def test_get_meetings(self):
        """ Test the get_meetings function. """
        self.__setup_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_meetings(self.session, calendar)
        self.assertNotEqual(meetings, None)
        cnt = 0
        for meeting in meetings['19:20']:
            if meeting is not None:
                for meet in meeting:
                    self.assertTrue(meet.meeting_name in
                        ['Fedora-fr-test-meeting',
                            'Another test meeting2'])
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        self.assertEqual(meetings['15:16'][0], None)

        new_day = date.today() + timedelta(days=10)
        meetings = fedocallib.get_meetings(self.session, calendar,
            new_day.year, new_day.month, new_day.day)
        self.assertNotEqual(meetings, None)
        cnt = 0
        for meeting in meetings['14:15']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(meet.meeting_name, 'test-meeting2')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['15:16']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(meet.meeting_name, 'test-meeting2')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['02:03']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(meet.meeting_name,
                    'Another test meeting')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        self.assertEqual(meetings['19:20'][0], None)

    def test_get_meetings_with_multiple_same_time(self):
        """ Test the get_meetings function when there are several
        meetings at the same time. """
        self.__setup_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar4')
        meetings = fedocallib.get_meetings(self.session, calendar)
        cnt = 0
        for meeting in meetings['14:15']:
            if meeting is not None:
                for meet in meeting:
                    self.assertTrue(meet.meeting_name in
                        ['test-meeting-st-1', 'test-meeting-st-2'])
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['15:16']:
            if meeting is not None:
                for meet in meeting:
                    self.assertTrue(meet.meeting_name in
                        ['test-meeting-st-1', 'test-meeting-st-2'])
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)

    def test_is_date_in_future(self):
        """ Test the is_date_in_future function. """
        meeting_date = date.today()
        meeting_time = datetime.utcnow().hour + 1
        self.assertTrue(fedocallib.is_date_in_future(meeting_date,
            meeting_time))

        meeting_time = datetime.utcnow().hour - 1
        self.assertFalse(fedocallib.is_date_in_future(meeting_date,
            meeting_time))

        meeting_date = date.today() + timedelta(days=1)
        meeting_time = datetime.utcnow().hour
        self.assertTrue(fedocallib.is_date_in_future(meeting_date,
            meeting_time))

        meeting_date = date.today() - timedelta(days=1)
        self.assertFalse(fedocallib.is_date_in_future(meeting_date,
            meeting_time))

    def test_get_past_meeting_of_user(self):
        """ Test the get_past_meeting_of_user function. """
        self.__setup_meeting()
        meetings = fedocallib.get_past_meeting_of_user(self.session,
            'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        obj = model.Meeting(
            'A past test meeting', 'pingou',
            date.today() - timedelta(days=1), time(12, 00), time(13, 00),
            'This is a past test meeting',
            'test_calendar', None, None)
        obj.save(self.session)
        self.session.commit()
        meetings = fedocallib.get_past_meeting_of_user(self.session,
            'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name, 'A past test meeting')
        self.assertEqual(meetings[0].meeting_information,
            'This is a past test meeting')

    def test_get_future_single_meeting_of_user(self):
        """ Test the get_future_single_meeting_of_user function. """
        self.__setup_meeting()
        meetings = fedocallib.get_future_single_meeting_of_user(self.session,
            'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 2)
        self.assertEqual(meetings[0].meeting_name, 'test-meeting2')
        self.assertEqual(meetings[0].meeting_information,
            'This is another test meeting')
        self.assertEqual(meetings[1].meeting_name,
            'Test meeting with reminder')
        self.assertEqual(meetings[1].meeting_information,
            'This is a test meeting with reminder')

    def test_get_future_single_meeting_of_user_empty(self):
        """ Test the get_future_single_meeting_of_user function on a
        empty meeting table. """
        self.__setup_calendar()
        meetings = fedocallib.get_future_single_meeting_of_user(self.session,
            'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_get_future_regular_meeting_of_user(self):
        """ Test the get_future_regular_meeting_of_user function. """
        self.__setup_meeting()
        meetings = fedocallib.get_future_regular_meeting_of_user(self.session,
            'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 2)
        self.assertEqual(meetings[0].meeting_name,
            'Another test meeting')
        self.assertEqual(meetings[0].meeting_information,
            'This is a test meeting with recursion')
        self.assertEqual(meetings[1].meeting_name,
            'Test meeting with reminder and recursion')
        self.assertEqual(meetings[1].meeting_information,
            'This is a test meeting with recursion and reminder')

    def test_get_future_regular_meeting_of_user_empty(self):
        """ Test the get_future_regular_meeting_of_user function on a
        empty meeting table. """
        self.__setup_calendar()
        meetings = fedocallib.get_future_regular_meeting_of_user(self.session,
            'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_agenda_is_free(self):
        """ Test the agenda_is_free function. """
        self.__setup_meeting()
        cal = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertTrue(fedocallib.agenda_is_free(self.session, cal,
            date.today(), 10, 11))
        self.assertFalse(fedocallib.agenda_is_free(self.session, cal,
            date.today(), 19, 20))

    def test_agenda_is_free_empty(self):
        """ Test the agenda_is_free function. """
        self.__setup_calendar()
        cal = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertTrue(fedocallib.agenda_is_free(self.session, cal,
            date.today(), 10, 11))

    def test_is_user_managing_in_calendar(self):
        """ Test the is_user_managing_in_calendar function. """
        self.__setup_calendar()
        cal = model.Calendar.by_id(self.session, 'test_calendar')
        user = FakeUser(['packager', 'fi-apprentice'])
        self.assertTrue(fedocallib.is_user_managing_in_calendar(
            self.session, 'test_calendar', user))

        user = FakeUser(['packager', 'infrastructure'])
        self.assertFalse(fedocallib.is_user_managing_in_calendar(
            self.session, 'test_calendar', user))

        calendar = model.Calendar('test_calendar3',
                    'This is a test calendar2', '')
        calendar.save(self.session)
        self.session.commit()

        user = FakeUser(['packager', 'infrastructure'])
        self.assertTrue(fedocallib.is_user_managing_in_calendar(
            self.session, 'test_calendar3', user))
        user = FakeUser([])
        self.assertTrue(fedocallib.is_user_managing_in_calendar(
            self.session, 'test_calendar3', user))

    def test_save_recursive_meeting(self):
        """ Test the save_recursive_meeting function. """
        self.__setup_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meeting = model.Meeting.by_id(self.session, 6)

        for delta_day in [7, 14, 21]:
            newdate = date.today() + timedelta(days=delta_day)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(new_meeting, [])
            self.assertEqual(len(new_meeting), 0)

        fedocallib.save_recursive_meeting(self.session, meeting)

        for delta_day in [7, 14, 21]:
            newdate = date.today() + timedelta(days=7)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 1)
            self.assertEqual(new_meeting[0].meeting_name,
                'Another test meeting2')

    def test_save_recursive_meeting_empty(self):
        """ Test the save_recursive_meeting function when
        there is no recursion attached to the meeting. """
        self.test_save_recursive_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meeting = model.Meeting.by_id(self.session, 1)

        fedocallib.save_recursive_meeting(self.session,
            meeting)

    def test_update_recursive_meeting(self):
        """ Test the update_recursive_meeting function. """
        self.test_save_recursive_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')

        newdate = date.today() + timedelta(days=21)
        meeting = model.Meeting.get_by_date(self.session, calendar,
            newdate, newdate + timedelta(days=1))[0]
        meeting.meeting_name = 'A new name'

        fedocallib.update_recursive_meeting(self.session, meeting)

        # The first three weeks are un-touched
        for delta_day in [0, 7, 14]:
            newdate = date.today() + timedelta(days=7)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 1)
            self.assertEqual(new_meeting[0].meeting_name,
                'Another test meeting2')

        # The followings week have been updated
        for delta_day in [21, 28, 35]:
            newdate = date.today() + timedelta(days=delta_day)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 1)
            self.assertEqual(new_meeting[0].meeting_name, 'A new name')

    def test_update_recursive_meeting_empty(self):
        """ Test the update_recursive_meeting function when
        there is no recursion attached to the meeting. """
        self.test_save_recursive_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meeting = model.Meeting.by_id(self.session, 1)

        fedocallib.update_recursive_meeting(self.session,
            meeting)

    def test_delete_recursive_meeting(self):
        """ Test the delete_recursive_meeting function. """
        self.test_save_recursive_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')

        newdate = date.today() + timedelta(days=21)
        meeting = model.Meeting.get_by_date(self.session, calendar,
            newdate, newdate + timedelta(days=1))[0]
        fedocallib.delete_recursive_meeting(self.session, meeting)

        # The first three weeks are un-touched
        for delta_day in [0, 7, 14]:
            newdate = date.today() + timedelta(days=7)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 1)
            self.assertEqual(new_meeting[0].meeting_name,
                'Another test meeting2')

        # The followings week have been removed
        for delta_day in [21, 28, 35]:
            newdate = date.today() + timedelta(days=delta_day)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 0)
            self.assertEqual(new_meeting, [])

    def test_delete_recursive_meeting_empty(self):
        """ Test the delete_recursive_meeting function when
        there is no recursion attached to the meeting. """
        self.test_save_recursive_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meeting = model.Meeting.by_id(self.session, 1)

        fedocallib.delete_recursive_meeting(self.session,
            meeting)

    def test_delete_recursive_meeting_after_end(self):
        """ Test the delete_recursive_meeting_after_end function. """
        self.test_save_recursive_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')

        newdate = date.today() + timedelta(days=21)
        meeting = model.Meeting.get_by_date(self.session, calendar,
            newdate, newdate + timedelta(days=1))[0]
        meeting.recursion.recursion_ends = date.today() + \
            timedelta(days=20)

        fedocallib.delete_recursive_meeting_after_end(self.session, meeting)

        # The first three weeks are un-touched
        for delta_day in [0, 7, 14]:
            newdate = date.today() + timedelta(days=7)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 1)
            self.assertEqual(new_meeting[0].meeting_name,
                'Another test meeting2')

        # The followings week have been removed
        for delta_day in [21, 28, 35]:
            newdate = date.today() + timedelta(days=delta_day)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 0)
            self.assertEqual(new_meeting, [])

    def test_add_recursive_meeting_after_end(self):
        """ Test the add_recursive_meeting_after_end function. """
        self.test_save_recursive_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')

        # The first three weeks are un-touched
        for delta_day in [0, 7, 14, 46]:
            newdate = date.today() + timedelta(days=7)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 1)
            self.assertEqual(new_meeting[0].meeting_name,
                'Another test meeting2')

        # The followings weeks do not exists yet
        for delta_day in [63, 70, 77]:
            newdate = date.today() + timedelta(days=delta_day)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 0)
            self.assertEqual(new_meeting, [])

        # Update the end date of the recursion
        newdate = date.today() + timedelta(days=21)
        meeting = model.Meeting.get_by_date(self.session, calendar,
            newdate, newdate + timedelta(days=1))[0]
        meeting.recursion.recursion_ends = date.today() + \
            timedelta(days=80)

        fedocallib.add_recursive_meeting_after_end(self.session, meeting)

        # The first three weeks are un-touched
        for delta_day in [0, 7, 14, 46]:
            newdate = date.today() + timedelta(days=7)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 1)
            self.assertEqual(new_meeting[0].meeting_name,
                'Another test meeting2')

        # The followings week have been added
        for delta_day in [63, 70, 77]:
            newdate = date.today() + timedelta(days=delta_day)
            new_meeting = model.Meeting.get_by_date(self.session, calendar,
                newdate, newdate + timedelta(days=1))
            self.assertNotEqual(new_meeting, None)
            self.assertEqual(len(new_meeting), 1)
            self.assertEqual(new_meeting[0].meeting_name,
                'Another test meeting2')

    def test_add_recursive_meeting_after_end_empty(self):
        """ Test the add_recursive_meeting_after_end function when
        there is no recursion attached to the meeting. """
        self.test_save_recursive_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meeting = model.Meeting.by_id(self.session, 1)

        fedocallib.add_recursive_meeting_after_end(self.session,
            meeting)

    def test_retrieve_meeting_to_remind(self):
        """ Test the retrieve_meeting_to_remind function. """
        self.__setup_calendar()
        remobj = model.Reminder('H-12', 'root@localhost',
            'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()
        time_start = datetime.utcnow() + timedelta(hours=12)
        time_end = datetime.utcnow() + timedelta(hours=13)
        meeting = model.Meeting(
            'Test meeting with reminder', 'pingou',
            time_start.date(),
            time(time_start.hour, 00), time(time_end.hour, 00),
            'This is a test meeting with reminder',
            'test_calendar',
            remobj.reminder_id, None)
        meeting.save(self.session)
        self.session.commit()

        meetings = fedocallib.retrieve_meeting_to_remind(self.session)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name,
            'Test meeting with reminder')
        self.assertEqual(meetings[0].meeting_information,
            'This is a test meeting with reminder')

    def test_retrieve_meeting_to_remind_empty(self):
        """ Test the retrieve_meeting_to_remind function on an empty
        meeting table. """
        self.__setup_calendar()
        meetings = fedocallib.retrieve_meeting_to_remind(self.session)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_add_meetings_to_vcal(self):
        """ Test the add_meetings_to_vcal function. """
        import vobject
        calendar = vobject.iCalendar()
        self.__setup_meeting()
        meetings = fedocallib.get_future_single_meeting_of_user(
            self.session, 'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 2)

        fedocallib.add_meetings_to_vcal(calendar, meetings)
        cnt = 0
        for event in calendar.vevent_list:
            self.assertTrue(event.summary.value in [
                'Test meeting with reminder', 'test-meeting2'])
            self.assertEqual(event.organizer.value, 'pingou')
            cnt = cnt + 1
        self.assertEqual(cnt, len(meetings))

    def test_get_meetings_by_date(self):
        """ Test the get_meetings_by_date function. """
        self.__setup_meeting()
        meetings = fedocallib.get_meetings_by_date(self.session,
            'test_calendar',
            date.today() + timedelta(days=10),
            date.today() + timedelta(days=12)
            )
        self.assertEqual(len(meetings), 3)
        for meeting in meetings:
            self.assertTrue(meeting.meeting_name in ['test-meeting2',
                'Another test meeting', 'Test meeting with reminder'])
            self.assertEqual(meeting.meeting_manager, 'pingou')

    def test_get_meetings_by_date_and_region(self):
        """ Test the get_meetings_by_date_and_region function. """
        self.__setup_meeting()
        obj = fedocallib.get_meetings_by_date_and_region(
            self.session,
            'test_calendar4',
            date.today(),
            date.today() + timedelta(days=2),
            'EMEA'
            )

        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].meeting_name, 'test-meeting-st-2')
        self.assertEqual(obj[0].meeting_manager, 'test')
        self.assertEqual(obj[0].calendar.calendar_name, 'test_calendar4')
        self.assertEqual(obj[0].meeting_information,
            'This is a second test meeting at the same time')
        self.assertEqual(obj[0].reminder, None)

        obj = fedocallib.get_meetings_by_date_and_region(
            self.session,
            'test_calendar4',
            date.today(),
            date.today() + timedelta(days=2),
            'NA'
            )
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].meeting_name, 'test-meeting-st-1')
        self.assertEqual(obj[0].meeting_manager, 'test')
        self.assertEqual(obj[0].calendar.calendar_name, 'test_calendar4')
        self.assertEqual(obj[0].meeting_information,
            'This is a test meeting at the same time')
        self.assertEqual(obj[0].reminder, None)

        obj = fedocallib.get_meetings_by_date_and_region(
            self.session,
            'test_calendar4',
            date.today(),
            date.today() + timedelta(days=2),
            'APAC'
            )
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 0)

    def test_get_html_monthly_cal(self):
        """ Test the get_html_monthly_call function. """
        output = fedocallib.get_html_monthly_cal()
        self.assertTrue(output.startswith('<table border="0" '\
        'cellpadding="0" cellspacing="0" class="month">\n<tr><th '\
        'colspan="7" class="month">'))
        self.assertTrue(output.endswith('<td class="noday">&nbsp;</td>'\
        '<td class="noday">&nbsp;</td></tr>\n</table>\n'))


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Fedocallibtests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
