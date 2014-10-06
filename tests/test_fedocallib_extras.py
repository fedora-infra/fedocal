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

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

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
from tests import Modeltests


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
        obj.add_manager(self.session, 'pingou')
        obj.save(self.session)
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



if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FedocallibExtratests)
    unittest.TextTestRunner(verbosity=2, failfast=True).run(SUITE)
