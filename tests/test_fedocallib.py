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

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import unittest
import sys
import os
import re

from datetime import date
from datetime import time
from datetime import datetime
from datetime import timedelta
from dateutil.relativedelta import relativedelta

from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedocal.fedocallib as fedocallib
from fedocal.fedocallib import model
from fedocal.fedocallib.exceptions import UserNotAllowed, InvalidMeeting
from tests import Modeltests, TODAY, FakeUser


# pylint: disable=R0904
class Fedocallibtests(Modeltests):
    """ Fedocallib tests. """

    session = None

    def __setup_calendar(self):
        """ Set up basic calendar information. """
        from test_calendar import Calendartests
        cal = Calendartests('test_init_calendar')
        cal.session = self.session
        cal.test_init_calendar()

    def __setup_meeting(self):
        """ Set up basic calendar information and add some meetings in
        them. """
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
        self.assertEqual(len(calendars), 4)
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
        self.assertEqual(len(week.meetings), 3)
        self.assertEqual(week.meetings[0].meeting_name,
            'Fedora-fr-test-meeting')
        self.assertEqual(week.meetings[0].meeting_information,
            'This is a test meeting')
        self.assertEqual(week.meetings[0].meeting_name,
            'Fedora-fr-test-meeting')
        self.assertEqual(week.meetings[0].meeting_information,
            'This is a test meeting')
        self.assertEqual(week.meetings[1].meeting_name,
            'Another test meeting2')
        self.assertEqual(week.meetings[1].meeting_information,
            'This is a test meeting with recursion2')

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
        expectdays = [date(2012, 10, 1), date(2012, 10, 2),
            date(2012, 10, 3), date(2012, 10, 4), date(2012, 10, 5),
            date(2012, 10, 6), date(2012, 10, 7)]
        days = fedocallib.get_week_days(2012, 10, 3)
        self.assertNotEqual(days, None)
        self.assertEqual(days, expectdays)

    # pylint: disable=R0912
    def test_get_meetings(self):
        """ Test the get_meetings function. """
        self.__setup_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_meetings(self.session, calendar)
        self.assertNotEqual(meetings, None)
        cnt = 0
        for meeting in meetings['20h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(meet.meeting_name,
                        'Fedora-fr-test-meeting')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        self.assertEqual(meetings['15h00'][0], None)

        new_day = TODAY + timedelta(days=10)
        meetings = fedocallib.get_meetings(self.session, calendar,
            new_day.year, new_day.month, new_day.day)
        self.assertNotEqual(meetings, None)
        cnt = 0
        for meeting in meetings['14h30']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(meet.meeting_name, 'test-meeting2')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['15h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(meet.meeting_name, 'test-meeting2')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['02h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(meet.meeting_name,
                        'Another test meeting')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        self.assertEqual(meetings['19h00'][0], None)

        new_day = TODAY + timedelta(days=20)
        meetings = fedocallib.get_meetings(self.session, calendar,
            new_day.year, new_day.month, new_day.day)
        self.assertNotEqual(meetings, None)
        cnt = 0
        for meeting in meetings['23h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(meet.meeting_name,
                        'test-meeting23h59')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)

    # pylint: disable=C0103
    def test_get_meetings_with_multiple_same_time(self):
        """ Test the get_meetings function when there are several
        meetings at the same time. """
        self.__setup_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar4')
        meetings = fedocallib.get_meetings(self.session, calendar)
        cnt = 0
        for meeting in meetings['14h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertTrue(meet.meeting_name in
                        ['test-meeting-st-1', 'test-meeting-st-2'])
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['15h00']:
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
        meeting_time = datetime.utcnow() + timedelta(hours=1)
        self.assertTrue(fedocallib.is_date_in_future(meeting_date,
            meeting_time))

        meeting_time = datetime.utcnow() - timedelta(hours=1)
        self.assertFalse(fedocallib.is_date_in_future(meeting_time.date(),
            meeting_time))

        meeting_date = date.today() + timedelta(days=1)
        meeting_time = datetime.utcnow()
        self.assertTrue(fedocallib.is_date_in_future(meeting_date,
            meeting_time))

        meeting_date = date.today() - timedelta(days=2)
        self.assertFalse(fedocallib.is_date_in_future(meeting_date,
            meeting_time))

    def test_get_past_meeting_of_user(self):
        """ Test the get_past_meeting_of_user function. """
        self.__setup_meeting()
        meetings = fedocallib.get_past_meeting_of_user(self.session,
            'pingou', from_date=TODAY - timedelta(days=100))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        obj = model.Meeting(
            meeting_name='A past test meeting',
            meeting_manager='pingou',
            meeting_date=TODAY - timedelta(days=110),
            meeting_date_end=TODAY - timedelta(days=110),
            meeting_time_start=time(12, 00),
            meeting_time_stop=time(13, 00),
            meeting_information='This is a past test meeting',
            calendar_name='test_calendar')
        obj.save(self.session)
        self.session.commit()
        meetings = fedocallib.get_past_meeting_of_user(self.session,
            'pingou', from_date=TODAY - timedelta(days=100))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name, 'A past test meeting')
        self.assertEqual(meetings[0].meeting_information,
            'This is a past test meeting')

    # pylint: disable=C0103
    def test_get_future_single_meeting_of_user(self):
        """ Test the get_future_single_meeting_of_user function. """
        self.__setup_meeting()
        meetings = fedocallib.get_future_single_meeting_of_user(self.session,
            'pingou,', from_date=TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 4)
        self.assertEqual(meetings[0].meeting_name,
            'Fedora-fr-test-meeting')
        self.assertEqual(meetings[0].meeting_information,
            'This is a test meeting')
        self.assertEqual(meetings[1].meeting_name, 'test-meeting2')
        self.assertEqual(meetings[1].meeting_information,
            'This is another test meeting')
        self.assertEqual(meetings[2].meeting_name,
            'Test meeting with reminder')
        self.assertEqual(meetings[2].meeting_information,
            'This is a test meeting with reminder')

    # pylint: disable=C0103
    def test_get_future_single_meeting_of_user_empty(self):
        """ Test the get_future_single_meeting_of_user function on a
        empty meeting table. """
        self.__setup_calendar()
        meetings = fedocallib.get_future_single_meeting_of_user(
            self.session, 'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    # pylint: disable=C0103
    def test_get_future_regular_meeting_of_user(self):
        """ Test the get_future_regular_meeting_of_user function. """
        self.__setup_meeting()
        meetings = fedocallib.get_future_regular_meeting_of_user(
            self.session, 'pingou', from_date=TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 5)
        self.assertEqual(meetings[0].meeting_name,
            'Another past test meeting')
        self.assertEqual(meetings[0].meeting_information,
            'This is a past meeting with recursion')
        self.assertEqual(meetings[1].meeting_name,
            'Another test meeting2')
        self.assertEqual(meetings[1].meeting_information,
            'This is a test meeting with recursion2')
        self.assertEqual(meetings[2].meeting_name,
            'Another test meeting')
        self.assertEqual(meetings[2].meeting_information,
            'This is a test meeting with recursion')
        self.assertEqual(meetings[3].meeting_name,
            'Full-day meeting with recursion')
        self.assertEqual(meetings[3].meeting_information,
            'Full day meeting with recursion')
        self.assertEqual(meetings[4].meeting_name,
            'Test meeting with reminder and recursion')
        self.assertEqual(meetings[4].meeting_information,
            'This is a test meeting with recursion and reminder')

    # pylint: disable=C0103
    def test_get_future_regular_meeting_of_user_empty(self):
        """ Test the get_future_regular_meeting_of_user function on a
        empty meeting table. """
        self.__setup_calendar()
        meetings = fedocallib.get_future_regular_meeting_of_user(self.session,
            'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_delete_recursive_meeting(self):
        """ Test the delete_recursive_meeting function. """
        self.__setup_meeting()
        meeting = model.Meeting.by_id(self.session, 8)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Another test meeting2')
        self.assertEqual(meeting.recursion_ends,
            TODAY + timedelta(days=90))

        fedocallib.delete_recursive_meeting(self.session, meeting)

        meeting = model.Meeting.by_id(self.session, 8)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Another test meeting2')
        self.assertEqual(meeting.recursion_ends, date.today())

    # pylint: disable=C0103
    def test_delete_recursive_meeting_past(self):
        """ Test the delete_recursive_meeting for past end_datefunction.
        """
        self.__setup_meeting()
        meeting = model.Meeting.by_id(self.session, 4)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'test-meeting3')
        self.assertEqual(meeting.recursion_ends,
            TODAY - timedelta(days=7))

        fedocallib.delete_recursive_meeting(self.session, meeting)

        meeting = model.Meeting.by_id(self.session, 4)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'test-meeting3')
        self.assertEqual(meeting.recursion_ends,
            TODAY - timedelta(days=7))

    def test_agenda_is_free(self):
        """ Test the agenda_is_free function. """
        self.__setup_meeting()
        cal = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertTrue(fedocallib.agenda_is_free(self.session, cal,
            TODAY, time(10, 0), time(11, 0)))
        self.assertFalse(fedocallib.agenda_is_free(self.session, cal,
            TODAY, time(20, 0), time(21, 0)))

    def test_agenda_is_free_empty(self):
        """ Test the agenda_is_free function. """
        self.__setup_calendar()
        cal = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertTrue(fedocallib.agenda_is_free(self.session, cal,
            TODAY, time(10, 0), time(11, 0)))

    # pylint: disable=C0103
    def test_is_user_managing_in_calendar(self):
        """ Test the is_user_managing_in_calendar function. """
        self.__setup_calendar()
        user = FakeUser(['packager', 'fi-apprentice'])
        self.assertTrue(fedocallib.is_user_managing_in_calendar(
            self.session, 'test_calendar', user))

        user = FakeUser(['packager', 'infrastructure'])
        self.assertFalse(fedocallib.is_user_managing_in_calendar(
            self.session, 'test_calendar', user))

        calendar = model.Calendar(
            calendar_name='test_calendar30',
            calendar_contact='test30@example.com',
            calendar_description='This is a test calendar30',
            calendar_manager_group='')
        calendar.save(self.session)
        self.session.commit()

        user = FakeUser(['packager', 'infrastructure'])
        self.assertTrue(fedocallib.is_user_managing_in_calendar(
            self.session, 'test_calendar30', user))
        user = FakeUser([])
        self.assertTrue(fedocallib.is_user_managing_in_calendar(
            self.session, 'test_calendar30', user))

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
            meeting_name='Test meeting with reminder',
            meeting_manager='pingou',
            meeting_date=time_start.date(),
            meeting_date_end=time_start.date(),
            meeting_time_start=time_start.time(),
            meeting_time_stop=time_end.time(),
            meeting_information='This is a test meeting with reminder',
            calendar_name='test_calendar',
            reminder_id=remobj.reminder_id)
        meeting.save(self.session)
        self.session.commit()

        meetings = fedocallib.retrieve_meeting_to_remind(self.session)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(meetings[0].meeting_name,
            'Test meeting with reminder')
        self.assertEqual(meetings[0].meeting_information,
            'This is a test meeting with reminder')

    # pylint: disable=C0103
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
            self.session, 'pingou,', from_date=TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 4)

        fedocallib.add_meetings_to_vcal(calendar, meetings)
        cnt = 0
        for event in calendar.vevent_list:
            self.assertTrue(event.summary.value in [
                'Fedora-fr-test-meeting', 'Test meeting with reminder',
                'test-meeting2', 'Full-day meeting'])
            self.assertTrue(event.organizer.value in [
                'pingou,', 'pingou, shaiton,'])
            cnt = cnt + 1
        self.assertEqual(cnt, len(meetings))

    def test_get_meetings_by_date(self):
        """ Test the get_meetings_by_date function. """
        self.__setup_meeting()
        meetings = fedocallib.get_meetings_by_date(self.session,
            'test_calendar',
            TODAY + timedelta(days=10),
            TODAY + timedelta(days=12)
            )
        self.assertEqual(len(meetings), 4)
        for meeting in meetings:
            self.assertTrue(meeting.meeting_name in ['test-meeting2',
                'Another test meeting', 'Test meeting with reminder',
                'Test meeting with reminder and recursion'])
            self.assertEqual(meeting.meeting_manager, 'pingou,')

    # pylint: disable=C0103
    def test_get_meetings_by_date_and_region(self):
        """ Test the get_meetings_by_date_and_region function. """
        self.__setup_meeting()
        obj = fedocallib.get_meetings_by_date_and_region(
            self.session,
            'test_calendar4',
            TODAY,
            TODAY + timedelta(days=2),
            'EMEA'
            )

        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].meeting_name, 'test-meeting-st-2')
        self.assertEqual(obj[0].meeting_manager, 'test,')
        self.assertEqual(obj[0].calendar.calendar_name, 'test_calendar4')
        self.assertEqual(obj[0].meeting_information,
            'This is a second test meeting at the same time')
        self.assertEqual(obj[0].reminder, None)

        obj = fedocallib.get_meetings_by_date_and_region(
            self.session,
            'test_calendar4',
            TODAY,
            TODAY + timedelta(days=2),
            'NA'
            )
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 1)
        self.assertEqual(obj[0].meeting_name, 'test-meeting-st-1')
        self.assertEqual(obj[0].meeting_manager, 'test,')
        self.assertEqual(obj[0].calendar.calendar_name, 'test_calendar4')
        self.assertEqual(obj[0].meeting_information,
            'This is a test meeting at the same time')
        self.assertEqual(obj[0].reminder, None)

        obj = fedocallib.get_meetings_by_date_and_region(
            self.session,
            'test_calendar4',
            TODAY,
            TODAY + timedelta(days=2),
            'APAC'
            )
        self.assertNotEqual(obj, None)
        self.assertEqual(len(obj), 0)

    def test_get_html_monthly_cal(self):
        """ Test the get_html_monthly_call function. """
        today = date.today()
        output = fedocallib.get_html_monthly_cal(today.day, today.month,
            today.year)
        # Check today css class
        self.assertTrue('class="%s today">%s' % (
                today.strftime('%a').lower(),
                today.day) in output)
        # Check the month
        self.assertTrue('class="month"> %s </th>' % (
                today.strftime('%B %Y')) in output)
        # Check the current_week css class
        self.assertNotEqual(re.match('<tr class="current_week">.*'
            '<td>%s</td>' % (today.day), output), [])

    def test_get_week_day_index(self):
        """ Test the get_week_day_index function. """
        output = fedocallib.get_week_day_index(year=2012, month=11,
            day=6)
        self.assertEqual(output, 2)
        today = date.today()
        output = fedocallib.get_week_day_index()
        self.assertEqual(output, today.isoweekday())

    def test_get_by_date_empty(self):
        """ Test the get_by_date function. """
        self.__setup_calendar()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)
        output = fedocallib.get_by_date(self.session, calendarobj, TODAY,
            TODAY + relativedelta(years=+1))
        self.assertNotEqual(output, None)
        self.assertEqual(len(output), 0)
        self.assertEqual(output, [])

    def test_get_by_date(self):
        """ Test the get_by_date function. """
        self.__setup_meeting()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)
        output = fedocallib.get_by_date(self.session, calendarobj, TODAY,
            TODAY + relativedelta(years=+1))
        self.assertNotEqual(output, None)
        self.assertEqual(len(output), 43)

    # pylint: disable=R0915
    def test_add_meeting_fail(self):
        """ Test the add_meeting function. """
        self.__setup_calendar()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)

        self.assertRaises(AttributeError, fedocallib.add_meeting,
            self.session, calendarobj, None,
            None, None,
            time(9, 0), time(10, 0), None,
            None, None, None,
            None, None,
            None, None)

        fasuser = FakeUser(['test'])
        self.assertRaises(UserNotAllowed, fedocallib.add_meeting,
            self.session, calendarobj, fasuser,
            None, None,
            time(9, 0), time(10, 0), None,
            None, None, None,
            None, None,
            None, None)

        fasuser = FakeUser(['fi-apprentice'])
        self.assertRaises(TypeError, fedocallib.add_meeting,
            self.session, calendarobj, fasuser,
            None, None,
            time(9, 0), time(10, 0), None,
            None, None, None,
            None, None,
            None, None)

        self.assertRaises(InvalidMeeting, fedocallib.add_meeting,
            self.session, calendarobj, fasuser,
            None, TODAY - timedelta(days=4),
            time(9, 0), time(10, 0), None,
            None, None, None,
            None, None,
            None, None)

        self.assertRaises(IntegrityError, fedocallib.add_meeting,
            self.session, calendarobj, fasuser,
            None, date.today() + timedelta(days=1),
            time(9, 0), time(10, 0), None,
            None, None, 'Europe/Paris',
            None, None,
            None, None)
        self.session.rollback()

        self.assertRaises(InvalidMeeting, fedocallib.add_meeting,
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(10, 0), time(9, 0), None,
            None, None, 'Europe/Paris',
            None, None,
            None, None)
        self.session.rollback()

    # pylint: disable=R0915
    def test_add_meeting(self):
        """ Test the add_meeting function. """
        self.__setup_calendar()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)
        fasuser = FakeUser(['fi-apprentice'])

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(9, 0), time(10, 0), None,
            None, None, 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertTrue(meeting.meeting_time_start.strftime('%H') == '07' or
            meeting.meeting_time_start.strftime('%H') == '08')
        self.assertTrue(meeting.meeting_time_stop.strftime('%H') == '08' or
            meeting.meeting_time_stop.strftime('%H') == '09')
        self.session.flush()

        self.assertRaises(InvalidMeeting, fedocallib.add_meeting,
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(9, 0), time(10, 0), None,
            None, None, 'Europe/Paris',
            None, None,
            None, None)

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(10, 0), time(11, 0), 'pingou',
            None, None, 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 2)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,pingou')
        self.assertTrue(meeting.meeting_time_start.strftime('%H') == '08' or
            meeting.meeting_time_start.strftime('%H') == '09')
        self.assertTrue(meeting.meeting_time_stop.strftime('%H') == '09' or
            meeting.meeting_time_stop.strftime('%H') == '10')
        self.session.commit()

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(11, 00), time(12, 0), 'pingou',
            'Information', None, 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 3)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,pingou')
        self.assertEqual(meeting.meeting_information, 'Information')

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(13, 0), time(14, 0), 'pingou',
            'Information', 'EMEA', 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 4)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,pingou')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_region, None)

        calendarobj = model.Calendar.by_id(self.session, 'test_calendar4')
        fasuser = FakeUser(['packager'])

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(9, 0), time(10, 0), 'pingou',
            'Information', 'EMEA', 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 5)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,pingou')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_region, 'EMEA')

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(10, 0), time(11, 0), 'pingou',
            'Information', 'EMEA', 'Europe/Paris',
            7, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 6)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,pingou')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_region, 'EMEA')
        self.assertEqual(meeting.recursion_frequency, 7)

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(11, 0), time(12, 0), 'pingou',
            'Information', 'EMEA', 'Europe/Paris',
            7, date.today() + timedelta(days=28),
            None, None)
        meeting = model.Meeting.by_id(self.session, 7)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,pingou')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_region, 'EMEA')
        self.assertEqual(meeting.recursion_frequency, 7)
        self.assertEqual((meeting.recursion_ends - date.today()).days,
            28)

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(12, 0), time(13, 0), 'pingou',
            'Information', 'EMEA', 'Europe/Paris',
            7, date.today() + timedelta(days=28),
            '', 'test@example.org')
        meeting = model.Meeting.by_id(self.session, 8)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,pingou')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_region, 'EMEA')
        self.assertEqual(meeting.recursion_frequency, 7)
        self.assertEqual(meeting.reminder, None)

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name', date.today() + timedelta(days=1),
            time(13, 0), time(14, 0), 'pingou',
            'Information', 'EMEA', 'Europe/Paris',
            7, date.today() + timedelta(days=28),
            'H-12', 'test@example.org')
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, 'username,pingou')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_region, 'EMEA')
        self.assertEqual(meeting.recursion_frequency, 7)
        self.assertEqual(meeting.reminder.reminder_offset, 'H-12')
        self.assertEqual(meeting.reminder.reminder_to, 'test@example.org')

        fedocallib.add_meeting(
            self.session, calendarobj, fasuser,
            'Name23h59', date.today() + timedelta(days=1),
            time(23, 0), time(23, 59), None,
            'Information', 'EMEA', 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 10)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name23h59')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_time_stop.minute, 59)

    def test_edit_meeting_fail(self):
        """ Test the edit_meeting function for when edit fails. """
        self.__setup_meeting()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)

        meeting = model.Meeting.by_id(self.session, 1)
        self.assertEqual(meeting.meeting_name, 'Fedora-fr-test-meeting')

        fasuser = FakeUser(['test'])
        self.assertRaises(UserNotAllowed, fedocallib.edit_meeting,
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1), None,
            time(23, 0), time(23, 59), None,
            'Information', 'EMEA', 'Europe/Paris',
            None, None,
            None, None)
        self.session.rollback()

        fasuser = FakeUser(['fi-apprentice'])

        self.assertRaises(InvalidMeeting, fedocallib.edit_meeting,
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited',
            date.today() - timedelta(days=2), None,
            time(23, 0), time(23, 59), None,
            'Information', 'EMEA', 'UTC',
            None, None,
            None, None)
        self.session.rollback()

        self.assertRaises(InvalidMeeting, fedocallib.edit_meeting,
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1), None,
            time(23, 0), time(21, 59), None,
            'Information', 'EMEA', 'Europe/Paris',
            None, None,
            None, None)
        self.session.rollback()

        self.assertRaises(InvalidMeeting, fedocallib.edit_meeting,
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1), date.today(),
            time(23, 0), time(23, 59), None,
            'Information', 'EMEA', 'Europe/Paris',
            None, None,
            None, None)
        self.session.rollback()

    def test_edit_meeting(self):
        """ Test the edit_meeting function. """
        self.__setup_meeting()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)
        fasuser = FakeUser(['fi-apprentice'])
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertEqual(meeting.meeting_name, 'Fedora-fr-test-meeting')

        fedocallib.edit_meeting(
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1), None,
            time(23, 0), time(23, 59), None,
            'Information', 'EMEA', 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Fedora-fr-meeting_edited')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_time_stop.minute, 59)

        fedocallib.edit_meeting(
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited2',
            date.today() + timedelta(days=1), None,
            time(23, 0), time(23, 59), 'pingou',
            'Information2', 'EMEA', 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Fedora-fr-meeting_edited2')
        self.assertEqual(meeting.meeting_manager, 'username,pingou,')
        self.assertEqual(meeting.meeting_information, 'Information2')
        self.assertEqual(meeting.meeting_time_stop.minute, 59)

        fedocallib.edit_meeting(
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1), None,
            time(23, 0), time(23, 59), None,
            'Information', 'EMEA', 'Europe/Paris',
            None, None,
            'H-24', 'test@example.org')
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Fedora-fr-meeting_edited')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_time_stop.minute, 59)
        self.assertEqual(meeting.reminder.reminder_offset, 'H-24')
        self.assertEqual(meeting.reminder.reminder_to, 'test@example.org')

        fedocallib.edit_meeting(
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited2',
            date.today() + timedelta(days=1), None,
            time(22, 0), time(23, 0), None,
            'Information', 'EMEA', 'Europe/Paris',
            7, TODAY + timedelta(days=30),
            None, None)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Fedora-fr-meeting_edited2')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_time_stop.minute, 0)
        self.assertEqual(meeting.recursion_frequency, 7)
        self.assertEqual(meeting.recursion_ends, TODAY + timedelta(days=30))
        self.assertEqual(meeting.reminder, None)

        fedocallib.edit_meeting(
            self.session, meeting, calendarobj, fasuser,
            'Fedora-fr-meeting_edited2',
            date.today() + timedelta(days=1), None,
            time(21, 0), time(22, 00), None,
            'Information2', None, 'Europe/Paris',
            None, None,
            None, None)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Fedora-fr-meeting_edited2')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertEqual(meeting.meeting_information, 'Information2')
        self.assertEqual(meeting.meeting_region, None)
        self.assertEqual(meeting.recursion_frequency, None)
        self.assertEqual(meeting.recursion_ends, date(2025, 12, 31))
        self.assertEqual(meeting.reminder, None)

        meeting = model.Meeting.by_id(self.session, 9)
        fedocallib.edit_meeting(
            self.session, meeting, calendarobj, fasuser,
            'Test meeting with reminder-2',
            date.today() + timedelta(days=1), date.today() + timedelta(
                days=3),
            time(20, 0), time(21, 00), None,
            'Information2', None, 'Europe/Paris',
            None, None,
            'H-24', 'test@example.org')
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name,
            'Test meeting with reminder-2')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertEqual(meeting.meeting_information, 'Information2')
        self.assertEqual(meeting.reminder.reminder_offset, 'H-24')
        self.assertEqual(meeting.reminder.reminder_to, 'test@example.org')
        self.assertEqual(meeting.meeting_date_end, date.today() +
            timedelta(days=3))

        meeting = model.Meeting.by_id(self.session, 9)
        fedocallib.edit_meeting(
            self.session, meeting, calendarobj, fasuser,
            'Test meeting with reminder-2',
            date.today() + timedelta(days=1), date.today() + timedelta(
                days=3),
            time(23, 0), time(23, 59), None,
            'Information2', None, 'Europe/Paris',
            7, TODAY + timedelta(days=30),
            'H-24', 'test@example.org',
            edit_all_meeting=False)
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name,
            'Test meeting with reminder-2')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertEqual(meeting.meeting_information, 'Information2')
        self.assertEqual(meeting.reminder.reminder_offset, 'H-24')
        self.assertEqual(meeting.reminder.reminder_to, 'test@example.org')
        self.assertEqual(meeting.meeting_date_end, date.today() +
            timedelta(days=3))

        meeting = model.Meeting.by_id(self.session, 9)
        fedocallib.edit_meeting(
            self.session, meeting, calendarobj, fasuser,
            'Test meeting with reminder-2.3',
            date.today() + timedelta(days=1), date.today() + timedelta(
                days=2),
            time(23, 0), time(23, 59), None,
            'Information3', None, 'Europe/Paris',
            None, None,  # Recursion
            None, None,  # Reminder
            edit_all_meeting=False)
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name,
            'Test meeting with reminder-2.3')
        self.assertEqual(meeting.meeting_manager, 'username,')
        self.assertEqual(meeting.meeting_information, 'Information3')
        self.assertEqual(meeting.reminder, None)
        self.assertEqual(meeting.recursion_ends, None)
        self.assertEqual(meeting.recursion_frequency, None)
        self.assertEqual(meeting.meeting_date_end, date.today() +
            timedelta(days=2))


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Fedocallibtests)
    unittest.TextTestRunner(verbosity=2, failfast=True).run(SUITE)
