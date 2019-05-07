#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
 (c) 2012-2017 - Copyright Pierre-Yves Chibon
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
from __future__ import unicode_literals, absolute_import, print_function

import logging
import unittest
import sys
import os
import re

from datetime import date
from datetime import datetime
from datetime import time
from datetime import timedelta

import flask
import six

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedocal
import fedocal.fedocallib as fedocallib
import fedocal.fedocallib.model as model
from tests import (Modeltests, FakeUser, flask10_only, user_set, TODAY,
                   ICS_FILE, ICS_FILE_NOTOK)


# pylint: disable=E1103
class Flasktests(Modeltests):
    """ Flask application tests. """

    maxDiff = None

    def __setup_db(self):
        """ Add a calendar and some meetings so that we can play with
        something. """
        from .test_meeting import Meetingtests
        meeting = Meetingtests('test_init_meeting')
        meeting.session = self.session
        meeting.test_init_meeting()

    def get_sample_file_content(self, filename):
        """
        Read a file with filename from dir ./sample_files and
        return its content.

        :arg filename: A string
        :returns: A string
        """
        filename = os.path.join(
            os.path.dirname(__file__),
            'sample_files/{}'.format(filename)
        )
        with open(filename) as stream:
            content = stream.read()
        return content

    def wrap_content(self, content, replacements=[]):
        """
        Wrap content and return wrapped content.

        :arg content: String
        :kwarg replacements: A list of tuples, where each
            tuple is of the form (<pattern_str>, <repl_str>)

        :returns: A string
        """
        for pattern, repl in replacements:
            content = re.sub(pattern, repl, content)
        return content

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(Flasktests, self).setUp()

        fedocal.APP.config['TESTING'] = True
        fedocal.APP.debug = True
        fedocal.APP.logger.handlers = []
        fedocal.APP.logger.setLevel(logging.CRITICAL)
        fedocal.SESSION = self.session
        self.app = fedocal.APP.test_client()

    def test_index_empty(self):
        """ Test the index function. """
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertTrue(
            '<title>Home - Fedocal</title>', output_text)

    def test_index(self):
        """ Test the index function. """
        self.__setup_db()

        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>Home - Fedocal</title>', output_text)
        self.assertIn('href="/test_calendar/">', output_text)
        self.assertIn('href="/test_calendar2/">', output_text)
        self.assertIn('href="/test_calendar4/">', output_text)

    def test_calendar(self):
        """ Test the calendar function. """
        self.__setup_db()

        output = self.app.get('/test_calendar')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/test_calendar', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get('/test_calendar2/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar2 - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get('/foorbar/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            'class="errors">No calendar named foorbar could be found</',
            output_text)

        output = self.app.get('/test_calendar2/?tzone=Europe/Paris',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar2 - Fedocal</title>', output_text)

    def test_location(self):
        """ Test the location calendar function. """
        self.__setup_db()

        output = self.app.get('/location/test')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/location/test/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

    def test_calendar_fullday(self):
        """ Test the calendar_fullday function. """
        self.__setup_db()

        today = date.today()
        output = self.app.get(
            '/test_calendar/%s/%s/%s/' % (
                today.year, today.month, today.day))
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get(
            '/test_calendar/%s/%s/%s' % (
                today.year, today.month, today.day))
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/test_calendar/%s/%s/%s/' % (
            today.year, today.month, today.day), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

    def test_calendar_list(self):
        """ Test the calendar_list function. """
        self.__setup_db()

        output = self.app.get('/list/test_calendar/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get('/list/foorbar/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            'class="errors">No calendar named foorbar could be found</',
            output_text)

        today = date.today()
        output = self.app.get('/list/test_calendar/%s/%s/%s/' % (
            today.year, today.month, today.day))
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get('/list/test_calendar/%s/%s/%s' % (
            today.year, today.month, today.day))
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/list/test_calendar/%s/%s/%s/' % (
            today.year, today.month, today.day), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get('/list/test_calendar/%s/%s/' % (
            today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        # 6 on Tue Jun 24 - 12 before, 14 on Tue Jul 15
        self.assertTrue(output_text.count('<a class="event meeting_') >= 5)
        self.assertTrue(output_text.count('<tr') > 10)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get('/list/test_calendar/%s/%s/?subject=Another'
            % (today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        # 4 on Tue Jun 24 - 6 before, 8 on Tue Jul 15
        self.assertTrue(output_text.count('<a class="event meeting_') >= 4)
        self.assertTrue(output_text.count('<tr') > 10)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get('/list/test_calendar/%s/%s/?subject=Another past'
            % (today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        # 3 on Tue Jun 24 - 4 before, 5 on Tue Jul 15
        self.assertTrue(output_text.count('<a class="event meeting_') >= 3)
        self.assertTrue(output_text.count('<tr') >= 10)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)

        output = self.app.get('/list/test_calendar/%s/%s/?delta=10'
            % (today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        # 1 on Tue Jun 24 - 2 before
        self.assertTrue(
            output_text.count(
                '<a class="event event_blue meeting_') in range(9))
        self.assertTrue(output_text.count('<tr') >= 6)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)

        output = self.app.get('/list/test_calendar/%s/%s/?delta=abc'
            % (today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        # 6 on Tue Jun 24 - 12 before, 14 on Tue Jul 15
        self.assertTrue(output_text.count(
            '<a class="event event_blue meeting_') >= 5)
        self.assertTrue(output_text.count('<tr') >= 10)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)

        end_date = today + timedelta(days=10)

        output = self.app.get('/list/test_calendar/%s/%s/?end=%s-11'
            % (today.year, today.month, end_date.strftime('%Y-%m')
            ), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        # 14 on Tue Jun 24 - 2 before, 1 on August 15th
        self.assertTrue(output_text.count(
            '<a class="event event_blue meeting_') > 0)
        # 22 on Tue Jun 24 - 10 before, 8 on August 15th
        self.assertTrue(output_text.count('<tr') >= 7)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)

        output = self.app.get('/list/test_calendar/%s/%s/?end=foobar'
            % (today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        # 6 on Tue Jun 24 - 12 before, 14 on Tue Jul 15
        self.assertTrue(output_text.count('<a class="event meeting_') >= 5)
        # 14 on Tue Jun 24 - 20 before, 21 on Tue Jul 15, 27 on Fri Aug 1
        # 22 on August 15th
        self.assertTrue(output_text.count('<tr') >= 12)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)

    def test_ical_out(self):
        """ Test the ical_out function. """
        self.__setup_db()

        output = self.app.get('/ical/test_calendar/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('BEGIN:VCALENDAR', output_text)
        self.assertIn('SUMMARY:test-meeting2', output_text)
        self.assertIn(
            'DESCRIPTION:This is a test meeting with recursion',
            output_text)
        self.assertIn('ORGANIZER:pingou', output_text)
        self.assertEqual(output_text.count('BEGIN:VEVENT'), 10)
        self.assertEqual(output_text.count('END:VEVENT'), 10)

        output = self.app.get('/ical/foorbar/')
        self.assertEqual(output.status_code, 404)

    def test_location_list(self):
        """ Test the calendar_list function. """
        self.__setup_db()

        output = self.app.get('/location/list/EMEA/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title> EMEA  - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)
        self.assertEqual(output_text.count('<a class="event event_blue'), 1)
        self.assertEqual(output_text.count('<a class="event'), 2)

        output = self.app.get('/location/list/foorbar/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            'class="errors">No location named foorbar could be found</',
            output_text)

        today = date.today()
        output = self.app.get('/location/list/EMEA/%s/%s/%s/' % (
            today.year, today.month, today.day))
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title> EMEA  - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)
        self.assertIn(
            output_text.count('<a class="event event_blue'), [0, 1])
        self.assertIn(output_text.count('<a class="event'), range(3))

        output = self.app.get('/location/list/EMEA/%s/%s/' % (
            today.year, today.month))
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title> EMEA  - Fedocal</title>', output_text)
        self.assertIn(' <a href="/test_calendar/">', output_text)
        self.assertIn(' <a href="/test_calendar2/">', output_text)
        self.assertIn(' <a href="/test_calendar4/">', output_text)
        self.assertIn(
            output_text.count('<a class="event event_blue'), [1, 2])
        self.assertIn(output_text.count('<a class="event'), [2, 4])

    def test_ical_all(self):
        """ Test the ical_all function. """
        self.__setup_db()

        output = self.app.get('/ical/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('BEGIN:VCALENDAR', output_text)
        self.assertIn('SUMMARY:test-meeting2', output_text)
        self.assertIn(
            'DESCRIPTION:This is a test meeting with recursion',
            output_text)
        self.assertIn('ORGANIZER:pingou', output_text)
        self.assertEqual(output_text.count('BEGIN:VEVENT'), 15)
        self.assertEqual(output_text.count('END:VEVENT'), 15)

    def test_ical_meeting(self):
        """ Test the ical_calendar_meeting function. """
        self.__setup_db()

        meeting_obj = model.Meeting.by_id(self.session, 2)
        expected_data = self.get_sample_file_content(
            'meeting.ical').format(
            start_datetime=datetime.combine(
                meeting_obj.meeting_date,
                meeting_obj.meeting_time_start).strftime(
                    '%Y%m%dT%H%M%SZ'),
            end_datetime=datetime.combine(
                meeting_obj.meeting_date_end,
                meeting_obj.meeting_time_stop).strftime(
                    '%Y%m%dT%H%M%SZ')
        )

        output = self.app.get('/ical/calendar/meeting/2/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        data = self.wrap_content(
            output_text, replacements=[
                (r'UID:.*\n', 'UID:DUMMY_UID\r\n'),
                (r'DTSTAMP:.*\n', 'DTSTAMP:20181221T120122Z\r\n'),
            ]
        )
        # Newer python-vobject in the DTSTAMP field
        if "DTSTAMP" in data:
            string = "DTSTAMP:20181221T120122Z\r\nORGANIZER"
            if six.PY3:
                string = "DTSTAMP:20181221T120122Z\nORGANIZER"
            expected_data = expected_data.replace("ORGANIZER", string)

        if six.PY3:
            data = data.replace("\r\n", "\n")
        self.assertEqual(data, expected_data)

        # Test meeting iCal with reminder
        expected_data = self.get_sample_file_content(
            'meeting_with_reminder.ical').format(
            start_datetime=datetime.combine(
                meeting_obj.meeting_date,
                meeting_obj.meeting_time_start).strftime(
                    '%Y%m%dT%H%M%SZ'),
            end_datetime=datetime.combine(
                meeting_obj.meeting_date_end,
                meeting_obj.meeting_time_stop).strftime(
                    '%Y%m%dT%H%M%SZ')
        )
        output = self.app.get('/ical/calendar/meeting/2/?reminder_delta=60')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        data = self.wrap_content(
            output_text, replacements=[
                (r'UID:.*\n', 'UID:DUMMY_UID\r\n'),
                (r'DTSTAMP:.*\n', 'DTSTAMP:20181221T120122Z\r\n'),
            ]
        )
        # Newer python-vobject in the DTSTAMP field
        if "DTSTAMP" in data:
            string = "DTSTAMP:20181221T120122Z\r\nORGANIZER"
            if six.PY3:
                string = "DTSTAMP:20181221T120122Z\nORGANIZER"
            expected_data = expected_data.replace("ORGANIZER", string)

        if six.PY3:
            data = data.replace("\r\n", "\n")
        self.assertEqual(data, expected_data)

        # Test non numeric value for numeric data
        output = self.app.get('/ical/calendar/meeting/2/?reminder_delta=foo')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertNotIn('VALARM', output_text)
        self.assertEqual(data, expected_data)

        # Test with a reminder_delta value not in the default choice
        output = self.app.get('/ical/calendar/meeting/2/?reminder_delta=150')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('VALARM', output_text)
        self.assertIn('TRIGGER:-PT2H30M', output_text)

    def test_view_meeting(self):
        """ Test the view_meeting function. """
        self.__setup_db()

        output = self.app.get('/meeting/5/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>Meeting "test-meeting-st-1" - Fedocal</title>',
            output_text)
        self.assertIn(
            '<h2 class="orange">Meeting "test-meeting-st-1"</h2>',
            output_text)
        self.assertIn(
            'This is a test meeting at the same time',
            output_text)
        self.assertIn('iCal export', output_text)
        self.assertIn(
            '<select id="ical-meeting-export-reminder-at"',
            output_text)

    def test_view_meeting_page(self):
        """ Test the view_meeting_page function. """
        self.__setup_db()

        output = self.app.get('/meeting/5/1/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>Meeting "test-meeting-st-1" - Fedocal</title>',
            output_text)
        self.assertIn(
            '<h2 class="orange">Meeting "test-meeting-st-1"</h2>',
            output_text)
        self.assertIn(
            'This is a test meeting at the same time',
            output_text)
        self.assertIn(
            '<a href="/ical/calendar/meeting/5/"',
            output_text)

        output = self.app.get('/meeting/5/0/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertNotIn(
            '<title>Meeting "test-meeting-st-1" - Fedocal</title>',
            output_text)
        self.assertIn(
            '<h2 class="orange">Meeting "test-meeting-st-1"</h2>',
            output_text)
        self.assertIn(
            'This is a test meeting at the same time',
            output_text)
        self.assertIn(
            '<a href="/ical/calendar/meeting/5/"',
            output_text)

        # Invalid from_date
        output = self.app.get('/meeting/5/0/?from_date=foobar')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertNotIn(
            '<title>Meeting "test-meeting-st-1" - Fedocal</title>',
            output_text)
        self.assertIn(
            '<h2 class="orange">Meeting "test-meeting-st-1"</h2>',
            output_text)
        self.assertIn(
            'This is a test meeting at the same time',
            output_text)
        self.assertIn(
            '<a href="/ical/calendar/meeting/5/"',
            output_text)

        # Valid from_date
        output = self.app.get(
            '/meeting/5/0/?from_date=%s' % TODAY.strftime('%Y-%m-%d'))
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertNotIn(
            '<title>Meeting "test-meeting-st-1" - Fedocal</title>',
            output_text)
        self.assertIn(
            '<h2 class="orange">Meeting "test-meeting-st-1"</h2>',
            output_text)
        self.assertIn(
            'This is a test meeting at the same time',
            output_text)
        self.assertIn(
            '<a href="/ical/calendar/meeting/5/"',
            output_text)

        output = self.app.get('/meeting/50/0/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            'class="errors">No meeting could be found for this identifier</',
            output_text)

    def test_is_admin(self):
        """ Test the is_admin function. """
        app = flask.Flask('fedocal')

        with app.test_request_context():
            flask.g.fas_user = None
            self.assertFalse(fedocal.is_admin())
            flask.g.fas_user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
            self.assertTrue(fedocal.is_admin())

    def test_is_calendar_admin(self):
        """ Test the is_calendar_admin function. """
        self.__setup_db()
        app = flask.Flask('fedocal')
        calendar = model.Calendar.by_id(self.session, 'test_calendar')

        with app.test_request_context():
            # No fas user
            flask.g.fas_user = None
            self.assertFalse(fedocal.is_calendar_admin(calendar))

            # User is in the wrong group
            flask.g.fas_user = FakeUser(['gitr2spec'])
            self.assertFalse(fedocal.is_calendar_admin(calendar))

            # User is admin
            flask.g.fas_user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
            self.assertTrue(fedocal.is_calendar_admin(calendar))

            # User is in the right group
            flask.g.fas_user = FakeUser(['infrastructure-main2'])
            self.assertTrue(fedocal.is_calendar_admin(calendar))

            # Calendar has no admin specified
            calendar = model.Calendar.by_id(self.session, 'test_calendar3')
            flask.g.fas_user = FakeUser(['gitr2spec'])
            self.assertFalse(fedocal.is_calendar_admin(calendar))

    def test_view_meeting_page_dst(self):
        """ Test the view_meeting_page function accross the DST time change
        """
        # Create calendar
        obj = model.Calendar(
            calendar_name='test_calendar',
            calendar_contact='test@example.com',
            calendar_description='This is a test calendar',
            calendar_editor_group='fi-apprentice',
            calendar_admin_group='infrastructure-main2')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Add a meeting
        mdate = date(2017, 1, 2)
        obj = model.Meeting(  # id:1
            meeting_name='Fedora-fr-test-meeting',
            meeting_date=mdate,
            meeting_date_end=mdate,
            meeting_time_start=time(9, 00),
            meeting_time_stop=time(10, 00),
            meeting_timezone='America/New_York',
            meeting_information='This is a test meeting',
            calendar_name='test_calendar',
            recursion_frequency=7,
            recursion_ends=mdate + timedelta(days=365)
        )
        obj.save(self.session)
        obj.add_manager(self.session, 'pingou, shaiton,')
        self.session.commit()
        self.assertNotEqual(obj, None)

        # Winter time
        output = self.app.get('/meeting/1/?from_date=2017-02-27')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>Meeting "Fedora-fr-test-meeting" - Fedocal</title>',
            output_text)
        self.assertIn(
            'Mon, February 27, 2017 - 14:00 UTC',
            output_text)
        self.assertIn(
            'Mon, February 27, 2017 - 15:00:00 UTC',
            output_text)

        # Summer time
        output = self.app.get('/meeting/1/?from_date=2017-03-13')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>Meeting "Fedora-fr-test-meeting" - Fedocal</title>',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 13:00 UTC', output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 14:00 UTC', output_text)

        # Summer time in the US
        output = self.app.get(
            '/meeting/1/?from_date=2017-03-13&tzone=America/New_York')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>Meeting "Fedora-fr-test-meeting" - Fedocal</title>',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 13:00:00 UTC',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 14:00:00 UTC',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 09:00 America/New_York',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 10:00 America/New_York',
            output_text)

        # Summer time in the US but not in Europe
        output = self.app.get(
            '/meeting/1/?from_date=2017-03-13&tzone=Europe/Paris')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>Meeting "Fedora-fr-test-meeting" - Fedocal</title>',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 13:00:00 UTC',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 14:00:00 UTC',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 14:00 Europe/Paris',
            output_text)
        self.assertIn(
            'Mon, March 13, 2017 - 15:00 Europe/Paris',
            output_text)

        # Winter time again
        output = self.app.get('/meeting/1/?from_date=2017-11-20')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>Meeting "Fedora-fr-test-meeting" - Fedocal</title>',
            output_text)
        self.assertIn(
            'Mon, November 20, 2017 - 14:00 UTC',
            output_text)
        self.assertIn(
            'Mon, November 20, 2017 - 15:00 UTC',
            output_text)

    def test_is_calendar_manager(self):
        """ Test the is_calendar_manager function. """
        self.__setup_db()
        app = flask.Flask('fedocal')
        calendar = model.Calendar.by_id(self.session, 'test_calendar')

        with app.test_request_context():
            # No user
            flask.g.fas_user = None
            self.assertFalse(fedocal.is_calendar_manager(calendar))

            # User in the wrong group
            flask.g.fas_user = FakeUser(['gitr2spec'])
            self.assertFalse(fedocal.is_calendar_manager(calendar))

            # User is admin
            flask.g.fas_user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
            self.assertTrue(fedocal.is_calendar_manager(calendar))

            # User in the right group
            flask.g.fas_user = FakeUser(['fi-apprentice'])
            self.assertTrue(fedocal.is_calendar_manager(calendar))

            calendar = model.Calendar.by_id(self.session, 'test_calendar3')

            # Calendar has no editors set
            flask.g.fas_user = FakeUser(['gitr2spec'])
            self.assertTrue(fedocal.is_calendar_manager(calendar))

    def test_is_meeting_manager(self):
        """ Test the is_meeting_manager function. """
        self.__setup_db()
        app = flask.Flask('fedocal')
        meeting = model.Meeting.by_id(self.session, 1)

        with app.test_request_context():
            # No user
            flask.g.fas_user = None
            self.assertFalse(fedocal.is_meeting_manager(meeting))

            # User is not one of the managers
            flask.g.fas_user = FakeUser(['gitr2spec'])
            flask.g.fas_user.username = 'kevin'
            self.assertFalse(fedocal.is_meeting_manager(meeting))

            # User is one of the manager
            flask.g.fas_user = FakeUser(['gitr2spec'])
            self.assertFalse(fedocal.is_meeting_manager(meeting))

    def test_get_timezone(self):
        """ Test the get_timezone function. """
        app = flask.Flask('fedocal')

        with app.test_request_context():
            flask.g.fas_user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
            self.assertEqual(fedocal.get_timezone(), 'Europe/Paris')

    def test_is_safe_url(self):
        """ Test the is_safe_url function. """
        app = flask.Flask('fedocal')

        with app.test_request_context():
            self.assertTrue(fedocal.is_safe_url('http://localhost'))

            self.assertTrue(fedocal.is_safe_url('https://localhost'))

            self.assertTrue(fedocal.is_safe_url('http://localhost/test'))

            self.assertFalse(
                fedocal.is_safe_url('http://fedoraproject.org/'))

            self.assertFalse(
                fedocal.is_safe_url('https://fedoraproject.org/'))

    @flask10_only
    def test_auth_login(self):
        """ Test the auth_login function. """
        self.__setup_db()
        user = FakeUser([], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/login/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn('<title>Home - Fedocal</title>', output_text)

    def test_locations(self):
        """ Test the locations function. """
        self.__setup_db()

        output = self.app.get('/locations/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('<h2>Locations</h2>', output_text)
        self.assertIn('href="/location/EMEA/">', output_text)
        self.assertIn(
            '<span class="calendar_name">EMEA</span>', output_text)
        self.assertIn('href="/location/NA/">', output_text)
        self.assertIn(
            '<span class="calendar_name">NA</span>', output_text)

    def test_location(self):
        """ Test the location function. """
        self.__setup_db()

        output = self.app.get('/location/EMEA')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/location/EMEA', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>EMEA - Fedocal</title>', output_text)
        self.assertIn('<a href="/location/EMEA/">', output_text)
        self.assertIn('title="Previous week">', output_text)
        self.assertIn('title="Next week">', output_text)
        self.assertIn(
            '<input type="hidden" name="location" value="EMEA"/>',
            output_text)

        output = self.app.get('/location/NA/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>NA - Fedocal</title>', output_text)
        self.assertIn('<a href="/location/NA/">', output_text)
        self.assertIn('title="Previous week">', output_text)
        self.assertIn('title="Next week">', output_text)
        self.assertIn(
            '<input type="hidden" name="location" value="NA"/>',
            output_text)

        output = self.app.get('/location/foobar/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            'class="errors">No location named foobar could be found</',
            output_text)

    @flask10_only
    def test_admin(self):
        """ Test the admin function. """
        user = None
        with user_set(fedocal.APP, user):
            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn('<title>Home - Fedocal</title>', output_text)

        user = FakeUser(['test'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '"errors">You are not a fedocal admin, you are not allowed '
                'to access the admin part.</', output_text)

        user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Admin - Fedocal</title>', output_text)
            self.assertIn(
                '<h2>Admin interface</h2>', output_text)
            self.assertIn(
                '<option value="delete">Delete</option>', output_text)

            output = self.app.get(
                '/admin/?calendar=test_calendar&action=edit',
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Home - Fedocal</title>', output_text)
            self.assertIn(
                '<li class="errors">No calendar named test_calendar could '
                'be found</li>', output_text)

            self.__setup_db()

            output = self.app.get(
                '/admin/?calendar=test_calendar&action=edit',
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Edit calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<h2>Edit calendar "test_calendar"</h2>', output_text)
            self.assertIn(
                'type="text" value="test_calendar"></td>', output_text)

            output = self.app.get(
                '/admin/?calendar=test_calendar&action=delete',
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Delete calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<h4>Calendar: test_calendar</h4>', output_text)
            self.assertIn(
                'value="Delete">', output_text)

    @flask10_only
    def test_add_calendar(self):
        """ Test the add_calendar function. """
        user = None
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            # discoveryfailure happens if there is no network
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in output_text or 'discoveryfailure' in output_text)

        user = FakeUser(['test'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '"errors">You are not a fedocal admin, you are not allowed '
                'to add calendars.</', output_text)

        user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Add calendar - Fedocal</title>', output_text)
            self.assertIn(
                'for="calendar_name">Calendar</label>', output_text)
            self.assertIn(
                'contact">Contact email', output_text)
            self.assertEqual(
                output_text.count('<span class="required">*</span>'), 3)

            csrf_token = output_text.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # calendar should have a name
            data = {
                'calendar_contact': 'election1',
                'calendar_status': 'Enabled',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<td>This field is required.</td>', output_text)

            # Works
            data = {
                'calendar_name': 'election1',
                'calendar_contact': 'election1',
                'calendar_status': 'Enabled',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="message">Calendar added</li>', output_text)

            # This calendar already exists
            data = {
                'calendar_name': 'election1',
                'calendar_contact': 'election1',
                'calendar_status': 'Enabled',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '="errors">Could not add this calendar to the database</',
                output_text)

    @flask10_only
    def test_delete_calendar(self):
        """ Test the delete_calendar function. """
        self.__setup_db()

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/delete/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertTrue(
                '<li class="errors">You are not a fedocal admin, you are not'
                ' allowed to delete the calendar.</l',
                output_text)
            self.assertIn('<title>Home - Fedocal</title>', output_text)

        user = FakeUser(['packager'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/delete/50/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '"errors">No calendar named 50 could be found</',
                output_text)
            self.assertIn('<title>Home - Fedocal</title>', output_text)

            output = self.app.get('/calendar/delete/test_calendar/')
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Delete calendar - Fedocal</title>', output_text)
            self.assertIn(
                "Are you positively sure that's what you want to do?",
                output_text)
            self.assertIn(
                'name="confirm_delete" type="checkbox" value="y"><label',
                output_text)

            # No data
            data = {}

            output = self.app.post('/calendar/delete/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Delete calendar - Fedocal</title>', output_text)
            self.assertIn(
                "Are you positively sure that's what you want to do?",
                output_text)
            self.assertIn(
                'name="confirm_delete" type="checkbox" value="y"><label',
                output_text)

            csrf_token = output_text.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # No delete
            data = {
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/delete/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn('<title>Home - Fedocal</title>', output_text)
            self.assertIn(
                '<span class="calendar_name">test_calendar</span>',
                output_text)

            # Delete
            data = {
                'confirm_delete': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/delete/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Home - Fedocal</title>', output_text)
            self.assertIn(
                '<li class="message">Calendar deleted</li>',
                output_text)
            self.assertNotIn(
                '<span class="calendar_name">test_calendar</span>',
                output_text)

    @flask10_only
    def test_clear_calendar(self):
        """ Test the clear_calendar function. """
        self.__setup_db()

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/clear/1/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">No calendar named 1 could be found</li',
                output_text)

            output = self.app.get('/calendar/clear/test_calendar/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">You are not an admin of this calendar, '
                'you are not allowed to clear the calendar.</l',
                output_text)
            self.assertIn(
                '<title>Home - Fedocal</title>', output_text)

        user = FakeUser(['packager'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/clear/test_calendar/')
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Clear calendar - Fedocal</title>', output_text)
            self.assertIn(
                "Are you positively sure that's what you want to do?",
                output_text)
            self.assertIn(
                'name="confirm_delete" type="checkbox" value="y"><label',
                output_text)
            self.assertIn(
                '>Yes I want to clear this calendar</label>', output_text)

            # No data
            data = {}

            output = self.app.post('/calendar/clear/test_calendar/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Clear calendar - Fedocal</title>', output_text)
            self.assertIn(
                "Are you positively sure that's what you want to do?",
                output_text)
            self.assertIn(
                'name="confirm_delete" type="checkbox" value="y"><label',
                output_text)

            csrf_token = output_text.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # No delete
            data = {
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/clear/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<title>test_calendar - Fedocal</title>', output_text)

            # Delete
            data = {
                'confirm_delete': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/clear/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<title>test_calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<li class="message">Calendar cleared</li>',
                output_text)

    @flask10_only
    def test_edit_calendar(self):
        """ Test the edit_calendar function. """
        self.__setup_db()

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/edit/test_calendar/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">You are not a fedocal admin, you are '
                'not allowed to edit the calendar.</li>', output_text)
            self.assertIn(
                '<title>Home - Fedocal</title>', output_text)

        user = FakeUser(['packager'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/edit/1/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">No calendar named 1 could be found</li',
                output_text)

            output = self.app.get('/calendar/edit/test_calendar/')
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Edit calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<h2>Edit calendar "test_calendar"</h2>', output_text)
            self.assertIn(
                'class="submit positive button" value="Edit">',
                output_text)

            # No data
            data = {}

            output = self.app.post('/calendar/edit/test_calendar/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Edit calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<h2>Edit calendar "test_calendar"</h2>', output_text)
            self.assertIn(
                'class="submit positive button" value="Edit">',
                output_text)

            csrf_token = output_text.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # No info except the csrf token
            data = {
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/edit/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertEqual(
                output_text.count('<td>This field is required.</td>'), 2)
            self.assertIn(
                '<h2>Edit calendar "test_calendar"</h2>',
                output_text)
            self.assertIn(
                'class="submit positive button" value="Edit">',
                output_text)

            # Edit
            data = {
                'calendar_name': 'Election1',
                'calendar_contact': 'election1',
                'calendar_status': 'Enabled',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/edit/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Election1 - Fedocal</title>', output_text)
            self.assertIn(
                '<li class="message">Calendar updated</li>',
                output_text)
            self.assertNotIn(
                '<span class="calendar_name">test_calendar</span>',
                output_text)
            self.assertNotIn(
                '<span class="calendar_name">election1</span>',
                output_text)

    @flask10_only
    def test_auth_logout(self):
        """ Test the auth_logout function. """
        user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/logout/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn('<title>Home - Fedocal</title>', output_text)
            self.assertIn(
                '<li class="message">You have been logged out</li>',
                output_text)

        user = None
        with user_set(fedocal.APP, user):
            output = self.app.get('/logout/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn('<title>Home - Fedocal</title>', output_text)
            self.assertNotIn(
                '<li class="message">You have been logged out</li>',
                output_text)

    @flask10_only
    def test_my_meetings(self):
        """ Test the my_meetings function. """
        self.__setup_db()
        user = FakeUser([], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/mine/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '"errors">You must be in one more group than the CLA</li>',
                output_text)

        user = FakeUser()
        user.cla_done=False
        with user_set(fedocal.APP, user):
            output = self.app.get('/mine/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn('<title>Home - Fedocal</title>', output_text)

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/mine/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>My meetings - Fedocal</title>', output_text)
            self.assertIn(
                '<td> Full-day meeting </td>', output_text)
            self.assertIn(
                '<td> test-meeting2 </td>', output_text)
            self.assertIn(
                '<td> Test meeting with reminder </td>', output_text)

    @flask10_only
    def test_add_meeting(self):
        """ Test the add_meeting function. """
        self.__setup_db()
        user = FakeUser(['gitr2spec'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar_test/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '"errors">No calendar named calendar_test could be found</',
                output_text)

            output = self.app.get('/test_calendar/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">You are not one of the editors of this '
                'calendar, or one of its admins, you are not allowed to add'
                ' new meetings.</li>', output_text)
            self.assertIn(
                '<title>test_calendar - Fedocal</title>', output_text)

        user = FakeUser(['fi-apprentice'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/test_calendar/add/')
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Add meeting - Fedocal</title>', output_text)
            self.assertIn(
                'meeting_name">Meeting name</label>', output_text)
            self.assertIn(
                'for="meeting_date">Date</label>', output_text)
            self.assertEqual(
                output_text.count('<span class="required">*</span>'), 5)

            csrf_token = output_text.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Meeting should have a name
            data = {
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<td>This field is required.</td>', output_text)

            # Format of the start time wrong
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': '13',
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertTrue(
                '<td>Time must be of type &HH:MM&#34;</td>' in output_text
                or
                '<td>Time must be of type "HH:MM"</td>' in output_text
            )

            # Start time should have integer
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': '65:12',
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertTrue(
                '<td>Time must be of type &HH:MM&#34;</td>' in output_text
                or
                '<td>Time must be of type "HH:MM"</td>' in output_text
            )

            # End date earlier than the start date
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_date_end': TODAY - timedelta(days=1),
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="warnings">The start date of your meeting is '
                'later than the stop date.</li>', output_text)
            self.assertIn(
                '<title>Add meeting - Fedocal</title>', output_text)

            # Invalid location
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'meeting_location': '#fedora-meeting',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<td>Please use channel@server format!</td>', output_text)
            self.assertIn(
                '<title>Add meeting - Fedocal</title>', output_text)

            # Works
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="message">Meeting added</li>', output_text)
            self.assertIn(
                'href="/meeting/16/?from_date=', output_text)
            self.assertNotIn(
                'href="/meeting/17/?from_date=', output_text)

            # Works - with a wiki_link
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'wiki_link': 'http://fedoraproject.org/wiki',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="message">Meeting added</li>', output_text)
            self.assertIn(
                'href="/meeting/17/?from_date=', output_text)
            self.assertNotIn(
                'href="/meeting/18/?from_date=', output_text)

            # Calendar disabled
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar_disabled/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar_disabled - Fedocal</title>'
               , output_text)
            self.assertIn(
                '<li class="errors">This calendar is &#34;Disabled&#34;, '
                'you are not allowed to add meetings anymore.</li>'
               , output_text)

            # Fails - with an invalid email as recipient of the reminder
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'reminder_from': 'pingou@fp.o',
                'reminder_who': 'pingou@fp.org',
                'remind_when': 'H-12',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<h2>New meeting</h2>', output_text)
            self.assertIn(
                '<td>Invalid email address.</td>', output_text)

            # Fails - one of the two email specified as recipient of the
            # reminder is invalid
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'reminder_from': 'pingou@fp.o',
                'reminder_who': 'pingou@fp.org, pingou@fp.o',
                'remind_when': 'H-12',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<h2>New meeting</h2>', output_text)
            self.assertIn(
                '<td>Invalid email address.</td>', output_text)

            # Works - with one email as recipient of the reminder
            data = {
                'meeting_name': 'Reminder',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'reminder_from': 'pingou@fp.org',
                'reminder_who': 'pingou@fp.org',
                'remind_when': 'H-12',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="message">Meeting added</li>', output_text)
            self.assertIn(
                'href="/meeting/17/?from_date=', output_text)
            self.assertIn(
                'href="/meeting/18/?from_date=', output_text)
            self.assertIn(
                'Reminder', output_text)
            self.assertNotIn(
                'href="/meeting/19/?from_date=', output_text)

            # Works - with two emails as recipient of the reminder
            data = {
                'meeting_name': 'Reminder2',
                'meeting_date': TODAY,
                'meeting_time_start': time(15, 0),
                'meeting_time_stop': time(16, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'reminder_from': 'pingou@fp.org',
                'reminder_who': 'pingou@fp.org,pingou@p.fr',
                'remind_when': 'H-12',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/test_calendar/add/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="message">Meeting added</li>', output_text)
            self.assertIn(
                'href="/meeting/18/?from_date=', output_text)
            self.assertIn(
                'href="/meeting/19/?from_date=', output_text)
            self.assertIn(
                'Reminder2', output_text)
            self.assertNotIn(
                'href="/meeting/20/?from_date=', output_text)

    @flask10_only
    def test_edit_meeting(self):
        """ Test the edit_meeting function. """
        self.__setup_db()
        user = FakeUser(['gitr2spec'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/edit/50/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                'class="errors">The meeting #50 could not be found</li>',
                output_text)
            self.assertIn('<title>Home - Fedocal</title>', output_text)

            output = self.app.get('/meeting/edit/3/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">You are not one of the manager of this '
                'meeting, or an admin, you are not allowed to edit it.</li>',
                output_text)
            self.assertIn(
                '<title>Meeting "test-meeting23h59" - Fedocal</title>',
                output_text)

        user = FakeUser(['fi-apprentice'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/edit/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">You are not one of the manager of this '
                'meeting, or an admin, you are not allowed to edit it.</li>',
                output_text)
            self.assertIn(
                '<title>Meeting "Fedora-fr-test-meeting" - Fedocal</title>',
                output_text)

        user = FakeUser(['fi-apprentice'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/edit/1/')
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Edit meeting - Fedocal</title>', output_text)
            self.assertIn(
                'meeting_name">Meeting name</label>', output_text)
            self.assertIn(
                'for="meeting_date">Date</label>', output_text)
            self.assertEqual(
                output_text.count('<span class="required">*</span>'), 6)

            csrf_token = output_text.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Meeting should have a name
            data = {
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/edit/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<td>This field is required.</td>', output_text)

            # No calendar provided
            data = {
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_date_end': TODAY - timedelta(days=1),
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/edit/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<td>Not a valid choice</td>', output_text)
            self.assertIn(
                '<title>Edit meeting - Fedocal</title>', output_text)

            # End date earlier than the start date
            data = {
                'calendar_name': 'test_calendar',
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_date_end': TODAY - timedelta(days=1),
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/edit/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="warnings">The start date of your meeting is '
                'later than the stop date.</li>', output_text)
            self.assertIn(
                '<title>Edit meeting - Fedocal</title>', output_text)

            # Works
            data = {
                'calendar_name': 'test_calendar',
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/edit/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="message">Meeting updated</li>', output_text)
            self.assertIn(
                '<title>Meeting "guess what?" - Fedocal</title>', output_text)

            # Calendar disabled
            data = {
                'calendar_name': 'test_calendar_disabled',
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/edit/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar_disabled - Fedocal</title>',
                output_text)
            self.assertIn(
                '<li class="errors">This calendar is &#34;Disabled&#34;, '
                'you are not allowed to add meetings to it anymore.</li>',
                output_text)

        # Add a meeting to the test_calendar_disabled calendar
        obj = model.Meeting(  # id:16
            meeting_name='Full-day meeting2',
            meeting_date=TODAY + timedelta(days=2),
            meeting_date_end=TODAY + timedelta(days=3),
            meeting_time_start=time(0, 00),
            meeting_time_stop=time(23, 59),
            meeting_information='Full day meeting 2',
            calendar_name='test_calendar_disabled',
            full_day=True)
        obj.add_manager(self.session, ['toshio'])
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        user = FakeUser(['fi-apprentice'], username='pingou')
        with user_set(fedocal.APP, user):
             # Calendar disabled
            data = {
                'calendar_name': 'test_calendar_disabled',
                'meeting_name': 'guess what?',
                'meeting_date': TODAY,
                'meeting_time_start': time(13, 0),
                'meeting_time_stop': time(14, 0),
                'meeting_timezone': 'Europe/Paris',
                'frequency': '',
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/edit/16/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar_disabled - Fedocal</title>',
                output_text)
            self.assertIn(
                '<li class="errors">This calendar is &#34;Disabled&#34;, '
                'you are not allowed to edit its meetings anymore.</li>',
                output_text)

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedocal.APP, user):
            # Recurring meeting
            output = self.app.get(
                '/meeting/edit/12/?from_date=foor', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Edit meeting - Fedocal</title>', output_text)
            self.assertIn(
                '<h2>Edit meeting "Another past test meeting"</h2>',
                output_text)
            self.assertIn(
                'meeting_name">Meeting name</label>', output_text)
            self.assertIn(
                'for="meeting_date">Date</label>', output_text)
            self.assertEqual(
                output_text.count('<span class="required">*</span>'), 6)

            output = self.app.get(
                '/meeting/edit/12/?from_date=%s' % TODAY.strftime('%Y-%m-%d'),
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Edit meeting - Fedocal</title>', output_text)
            self.assertIn(
                '<h2>Edit meeting "Another past test meeting"</h2>',
                output_text)
            self.assertIn(
                'meeting_name">Meeting name</label', output_text)
            self.assertIn(
                'for="meeting_date">Date</label>', output_text)
            self.assertEqual(
                output_text.count('<span class="required">*</span>'), 6)

    @flask10_only
    def test_delete_meeting(self):
        """ Test the delete_meeting function. """
        self.__setup_db()
        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/delete/50/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '"errors">No meeting with this identifier could be found.</',
                output_text)
            self.assertIn('<title>Home - Fedocal</title>', output_text)

            output = self.app.get('/meeting/delete/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">You are not one of the manager of this '
                'meeting, or an admin, you are not allowed to delete it.</l',
                output_text)
            self.assertIn(
                '<title>Meeting "Fedora-fr-test-meeting" - Fedocal</title>',
                output_text)

        user = FakeUser(['fi-apprentice'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/delete/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">You are not one of the manager of this '
                'meeting, or an admin, you are not allowed to delete it.</l',
                output_text)
            self.assertIn(
                '<title>Meeting "Fedora-fr-test-meeting" - Fedocal</title>',
                output_text)

        user = FakeUser(['fi-apprentice'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/delete/1/')
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Delete meeting - Fedocal</title>', output_text)
            self.assertIn(
                '<h4>Meeting: Fedora-fr-test-meeting</h4>',
                output_text)
            self.assertIn(
                "positively sure that's what you want to do?",
                output_text)
            self.assertIn(
                'name="confirm_delete" type="checkbox" value="y"><label',
                output_text)
            self.assertIn(
                '<input id="confirm_button" type="submit" class="submit positi',
                output_text)

            csrf_token = output_text.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Invalid from_date
            output = self.app.get(
                '/meeting/delete/1/?from_date=foobar', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Delete meeting - Fedocal</title>', output_text)
            self.assertIn(
                '<h4>Meeting: Fedora-fr-test-meeting</h4>',
                output_text)
            self.assertIn(
                "positively sure that's what you want to do?",
                output_text)
            self.assertIn(
                'name="confirm_delete" type="checkbox" value="y"><label',
                output_text)

            # Do not delete
            data = {
                #'confirm_delete': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/delete/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar - Fedocal</title>', output_text)

            # Delete
            data = {
                'confirm_delete': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/delete/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<li class="message">Meeting deleted</li>', output_text)

            # Delete all
            data = {
                'confirm_delete': True,
                'confirm_futher_delete': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/delete/8/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar - Fedocal</title>', output_text)
            self.assertIn(
                '<li class="message">Meeting deleted</li>', output_text)

        # Add a meeting to the test_calendar_disabled calendar
        obj = model.Meeting(  # id:16
            meeting_name='Full-day meeting2',
            meeting_date=TODAY + timedelta(days=2),
            meeting_date_end=TODAY + timedelta(days=3),
            meeting_time_start=time(0, 00),
            meeting_time_stop=time(23, 59),
            meeting_information='Full day meeting 2',
            calendar_name='test_calendar_disabled',
            full_day=True)
        obj.add_manager(self.session, ['toshio'])
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

        user = FakeUser(['fi-apprentice'], username='pingou')
        with user_set(fedocal.APP, user):
            # Delete all
            data = {
                'confirm_delete': True,
                'confirm_futher_delete': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/delete/16/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>test_calendar_disabled - Fedocal</title>',
                output_text)
            self.assertTrue(
                '<li class="errors">This calendar is &#34;Disabled&#34;, '
                'you are not allowed to delete its meetings anymore.</li>',
                output_text)

    def test_update_tz(self):
        """ Test the update_tz function. """
        self.__setup_db()

        output = self.app.get('/updatetz/?tzone=Europe/Paris',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('<title>Home - Fedocal</title>', output_text)
        self.assertIn(
            '<li class="warnings">Invalid referred url</li>', output_text)

        output = self.app.get('/updatetz/',
                              follow_redirects=True)
        self.assertIn('<title>Home - Fedocal</title>', output_text)
        self.assertIn(
            '<li class="warnings">Invalid referred url</li>',
            output_text)

    def test_search(self):
        """ Test the search function. """
        self.__setup_db()

        # With '*'
        output = self.app.get('/search/?keyword=*meeting3*',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('<title>Search - Fedocal</title>', output_text)
        self.assertIn(
            '<p>Result of your search for "*meeting3*"</p>',
            output_text)
        self.assertIn('href="/meeting/4/?from_date=', output_text)
        self.assertIn(
            '<p>Test meeting with past end_recursion....</p>',
            output_text)

        # Without any '*'
        output = self.app.get('/search/?keyword=meeting3',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('<title>Search - Fedocal</title>', output_text)
        self.assertIn(
            '<p>Result of your search for "meeting3*"</p>', output_text)
        self.assertNotIn('href="/meeting/4/?from_date=', output_text)
        self.assertNotIn('href="/meeting/4/', output_text)
        self.assertNotIn(
            'd> <p>Test meeting with past end_recursion.</p> </',
            output_text)

        output = self.app.get('/search/',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('<title>Home - Fedocal</title>', output_text)
        self.assertIn(
            'class="errors">No keyword provided for the search</',
            output_text)

    def test_goto(self):
        """ Test the goto function. """
        self.__setup_db()

        data = {
            'calendar': 'test_calendar',
            'view_type': 'calendar',
            'year': 2014,
            'month': 12,
            'day': 1,
        }

        output = self.app.get('/goto/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn('<title>Home - Fedocal</title>', output_text)
        self.assertIn(
            '<li class="errors">No calendar specified</li>', output_text)

        output = self.app.get('/goto/?calendar=test_calendar',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get('/goto/?calendar=test_calendar&month=3',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get('/goto/?calendar=test_calendar&month=3&day=1',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get(
            '/goto/?calendar=test_calendar&year=2010&month=3&day=1',
            follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get(
            '/goto/?calendar=test_calendar&year=2010&month=3&day=a',
            follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<li class="errors">Invalid date specified</li>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get(
            '/goto/?calendar=test_calendar&year=2010&month=a',
            follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<li class="errors">Invalid date specified</li>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get('/goto/?calendar=test_calendar&year=a',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<li class="errors">Invalid date specified</li>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get('/goto/?calendar=test_calendar&year=1870',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '="warnings">Dates before 1900 are not allowed</li',
            output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get('/goto/?calendar=test_calendar&type=list',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

        output = self.app.get('/goto/?calendar=test_calendar&type=foobar',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>test_calendar - Fedocal</title>', output_text)
        self.assertIn(
            '<p>This is a test calendar</p>', output_text)

    @flask10_only
    def test_upload_calendar(self):
        """ Test the upload_calendar function. """
        self.__setup_db()

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/upload/1/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">No calendar named 1 could be found</li',
                output_text)

            output = self.app.get('/calendar/upload/test_calendar/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<li class="errors">You are not an admin for this calendar, '
                'you are not allowed to upload a iCalendar file to it.</l',
                output_text)
            self.assertIn(
                '<title>Home - Fedocal</title>', output_text)

        user = FakeUser(['packager'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/upload/test_calendar/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertIn(
                '<title>Upload calendar - Fedocal</title>', output_text)
            self.assertIn('<h2>Upload calendar</h2>', output_text)

            csrf_token = output_text.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            with open(ICS_FILE, 'rb') as stream:
                data = {
                    'ics_file': stream,
                    'enctype': 'multipart/form-data',
                    'csrf_token': csrf_token,
                }
                output = self.app.post('/calendar/upload/test_calendar/',
                                       follow_redirects=True, data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                if '<li class="error">' not in output_text:
                    self.assertIn(
                        '<title>test_calendar - Fedocal</title>',
                        output_text)
                    self.assertIn(
                        '<p>This is a test calendar</p>', output_text)
                    self.assertIn(
                        'li class="message">Calendar uploaded</li>',
                        output_text)
                else:
                    self.assertIn(
                        '<li class="error">The submitted candidate has the '
                        'MIME type &#34;application/octet-stream&#34; which '
                        'is not an allowed MIME type</li>', output_text)

            with open(ICS_FILE_NOTOK, 'rb') as stream:
                data = {
                    'ics_file': stream,
                    'enctype': 'multipart/form-data',
                    'csrf_token': csrf_token,
                }
                output = self.app.post('/calendar/upload/test_calendar/',
                                       follow_redirects=True, data=data)
                self.assertEqual(output.status_code, 200)
                output_text = output.get_data(as_text=True)
                self.assertIn(
                    '<title>Upload calendar - Fedocal</title>',
                    output_text)
                self.assertIn(
                    '<li class="error">The submitted candidate has the file '
                    'extension &#34;txt&#34; which is not an allowed '
                    'format</li>', output_text)

    @flask10_only
    def test_markdown_preview(self):
        """ Test the markdown_preview function. """
        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/markdown/')
            self.assertEqual(output.status_code, 302)

            data = {
                'content': '``test``'
            }
            output = self.app.post('/markdown/', data=data)
            self.assertEqual(output.status_code, 200)
            output_text = output.get_data(as_text=True)
            self.assertEqual(output_text, ' <p><code>test</code></p> ')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Flasktests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
