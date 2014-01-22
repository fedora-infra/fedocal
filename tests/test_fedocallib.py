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

import pytz

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
        self.assertEqual(len(calendars), 5)
        self.assertEqual(
            calendars[0].calendar_name, 'test_calendar')
        self.assertEqual(
            calendars[0].calendar_editor_group, 'fi-apprentice')
        self.assertEqual(
            calendars[1].calendar_name, 'test_calendar2')
        self.assertEqual(
            calendars[1].calendar_editor_group, 'packager')

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
        self.assertEqual(len(week.full_day_meetings), 1)

        self.assertEqual(
            week.meetings[0].meeting_name,
            'Another past test meeting')
        self.assertEqual(
            week.meetings[0].meeting_information,
            'This is a past meeting with recursion')

        self.assertEqual(
            week.meetings[1].meeting_name,
            'Another test meeting2')
        self.assertEqual(
            week.meetings[1].meeting_information,
            'This is a test meeting with recursion2')

        self.assertEqual(
            week.meetings[2].meeting_name,
            'Fedora-fr-test-meeting')
        self.assertEqual(
            week.meetings[2].meeting_information,
            'This is a test meeting')

        self.assertEqual(
            week.full_day_meetings[0].meeting_name,
            'Full-day meeting')
        self.assertEqual(
            week.full_day_meetings[0].meeting_manager,
            ['pingou'])
        self.assertEqual(
            week.full_day_meetings[0].meeting_information,
            'This is a full day meeting')

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
        expectdays = [
            date(2012, 10, 1), date(2012, 10, 2),
            date(2012, 10, 3), date(2012, 10, 4), date(2012, 10, 5),
            date(2012, 10, 6), date(2012, 10, 7)]
        days = fedocallib.get_week_days(2012, 10, 3)
        self.assertNotEqual(days, None)
        self.assertEqual(days, expectdays)

    # pylint: disable=R0912
    def test_format_week_meeting(self):
        """ Test the format_week_meeting function. """
        self.__setup_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar')
        week = fedocallib.get_week(self.session, calendar)
        week_start = fedocallib.get_start_week()
        tzone = 'UTC'
        meetings = fedocallib.format_week_meeting(
            week.meetings, tzone, week_start)

        self.assertNotEqual(meetings, None)
        cnt = 0
        for meeting in meetings['20h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(
                        meet.meeting_name, 'Fedora-fr-test-meeting')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        self.assertEqual(meetings['15h00'][0], None)

        new_day = TODAY + timedelta(days=10)

        week = fedocallib.get_week(
            self.session, calendar, new_day.year, new_day.month,
            new_day.day)
        week_start = fedocallib.get_start_week(
            new_day.year, new_day.month, new_day.day)
        tzone = 'UTC'
        meetings = fedocallib.format_week_meeting(
            week.meetings, tzone, week_start)

        self.assertNotEqual(meetings, None)
        cnt = 0
        for meeting in meetings['14h30']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(
                        meet.meeting_name, 'test-meeting2')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['15h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(
                        meet.meeting_name, 'test-meeting2')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['02h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(
                        meet.meeting_name, 'Another test meeting')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        self.assertEqual(meetings['19h00'][0], None)

        new_day = TODAY + timedelta(days=20)

        week = fedocallib.get_week(
            self.session, calendar, new_day.year, new_day.month,
            new_day.day)
        week_start = fedocallib.get_start_week(
            new_day.year, new_day.month, new_day.day)
        tzone = 'UTC'
        meetings = fedocallib.format_week_meeting(
            week.meetings, tzone, week_start)

        self.assertNotEqual(meetings, None)
        cnt = 0
        for meeting in meetings['23h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertEqual(
                        meet.meeting_name, 'test-meeting23h59')
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)

    # pylint: disable=C0103
    def test_format_week_meeting_with_multiple_same_time(self):
        """ Test the get_meetings function when there are several
        meetings at the same time. """
        self.__setup_meeting()
        calendar = model.Calendar.by_id(self.session, 'test_calendar4')

        week = fedocallib.get_week(self.session, calendar)
        week_start = fedocallib.get_start_week()
        tzone = 'UTC'
        meetings = fedocallib.format_week_meeting(
            week.meetings, tzone, week_start)

        cnt = 0
        for meeting in meetings['14h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertTrue(
                        meet.meeting_name in
                        ['test-meeting-st-1', 'test-meeting-st-2'])
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)
        cnt = 0
        for meeting in meetings['15h00']:
            if meeting is not None:
                for meet in meeting:
                    self.assertTrue(
                        meet.meeting_name in
                        ['test-meeting-st-1', 'test-meeting-st-2'])
            else:
                cnt = cnt + 1
        self.assertEqual(cnt, 6)

    def test_is_date_in_future(self):
        """ Test the is_date_in_future function. """
        meeting_date = datetime.utcnow().date()
        meeting_time = datetime.utcnow() + timedelta(hours=1)
        self.assertTrue(
            fedocallib.is_date_in_future(meeting_date, meeting_time))

        meeting_time = datetime.utcnow() - timedelta(hours=1)
        self.assertFalse(
            fedocallib.is_date_in_future(meeting_time.date(), meeting_time))

        meeting_date = date.today() + timedelta(days=1)
        meeting_time = datetime.utcnow()
        self.assertTrue(
            fedocallib.is_date_in_future(meeting_date, meeting_time))

        meeting_date = date.today() - timedelta(days=2)
        self.assertFalse(
            fedocallib.is_date_in_future(meeting_date, meeting_time))

    def test_get_past_meeting_of_user(self):
        """ Test the get_past_meeting_of_user function. """
        self.__setup_meeting()
        meetings = fedocallib.get_past_meeting_of_user(
            self.session, 'pingou', from_date=TODAY - timedelta(days=100))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

        obj = model.Meeting(
            meeting_name='A past test meeting',
            meeting_date=TODAY - timedelta(days=110),
            meeting_date_end=TODAY - timedelta(days=110),
            meeting_time_start=time(12, 00),
            meeting_time_stop=time(13, 00),
            meeting_information='This is a past test meeting',
            calendar_name='test_calendar')
        obj.add_manager(self.session, 'pingou')
        obj.save(self.session)
        self.session.commit()
        meetings = fedocallib.get_past_meeting_of_user(
            self.session, 'pingou', from_date=TODAY - timedelta(days=100))
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(
            meetings[0].meeting_name,
            'A past test meeting')
        self.assertEqual(
            meetings[0].meeting_information,
            'This is a past test meeting')

    # pylint: disable=C0103
    def test_get_future_single_meeting_of_user(self):
        """ Test the get_future_single_meeting_of_user function. """
        self.__setup_meeting()
        meetings = fedocallib.get_future_single_meeting_of_user(
            self.session, 'pingou', from_date=TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 4)

        self.assertEqual(
            meetings[0].meeting_name,
            'Fedora-fr-test-meeting')
        self.assertEqual(
            meetings[0].meeting_information,
            'This is a test meeting')
        self.assertEqual(
            meetings[1].meeting_name,
            'Full-day meeting')
        self.assertEqual(
            meetings[1].meeting_information,
            'This is a full day meeting')
        self.assertEqual(
            meetings[2].meeting_name,
            'test-meeting2')
        self.assertEqual(
            meetings[2].meeting_information,
            'This is another test meeting')
        self.assertEqual(
            meetings[3].meeting_name,
            'Test meeting with reminder')
        self.assertEqual(
            meetings[3].meeting_information,
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

        self.assertEqual(
            meetings[0].meeting_name,
            'Another past test meeting')
        self.assertEqual(
            meetings[0].meeting_information,
            'This is a past meeting with recursion')
        self.assertEqual(
            meetings[1].meeting_name,
            'Another test meeting2')
        self.assertEqual(
            meetings[1].meeting_information,
            'This is a test meeting with recursion2')
        self.assertEqual(
            meetings[2].meeting_name,
            'Full-day meeting with recursion')
        self.assertEqual(
            meetings[2].meeting_information,
            'Full day meeting with recursion')
        self.assertEqual(
            meetings[3].meeting_name,
            'Another test meeting')
        self.assertEqual(
            meetings[3].meeting_information,
            'This is a test meeting with recursion')
        self.assertEqual(
            meetings[4].meeting_name,
            'Test meeting with reminder and recursion')
        self.assertEqual(
            meetings[4].meeting_information,
            'This is a test meeting with recursion and reminder')

    # pylint: disable=C0103
    def test_get_future_regular_meeting_of_user_empty(self):
        """ Test the get_future_regular_meeting_of_user function on a
        empty meeting table. """
        self.__setup_calendar()
        meetings = fedocallib.get_future_regular_meeting_of_user(
            self.session, 'pingou')
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 0)
        self.assertEqual(meetings, [])

    def test_delete_recursive_meeting(self):
        """ Test the delete_recursive_meeting function. """
        self.__setup_meeting()
        meeting = model.Meeting.by_id(self.session, 8)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name, 'Another test meeting2')
        self.assertEqual(
            meeting.recursion_ends, TODAY + timedelta(days=90))

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
        self.assertEqual(
            meeting.recursion_ends, TODAY - timedelta(days=7))

        fedocallib.delete_recursive_meeting(self.session, meeting)

        meeting = model.Meeting.by_id(self.session, 4)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'test-meeting3')
        self.assertEqual(
            meeting.recursion_ends, TODAY - timedelta(days=7))

    def test_agenda_is_free(self):
        """ Test the agenda_is_free function. """
        self.__setup_meeting()
        cal = model.Calendar.by_id(self.session, 'test_calendar')

        today_dt_start = datetime(
            TODAY.year, TODAY.month, TODAY.day, 10, 0, tzinfo=pytz.utc)
        today_dt_stop = datetime(
            TODAY.year, TODAY.month, TODAY.day, 11, 0, tzinfo=pytz.utc)
        self.assertTrue(
            fedocallib.agenda_is_free(
                self.session, cal, today_dt_start, today_dt_stop))

        today_dt_start = datetime(
            TODAY.year, TODAY.month, TODAY.day, 20, 0, tzinfo=pytz.utc)
        today_dt_stop = datetime(
            TODAY.year, TODAY.month, TODAY.day, 21, 0, tzinfo=pytz.utc)
        self.assertFalse(
            fedocallib.agenda_is_free(
                self.session, cal, today_dt_start, today_dt_stop))

    def test_agenda_is_free_empty(self):
        """ Test the agenda_is_free function. """
        self.__setup_calendar()
        cal = model.Calendar.by_id(self.session, 'test_calendar')
        today_dt_start = datetime(
            TODAY.year, TODAY.month, TODAY.day, 10, 0, tzinfo=pytz.utc)
        today_dt_stop = datetime(
            TODAY.year, TODAY.month, TODAY.day, 11, 0, tzinfo=pytz.utc)
        self.assertTrue(
            fedocallib.agenda_is_free(
                self.session, cal, today_dt_start, today_dt_stop))

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
            calendar_editor_group='')
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
        remobj = model.Reminder(
            'H-12', 'root@localhost', 'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()
        time_start = datetime.utcnow() + timedelta(hours=12)
        time_end = datetime.utcnow() + timedelta(hours=13)
        meeting = model.Meeting(
            meeting_name='Test meeting with reminder',
            meeting_date=time_start.date(),
            meeting_date_end=time_start.date(),
            meeting_time_start=time_start.time(),
            meeting_time_stop=time_end.time(),
            meeting_information='This is a test meeting with reminder',
            calendar_name='test_calendar',
            reminder_id=remobj.reminder_id)
        meeting.add_manager(self.session, 'pingou')
        meeting.save(self.session)
        self.session.commit()

        meetings = fedocallib.retrieve_meeting_to_remind(self.session)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 1)
        self.assertEqual(
            meetings[0].meeting_name,
            'Test meeting with reminder')
        self.assertEqual(
            meetings[0].meeting_information,
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
            self.session, 'pingou', from_date=TODAY)
        self.assertNotEqual(meetings, None)
        self.assertEqual(len(meetings), 4)

        fedocallib.add_meetings_to_vcal(calendar, meetings)
        cnt = 0
        for event in calendar.vevent_list:
            self.assertTrue(event.summary.value in [
                'Fedora-fr-test-meeting', 'Test meeting with reminder',
                'test-meeting2', 'Full-day meeting'])
            self.assertTrue(
                event.organizer.value in
                ('pingou', 'pingou, shaiton'))
            cnt = cnt + 1
        self.assertEqual(cnt, len(meetings))

    def test_get_html_monthly_cal(self):
        """ Test the get_html_monthly_call function. """
        today = date.today()
        output = fedocallib.get_html_monthly_cal(
            today.day, today.month, today.year)
        # Check today css class
        self.assertTrue(
            'class="%s today">%s' % (
                today.strftime('%a').lower(),
                today.day) in output)
        # Check the month
        self.assertTrue(
            'class="month"> %s </th>' % (
                today.strftime('%B %Y')) in output)
        # Check the current_week css class
        self.assertNotEqual(
            re.match('<tr class="current_week">.*'
                     '<td>%s</td>' % (today.day), output), [])

    def test_get_week_day_index(self):
        """ Test the get_week_day_index function. """
        output = fedocallib.get_week_day_index(
            year=2012, month=11, day=6)
        self.assertEqual(output, 2)
        today = date.today()
        output = fedocallib.get_week_day_index()
        self.assertEqual(output, today.isoweekday())

    def test_get_by_date_empty(self):
        """ Test the get_by_date function. """
        self.__setup_calendar()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)
        output = fedocallib.get_by_date(
            self.session, calendarobj, TODAY,
            TODAY + relativedelta(years=+1))
        self.assertNotEqual(output, None)
        self.assertEqual(len(output), 0)
        self.assertEqual(output, [])

    # pylint: disable=R0915
    def test_add_meeting_fail(self):
        """ Test the add_meeting function. """
        self.__setup_calendar()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)

        self.assertRaises(
            AttributeError,
            fedocallib.add_meeting,
            session=self.session,
            calendarobj=calendarobj,
            fas_user=None,
            meeting_name=None,
            meeting_date=None,
            meeting_date_end=None,
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone=None,
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)

        fasuser = FakeUser(['test'])
        self.assertRaises(
            UserNotAllowed,
            fedocallib.add_meeting,
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name=None,
            meeting_date=None,
            meeting_date_end=None,
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone=None,
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)

        fasuser = FakeUser(['fi-apprentice'])
        # Fails due to dates being None and thus not having .year .month...
        self.assertRaises(
            AttributeError,
            fedocallib.add_meeting,
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name=None,
            meeting_date=None,
            meeting_date_end=None,
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone=None,
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)

        # Fails because the meeting name is None
        self.assertRaises(
            IntegrityError,
            fedocallib.add_meeting,
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name=None,
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        self.session.rollback()

        # Fail because stop date is earlier than start date
        self.assertRaises(
            InvalidMeeting,
            fedocallib.add_meeting,
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=2),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        self.session.rollback()

        # Fail because stop time is earlier than start time
        self.assertRaises(
            InvalidMeeting,
            fedocallib.add_meeting,
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(10, 0),
            meeting_time_stop=time(9, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        self.session.rollback()

        # Correctly insert a meeting
        mtg = fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=21),
            meeting_date_end=date.today() + timedelta(days=21),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=7,
            end_repeats=date.today() + timedelta(days=60),
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, mtg.meeting_id)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, ['username'])
        self.assertEqual(meeting.meeting_date,
                         date.today() + timedelta(days=21))

        # Correctly insert a meeting
        mtg = fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=5),
            meeting_date_end=date.today() + timedelta(days=5),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=7,
            end_repeats=date.today() + timedelta(days=60),
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, mtg.meeting_id)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Name')
        self.assertEqual(meeting.meeting_manager, ['username'])
        self.assertEqual(meeting.meeting_date,
                         date.today() + timedelta(days=5))

    # pylint: disable=R0915
    def test_add_meeting(self):
        """ Test the add_meeting function. """
        self.__setup_calendar()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)
        fasuser = FakeUser(['fi-apprentice'])

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager=None,
            meeting_information=None,
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_time_start.strftime('%H'), '09')
        self.assertEqual(
            meeting.meeting_time_stop.strftime('%H'), '10')
        self.session.flush()

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(10, 0),
            meeting_time_stop=time(11, 0),
            comanager='pingou',
            meeting_information=None,
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 2)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_time_start.strftime('%H'), '10')
        self.assertEqual(
            meeting.meeting_time_stop.strftime('%H'), '11')
        self.session.commit()

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(11, 0),
            meeting_time_stop=time(12, 0),
            comanager='pingou',
            meeting_information='Information',
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 3)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(13, 0),
            meeting_time_stop=time(14, 0),
            comanager='pingou',
            meeting_information='Information',
            meeting_location=None,
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 4)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_location,
            None)

        calendarobj = model.Calendar.by_id(self.session, 'test_calendar3')
        fasuser = FakeUser(['packager'])

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager='pingou',
            meeting_information='Information',
            meeting_location='EMEA',
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 5)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_location,
            'EMEA')

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(10, 0),
            meeting_time_stop=time(11, 0),
            comanager='pingou',
            meeting_information='Information',
            meeting_location='EMEA',
            tzone='Europe/Paris',
            frequency=7,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 6)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_location,
            'EMEA')
        self.assertEqual(
            meeting.recursion_frequency,
            7)

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(11, 0),
            meeting_time_stop=time(12, 0),
            comanager='pingou',
            meeting_information='Information',
            meeting_location='EMEA',
            tzone='Europe/Paris',
            frequency=7,
            end_repeats=date.today() + timedelta(days=28),
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 7)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_location,
            'EMEA')
        self.assertEqual(
            meeting.recursion_frequency,
            7)
        self.assertEqual(
            (meeting.recursion_ends - date.today()).days,
            28)

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(12, 0),
            meeting_time_stop=time(13, 0),
            comanager='pingou',
            meeting_information='Information',
            meeting_location='EMEA',
            tzone='Europe/Paris',
            frequency=7,
            end_repeats=date.today() + timedelta(days=28),
            remind_when='',
            remind_who='test@example.org',
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 8)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_location,
            'EMEA')
        self.assertEqual(
            meeting.recursion_frequency,
            7)
        self.assertEqual(
            meeting.reminder,
            None)

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(13, 0),
            meeting_time_stop=time(14, 0),
            comanager='pingou',
            meeting_information='Information',
            meeting_location='EMEA',
            tzone='Europe/Paris',
            frequency=7,
            end_repeats=date.today() + timedelta(days=28),
            remind_when='H-12',
            remind_who='test@example.org',
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_location,
            'EMEA')
        self.assertEqual(
            meeting.recursion_frequency,
            7)
        self.assertEqual(
            meeting.reminder.reminder_offset,
            'H-12')
        self.assertEqual(
            meeting.reminder.reminder_to,
            'test@example.org')

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Name23h59',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=date.today() + timedelta(days=1),
            meeting_time_start=time(23, 0),
            meeting_time_stop=time(23, 59),
            comanager=None,
            meeting_information='Information',
            meeting_location='EMEA',
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 10)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Name23h59')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_time_stop.minute,
            59)

        fedocallib.add_meeting(
            session=self.session,
            calendarobj=calendarobj,
            fas_user=fasuser,
            meeting_name='Full day',
            meeting_date=date.today() + timedelta(days=1),
            meeting_date_end=None,
            meeting_time_start=time(23, 0),
            meeting_time_stop=time(23, 59),
            comanager=None,
            meeting_information='Information',
            meeting_location='EMEA',
            tzone='Europe/Paris',
            frequency=None,
            end_repeats=None,
            remind_when=None,
            remind_who=None,
            full_day=True)
        meeting = model.Meeting.by_id(self.session, 11)
        self.assertNotEqual(meeting, None)
        self.assertEqual(meeting.meeting_name, 'Full day')
        self.assertEqual(meeting.meeting_manager, ['username'])
        self.assertEqual(meeting.meeting_information, 'Information')
        self.assertEqual(meeting.meeting_date,
                         date.today() + timedelta(days=1))
        self.assertEqual(meeting.meeting_time_start.hour, 0)
        self.assertEqual(meeting.meeting_time_start.minute, 0)
        self.assertEqual(meeting.meeting_date_end,
                         date.today() + timedelta(days=2))
        self.assertEqual(meeting.meeting_time_stop.hour, 0)
        self.assertEqual(meeting.meeting_time_stop.minute, 0)

    def test_edit_meeting_fail(self):
        """ Test the edit_meeting function for when edit fails. """
        self.__setup_meeting()
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        self.assertNotEqual(calendarobj, None)

        meeting = model.Meeting.by_id(self.session, 1)
        self.assertEqual(meeting.meeting_name, 'Fedora-fr-test-meeting')

        fasuser = FakeUser(['test'])
        self.assertRaises(
            UserNotAllowed,
            fedocallib.edit_meeting,
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1),
            None,
            time(23, 0),
            time(23, 59),
            None,
            'Information',
            'EMEA',
            'Europe/Paris',
            None, None,
            None, None,
            full_day=False)
        self.session.rollback()

        fasuser = FakeUser(['fi-apprentice'])

        self.assertRaises(
            InvalidMeeting,
            fedocallib.edit_meeting,
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1),
            None,
            time(23, 0),
            time(21, 59),
            None,
            'Information',
            'EMEA',
            'Europe/Paris',
            None, None,
            None, None,
            full_day=False)
        self.session.rollback()

        self.assertRaises(
            InvalidMeeting,
            fedocallib.edit_meeting,
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1),
            date.today(),
            time(23, 0),
            time(23, 59),
            None,
            'Information',
            'EMEA',
            'Europe/Paris',
            None, None,
            None, None,
            full_day=False)
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
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1),
            None,
            time(23, 0),
            time(23, 59),
            None,
            'Information',
            'EMEA',
            'Europe/Paris',
            None, None,
            None, None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Fedora-fr-meeting_edited')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_time_stop.minute,
            59)

        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1),
            None,
            time(23, 0),
            time(23, 0),
            None,
            'Information',
            'EMEA',
            'Europe/Paris',
            None, None,
            None, None,
            full_day=True)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Fedora-fr-meeting_edited')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_date, date.today() + timedelta(days=1))
        self.assertEqual(
            meeting.meeting_date_end, date.today() + timedelta(days=2))

        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited2',
            date.today() + timedelta(days=1),
            None,
            time(23, 0),
            time(23, 59),
            'pingou',
            'Information2',
            'EMEA',
            'Europe/Paris',
            None, None,
            None, None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Fedora-fr-meeting_edited2')
        self.assertEqual(
            meeting.meeting_manager,
            ['pingou', 'username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information2')
        self.assertEqual(
            meeting.meeting_time_stop.minute,
            59)

        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited',
            date.today() + timedelta(days=1),
            None,
            time(23, 0),
            time(23, 59),
            None,
            'Information',
            'EMEA',
            'Europe/Paris',
            None, None,
            'H-24', 'test@example.org',
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Fedora-fr-meeting_edited')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_time_stop.minute,
            59)
        self.assertEqual(
            meeting.reminder.reminder_offset,
            'H-24')
        self.assertEqual(
            meeting.reminder.reminder_to,
            'test@example.org')

        dstart = date.today() + timedelta(days=1)
        if dstart == TODAY + timedelta(days=3):
            dstart = dstart + timedelta(days=1)
        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited2',
            dstart,
            None,
            time(22, 0),
            time(23, 0),
            None,
            'Information',
            'EMEA',
            'Europe/Paris',
            7, TODAY + timedelta(days=30),
            None, None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Fedora-fr-meeting_edited2')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.meeting_time_stop.minute,
            0)
        self.assertEqual(
            meeting.recursion_frequency,
            7)
        self.assertEqual(
            meeting.recursion_ends,
            TODAY + timedelta(days=30))
        self.assertEqual(
            meeting.reminder,
            None)

        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Fedora-fr-meeting_edited2',
            date.today() + timedelta(days=1),
            None,
            time(21, 0),
            time(22, 00),
            None,
            'Information2',
            None,
            'Europe/Paris',
            None, None,
            None, None,
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 1)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Fedora-fr-meeting_edited2')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information2')
        self.assertEqual(
            meeting.meeting_location,
            None)
        self.assertEqual(
            meeting.recursion_frequency,
            None)
        self.assertEqual(
            meeting.recursion_ends,
            None)
        self.assertEqual(
            meeting.reminder,
            None)

        meeting = model.Meeting.by_id(self.session, 9)
        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Test meeting with reminder-2',
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=3),
            time(20, 0),
            time(21, 00),
            None,
            'Information2',
            None,
            'Europe/Paris',
            None, None,
            'H-24', 'test@example.org',
            full_day=False)
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Test meeting with reminder-2')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information2')
        self.assertEqual(
            meeting.reminder.reminder_offset,
            'H-24')
        self.assertEqual(
            meeting.reminder.reminder_to,
            'test@example.org')
        self.assertEqual(
            meeting.meeting_date_end,
            date.today() + timedelta(days=3))

        meeting = model.Meeting.by_id(self.session, 9)
        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Test meeting with reminder-2',
            dstart,
            date.today() + timedelta(days=3),
            time(23, 0),
            time(23, 59),
            None,
            'Information2',
            None,
            'Europe/Paris',
            7, TODAY + timedelta(days=30),
            'H-24', 'test@example.org',
            full_day=False,
            edit_all_meeting=False)
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Test meeting with reminder-2')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information2')
        self.assertEqual(
            meeting.reminder.reminder_offset,
            'H-24')
        self.assertEqual(
            meeting.reminder.reminder_to,
            'test@example.org')
        self.assertEqual(
            meeting.meeting_date_end,
            date.today() + timedelta(days=3))

        # Remove recursion
        meeting = model.Meeting.by_id(self.session, 9)
        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Test meeting with reminder-2.4',
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=2),
            time(23, 0),
            time(23, 59),
            None,
            'Information',
            None,
            'Europe/Paris',
            None, None,  # Recursion
            None, None,  # Reminder
            full_day=True,
            edit_all_meeting=False)
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Test meeting with reminder-2.4')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information')
        self.assertEqual(
            meeting.reminder,
            None)
        self.assertEqual(
            meeting.recursion_ends,
            None)
        self.assertEqual(
            meeting.recursion_frequency,
            None)
        self.assertEqual(
            meeting.meeting_date,
            date.today() + timedelta(days=1))
        self.assertEqual(
            meeting.meeting_time_start,
            time(0, 0))
        self.assertEqual(
            meeting.meeting_time_stop,
            time(0, 0))
        self.assertEqual(
            meeting.meeting_date_end,
            date.today() + timedelta(days=2))

        # Set the recursion to 7 days - end recursion will be filled
        # automatically
        meeting = model.Meeting.by_id(self.session, 9)
        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Test meeting with reminder-2.3',
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=2),
            time(23, 0),
            time(23, 59),
            None,
            'Information3',
            None,
            'Europe/Paris',
            7, None,  # Recursion
            None, None,  # Reminder
            full_day=False,
            edit_all_meeting=False)
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Test meeting with reminder-2.3')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information3')
        self.assertEqual(
            meeting.reminder,
            None)
        self.assertEqual(
            meeting.recursion_ends,
            date(2025, 12, 31))
        self.assertEqual(
            meeting.recursion_frequency,
            7)
        self.assertEqual(
            meeting.meeting_date_end,
            date.today() + timedelta(days=2))

        # Move the meeting to another calendar
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar4')
        meeting = model.Meeting.by_id(self.session, 9)
        fedocallib.edit_meeting(
            self.session,
            meeting,
            calendarobj,
            fasuser,
            'Test meeting with reminder-2.3',
            date.today() + timedelta(days=1),
            date.today() + timedelta(days=2),
            time(23, 0),
            time(23, 59),
            None,
            'Information3',
            None,
            'Europe/Paris',
            7, None,  # Recursion
            None, None,  # Reminder
            full_day=False,
            edit_all_meeting=False)
        meeting = model.Meeting.by_id(self.session, 9)
        self.assertNotEqual(meeting, None)
        self.assertEqual(
            meeting.meeting_name,
            'Test meeting with reminder-2.3')
        self.assertEqual(
            meeting.meeting_manager,
            ['username'])
        self.assertEqual(
            meeting.meeting_information,
            'Information3')
        self.assertEqual(
            meeting.reminder,
            None)
        self.assertEqual(
            meeting.recursion_ends,
            None)
        self.assertEqual(
            meeting.recursion_frequency,
            None)
        self.assertEqual(
            meeting.meeting_date_end,
            date.today() + timedelta(days=2))
        self.assertEqual(
            meeting.calendar_name,
            'test_calendar4')

    def test_get_calendar_statuses(self):
        """ Test the get_calendar_statuses function from fedocallib. """
        statuses = [status.status
                    for status in fedocallib.get_calendar_statuses(
                        self.session)
                    ]
        self.assertEqual(statuses, ['Enabled', 'Disabled'])

    def test_search_meetings(self):
        """ Test the search_meetings function of fedocallib. """
        self.assertEqual(fedocallib.search_meetings(self.session, '*'), [])
        self.__setup_meeting()
        self.assertEqual(
            len(fedocallib.search_meetings(self.session, '*')), 14)
        self.assertEqual(
            len(fedocallib.search_meetings(self.session, '*-fr*')), 1)
        self.assertEqual(
            len(fedocallib.search_meetings(self.session, 'fedora-fr*')), 1)

    def test_get_locations(self):
        """ Test the get_locations function of fedocallib. """
        self.assertEqual(
            fedocallib.get_locations(self.session), [])

    def test_clear_calendar(self):
        """ Test the clear_calendar function of fedocallib. """
        self.__setup_meeting()
        self.assertEqual(
            len(fedocallib.search_meetings(self.session, '*')), 14)

        calendarobj = model.Calendar.by_id(self.session, 'test_calendar4')
        fedocallib.clear_calendar(self.session, calendarobj)

        self.assertEqual(
            len(fedocallib.search_meetings(self.session, '*')), 11)

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Fedocallibtests)
    unittest.TextTestRunner(verbosity=2, failfast=True).run(SUITE)
