#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Pierre-Yves Chibon
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

 fedocal.lib tests script
 - for special corner case to test
"""
from __future__ import unicode_literals, absolute_import, print_function

import unittest
import sys
import os

from datetime import time
from datetime import datetime
from datetime import timedelta

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedocal.fedocallib as fedocallib
from fedocal.fedocallib import model
from tests import Modeltests, FakeUser


# pylint: disable=R0904
class FedocallibExtratests(Modeltests):
    """ FedocallibExtra tests. """

    session = None

    def __setup_calendar(self):
        """ Set up basic calendar information. """
        obj = model.Calendar(
            calendar_name='test_calendar',
            calendar_contact='test@example.com',
            calendar_description='This is a test calendar',
            calendar_editor_group='fi-apprentice',
            calendar_admin_group='infrastructure-main2')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_delete_recurring_meeting(self):
        """ Test deleting a recurring meeting in the middle of the
        recursion.
        """
        # Setup info
        self.__setup_calendar()
        obj = model.Meeting(  # id:1
            meeting_name='test recurring',
            meeting_date=datetime(2014, 9, 1).date(),
            meeting_date_end=datetime(2014, 9, 1).date(),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            meeting_information='This is a test meeting recurring',
            calendar_name='test_calendar',
            recursion_frequency=7,
            recursion_ends=datetime(2014, 10, 27).date(),
        )
        obj.save(self.session)
        obj.add_manager(self.session, 'pingou')
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Before deletion
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2014, 10, 27).date()
        )
        self.assertEqual(len(meetings), 9)
        ids = set([mtg.meeting_id for mtg in meetings])
        self.assertEqual(len(ids), 1)
        self.assertEqual(list(ids)[0], 1)
        dates = [str(mtg.meeting_date) for mtg in meetings]
        self.assertEqual(
            dates,
            [
                '2014-09-01', '2014-09-08', '2014-09-15', '2014-09-22',
                '2014-09-29', '2014-10-06', '2014-10-13', '2014-10-20',
                '2014-10-27',
            ]
        )

        # Delete meeting in the middle
        meeting = model.Meeting.by_id(self.session, 1)
        fedocallib.delete_recursive_meeting(
            self.session,
            meeting=meeting,
            del_date=datetime(2014, 10, 20).date(),
            all_meetings=False)

        # After deletion
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2014, 10, 27).date()
        )
        self.assertEqual(len(meetings), 8)
        self.assertEqual(len(ids), 1)
        self.assertEqual(list(ids)[0], 1)
        dates = [str(mtg.meeting_date) for mtg in meetings]
        self.assertEqual(
            dates,
            [
                '2014-09-01', '2014-09-08', '2014-09-15', '2014-09-22',
                '2014-09-29', '2014-10-06', '2014-10-13',
                '2014-10-27',
            ]
        )

        # Delete meeting after the end of the recursion
        meeting = model.Meeting.by_id(self.session, 1)
        fedocallib.delete_recursive_meeting(
            self.session,
            meeting=meeting,
            del_date=datetime(2015, 10, 20).date(),
            all_meetings=False)

        # After deletion
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2015, 10, 27).date()
        )
        self.assertEqual(len(meetings), 8)
        self.assertEqual(len(ids), 1)
        self.assertEqual(list(ids)[0], 1)
        dates = [str(mtg.meeting_date) for mtg in meetings]
        self.assertEqual(
            dates,
            [
                '2014-09-01', '2014-09-08', '2014-09-15', '2014-09-22',
                '2014-09-29', '2014-10-06', '2014-10-13',
                '2014-10-27',
            ]
        )

        # Delete meeting before the start of the recursion
        # This will delete the first occurrence of the meeting as it is the
        # first one after the date specified.
        meeting = model.Meeting.by_id(self.session, 1)
        fedocallib.delete_recursive_meeting(
            self.session,
            meeting=meeting,
            del_date=datetime(2014, 8, 18).date(),
            all_meetings=False)

        # After deletion
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 8, 1).date(),
            datetime(2015, 10, 27).date()
        )
        self.assertEqual(len(meetings), 7)
        self.assertEqual(len(ids), 1)
        self.assertEqual(list(ids)[0], 1)
        dates = [str(mtg.meeting_date) for mtg in meetings]
        self.assertEqual(
            dates,
            [
                '2014-09-08', '2014-09-15', '2014-09-22',
                '2014-09-29', '2014-10-06', '2014-10-13',
                '2014-10-27',
            ]
        )

    def test_editing_recurring_meeting_one_day_later(self):
        """ Test editing moving a meeting one day later in a recursion
        """
        # Setup info
        self.__setup_calendar()
        obj = model.Meeting(  # id:1
            meeting_name='test recurring',
            meeting_date=datetime(2014, 9, 1).date(),
            meeting_date_end=datetime(2014, 9, 1).date(),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            meeting_information='This is a test meeting recurring',
            calendar_name='test_calendar',
            recursion_frequency=7,
            recursion_ends=datetime(2014, 10, 27).date(),
        )
        obj.save(self.session)
        obj.add_manager(self.session, 'pingou')
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Before edition
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2014, 10, 27).date()
        )
        self.assertEqual(len(meetings), 9)
        ids = set([mtg.meeting_id for mtg in meetings])
        self.assertEqual(len(ids), 1)
        self.assertEqual(list(ids)[0], 1)
        dates = [str(mtg.meeting_date) for mtg in meetings]
        self.assertEqual(
            dates,
            [
                '2014-09-01', '2014-09-08', '2014-09-15', '2014-09-22',
                '2014-09-29', '2014-10-06', '2014-10-13', '2014-10-20',
                '2014-10-27',
            ]
        )

        # Edit meeting in the middle to move it by one day
        meeting = model.Meeting.by_id(self.session, 1)
        fedocallib.edit_meeting(
            session=self.session,
            meeting=meeting,
            calendarobj=calendarobj,
            fas_user=FakeUser(groups=['fi-apprentice'], username='pingou'),
            meeting_name='test recurring',
            meeting_date=datetime(2014, 9, 16).date(),
            meeting_date_end=datetime(2014, 9, 16).date(),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager='pingou',
            meeting_information='This is a test meeting recurring',
            meeting_location=None,
            tzone='UTC',
            recursion_frequency=7,
            recursion_ends=datetime(2014, 10, 27).date(),
            remind_when=None,
            reminder_from=None,
            remind_who=None,
            full_day=False,
            edit_all_meeting=False,
            admin=False
        )

        # After edition
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2014, 10, 27).date()
        )
        self.assertEqual(len(meetings), 9)
        ids = set([mtg.meeting_id for mtg in meetings])
        self.assertEqual(list(ids), [1, 2, 3])
        dates = [str(mtg.meeting_date) for mtg in meetings]
        # One meeting moved by 1 day
        self.assertEqual(
            sorted(dates),
            [
                '2014-09-01', '2014-09-08', '2014-09-16', '2014-09-22',
                '2014-09-29', '2014-10-06', '2014-10-13', '2014-10-20',
                '2014-10-27',
            ]
        )

        # Edit meeting in the middle to move it by 3 day (later)
        meeting = model.Meeting.by_id(self.session, 3)
        fedocallib.edit_meeting(
            session=self.session,
            meeting=meeting,
            calendarobj=calendarobj,
            fas_user=FakeUser(groups=['fi-apprentice'], username='pingou'),
            meeting_name='test recurring',
            meeting_date=datetime(2014, 10, 9).date(),
            meeting_date_end=datetime(2014, 10, 9).date(),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager='pingou',
            meeting_information='This is a test meeting recurring',
            meeting_location=None,
            tzone='UTC',
            recursion_frequency=7,
            recursion_ends=datetime(2014, 10, 27).date(),
            remind_when=None,
            reminder_from=None,
            remind_who=None,
            full_day=False,
            edit_all_meeting=False,
            admin=False
        )

        # After edition
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2014, 10, 27).date()
        )
        self.assertEqual(len(meetings), 9)
        ids = set([mtg.meeting_id for mtg in meetings])
        self.assertEqual(list(ids), [1, 2, 3, 4, 5])
        dates = [str(mtg.meeting_date) for mtg in meetings]
        # One meeting moved by 3 days
        self.assertEqual(
            sorted(dates),
            [
                '2014-09-01', '2014-09-08', '2014-09-16', '2014-09-22',
                '2014-09-29', '2014-10-09', '2014-10-13', '2014-10-20',
                '2014-10-27',
            ]
        )

    def test_editing_recurring_meeting_one_day_earlier(self):
        """ Test editing moving a meeting one day earlier in a recursion
        """
        # Setup info
        self.__setup_calendar()
        obj = model.Meeting(  # id:1
            meeting_name='test recurring',
            meeting_date=datetime(2014, 9, 1).date(),
            meeting_date_end=datetime(2014, 9, 1).date(),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            meeting_information='This is a test meeting recurring',
            calendar_name='test_calendar',
            recursion_frequency=7,
            recursion_ends=datetime(2014, 10, 27).date(),
        )
        obj.save(self.session)
        obj.add_manager(self.session, 'pingou')
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Before edition
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2014, 10, 27).date()
        )
        self.assertEqual(len(meetings), 9)
        ids = set([mtg.meeting_id for mtg in meetings])
        self.assertEqual(list(ids)[0], 1)
        dates = [str(mtg.meeting_date) for mtg in meetings]
        self.assertEqual(
            dates,
            [
                '2014-09-01', '2014-09-08', '2014-09-15', '2014-09-22',
                '2014-09-29', '2014-10-06', '2014-10-13', '2014-10-20',
                '2014-10-27',
            ]
        )

        # Edit meeting in the middle to move it by one day
        meeting = model.Meeting.by_id(self.session, 1)
        fedocallib.edit_meeting(
            session=self.session,
            meeting=meeting,
            calendarobj=calendarobj,
            fas_user=FakeUser(groups=['fi-apprentice'], username='pingou'),
            meeting_name='test recurring',
            meeting_date=datetime(2014, 9, 14).date(),
            meeting_date_end=datetime(2014, 9, 14).date(),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager='pingou',
            meeting_information='This is a test meeting recurring',
            meeting_location=None,
            tzone='UTC',
            recursion_frequency=7,
            recursion_ends=datetime(2014, 10, 27).date(),
            remind_when=None,
            reminder_from=None,
            remind_who=None,
            full_day=False,
            edit_all_meeting=False,
            admin=False
        )

        # After edition
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2014, 10, 27).date()
        )
        #self.assertEqual(len(meetings), 9)
        ids = set([mtg.meeting_id for mtg in meetings])
        #self.assertEqual(list(ids), [1, 2, 3])
        dates = [str(mtg.meeting_date) for mtg in meetings]
        # One meeting moved by 1 day
        self.assertEqual(
            sorted(dates),
            [
                '2014-09-01', '2014-09-08', '2014-09-14', '2014-09-22',
                '2014-09-29', '2014-10-06', '2014-10-13', '2014-10-20',
                '2014-10-27',
            ]
        )

        # Edit meeting in the middle to move it by 3 days (earlier)
        meeting = model.Meeting.by_id(self.session, 3)
        fedocallib.edit_meeting(
            session=self.session,
            meeting=meeting,
            calendarobj=calendarobj,
            fas_user=FakeUser(groups=['fi-apprentice'], username='pingou'),
            meeting_name='test recurring',
            meeting_date=datetime(2014, 9, 26).date(),
            meeting_date_end=datetime(2014, 9, 26).date(),
            meeting_time_start=time(9, 0),
            meeting_time_stop=time(10, 0),
            comanager='pingou',
            meeting_information='This is a test meeting recurring',
            meeting_location=None,
            tzone='UTC',
            recursion_frequency=7,
            recursion_ends=datetime(2014, 10, 27).date(),
            remind_when=None,
            reminder_from=None,
            remind_who=None,
            full_day=False,
            edit_all_meeting=False,
            admin=False
        )

        # After edition
        calendarobj = model.Calendar.by_id(self.session, 'test_calendar')
        meetings = fedocallib.get_by_date(
            self.session, calendarobj,
            datetime(2014, 9, 1).date(),
            datetime(2014, 10, 27).date()
        )
        self.assertEqual(len(meetings), 9)
        ids = set([mtg.meeting_id for mtg in meetings])
        self.assertEqual(list(ids), [1, 2, 3, 4, 5])
        dates = [str(mtg.meeting_date) for mtg in meetings]
        # One meeting moved by 3 day
        self.assertEqual(
            sorted(dates),
            [
                '2014-09-01', '2014-09-08', '2014-09-14', '2014-09-22',
                '2014-09-26', '2014-10-06', '2014-10-13', '2014-10-20',
                '2014-10-27',
            ]
        )


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FedocallibExtratests)
    unittest.TextTestRunner(verbosity=2, failfast=True).run(SUITE)
