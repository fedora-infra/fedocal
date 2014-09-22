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

 tests for fedocal's cron job
"""

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import logging
import unittest
import sys
import os

from datetime import timedelta, datetime

from mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedocal_cron

from fedocal.fedocallib import model
from fedocal.fedocallib import week
from fedocal.fedocallib import exceptions

import tests
from tests import Modeltests
from test_meeting import Meetingtests, TODAY


DB_PATH = 'sqlite:////tmp/fedocal_test.sqlite'


# pylint: disable=C0103
class Crontests(Modeltests):
    """ Cron tests. """

    def _clean(self):
        """ Clean a potentially existing test database. """
        root, path = DB_PATH.split(':///', 1)
        if os.path.exists(path):
            os.unlink(path)


    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        self._clean()

        tests.DB_PATH = DB_PATH

        super(Crontests, self).setUp()

        fedocal_cron.fedocal.APP.config['DB_URL'] = DB_PATH
        fedocal_cron.fedocal.APP.config['TESTING'] = True
        fedocal_cron.fedocal.APP.debug = True
        fedocal_cron.fedocal.APP.logger.handlers = []
        fedocal_cron.fedocal.APP.logger.setLevel(logging.CRITICAL)
        fedocal_cron.fedocal.SESSION = self.session

        # Fills some data in the database in memory

        # A calendar
        calendar = model.Calendar(
            calendar_name='test_calendar',
            calendar_contact='test@example.com',
            calendar_description='This is a test calendar',
            calendar_editor_group='fi-apprentice',
            calendar_admin_group='infrastructure-main2')
        calendar.save(self.session)
        self.session.commit()
        self.assertNotEqual(calendar, None)

    fedocal_cron.fedmsg_init()

    def tearDown(self):
        """ Remove the test.db database if there is one. """
        self.session.close()

        super(Crontests, self).tearDown()

        self._clean()

    def test_no_reminder(self):
        """ Test the cron job for run with no reminders.
        """
        # Meeting with a reminder but outside the standard offsets
        remobj = model.Reminder(
            'H-12', 'pingou@fedoraproject.org', 'root@localhost',
            'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()

        date_sa = datetime.utcnow() + timedelta(hours=15)
        date_so = datetime.utcnow() + timedelta(hours=16)

        obj = model.Meeting(  # id:1
            meeting_name='Test meeting with reminder',
            meeting_date=date_sa.date(),
            meeting_date_end=date_so.date(),
            meeting_time_start=date_sa.time(),
            meeting_time_stop=date_so.time(),
            meeting_information='This is a test meeting with reminder',
            calendar_name='test_calendar',
            reminder_id=remobj.reminder_id)
        obj.add_manager(self.session, ['pingou'])
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        msgs = fedocal_cron.send_reminder()

        self.assertEqual(len(msgs), 0)

    @patch('fedocal_cron.smtplib.SMTP.sendmail')
    def test_one_reminder(self, mail_mock):
        """ Test the cron job for a meeting with a single reminder to send.
        """
        mail_mock.return_value = None

        # Meeting with a reminder
        remobj = model.Reminder(
            'H-12', 'pingou@fp.o', 'list@lists.fp.o',
            'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()

        date_sa = datetime.utcnow() + timedelta(hours=12)
        date_so = datetime.utcnow() + timedelta(hours=13)

        obj = model.Meeting(  # id:1
            meeting_name='Test meeting with reminder',
            meeting_date=date_sa.date(),
            meeting_date_end=date_so.date(),
            meeting_time_start=date_sa.time(),
            meeting_time_stop=date_so.time(),
            meeting_information='This is a test meeting with reminder',
            calendar_name='test_calendar',
            reminder_id=remobj.reminder_id)
        obj.add_manager(self.session, ['pingou'])
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        msgs = fedocal_cron.send_reminder()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['To'], 'list@lists.fp.o')
        self.assertEqual(msgs[0]['From'], 'pingou@fp.o')

    @patch('fedocal_cron.smtplib.SMTP.sendmail')
    def test_two_reminder(self, mail_mock):
        """ Test the cron job for a meeting with a single reminder to send.
        """
        mail_mock.return_value = None

        # Meeting with a reminder
        remobj = model.Reminder(
            'H-12', 'pingou@fp.o', 'pingou@fp.o,pingou@p.fr',
            'Come to our test meeting')
        remobj.save(self.session)
        self.session.flush()

        date_sa = datetime.utcnow() + timedelta(hours=12)
        date_so = datetime.utcnow() + timedelta(hours=13)

        obj = model.Meeting(  # id:1
            meeting_name='Test meeting with reminder',
            meeting_date=date_sa.date(),
            meeting_date_end=date_so.date(),
            meeting_time_start=date_sa.time(),
            meeting_time_stop=date_so.time(),
            meeting_information='This is a test meeting with reminder',
            calendar_name='test_calendar',
            reminder_id=remobj.reminder_id)
        obj.add_manager(self.session, ['pingou'])
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        msgs = fedocal_cron.send_reminder()

        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0]['To'], 'pingou@fp.o, pingou@p.fr')
        self.assertEqual(msgs[0]['From'], 'pingou@fp.o')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Crontests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
