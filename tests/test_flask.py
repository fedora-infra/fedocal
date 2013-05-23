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

import flask
import unittest
import sys
import os

from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedocal
import fedocal.fedocallib as fedocallib
from tests import Modeltests, FakeUser


# pylint: disable=E1103
class Flasktests(Modeltests):
    """ Flask application tests. """

    def __setup_db(self):
        """ Add a calendar and some meetings so that we can play with
        something. """
        from test_meeting import Meetingtests
        meeting = Meetingtests('test_init_meeting')
        meeting.session = self.session
        meeting.test_init_meeting()

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(Flasktests, self).setUp()

        fedocal.APP.config['TESTING'] = True
        fedocal.SESSION = self.session
        self.app = fedocal.APP.test_client()

    def test_index_empty(self):
        """ Test the index function. """
        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>Home - Fedocal</title>' in output.data)

    def test_index(self):
        """ Test the index function. """
        self.__setup_db()

        output = self.app.get('/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>Home - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

    def test_calendar(self):
        """ Test the calendar function. """
        self.__setup_db()

        output = self.app.get('/test_calendar')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/test_calendar', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title> test_calendar  - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/test_calendar2/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title> test_calendar2  - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

    def test_calendar_fullday(self):
        """ Test the calendar_fullday function. """
        self.__setup_db()

        today = date.today()
        output = self.app.get('/test_calendar/%s/%s/%s/' % (today.year,
            today.month, today.day))
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title> test_calendar  - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/test_calendar/%s/%s/%s' % (today.year,
            today.month, today.day))
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/test_calendar/%s/%s/%s/' % (today.year,
            today.month, today.day), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title> test_calendar  - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

    def test_calendar_list(self):
        """ Test the calendar_list function. """
        self.__setup_db()

        today = date.today()
        output = self.app.get('/list/test_calendar/%s/%s/%s/' % (
            today.year, today.month, today.day))
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title> test_calendar  - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/list/test_calendar/%s/%s/%s' % (
            today.year, today.month, today.day))
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/list/test_calendar/%s/%s/%s/' % (
            today.year, today.month, today.day), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title> test_calendar  - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/list/test_calendar/%s/%s/' % (
            today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title> test_calendar  - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

    def test_ical_out(self):
        """ Test the ical_out function. """
        self.__setup_db()

        output = self.app.get('/ical/test_calendar/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('BEGIN:VCALENDAR' in output.data)
        self.assertTrue('SUMMARY:test-meeting2' in output.data)
        self.assertTrue('DESCRIPTION:This is a test meeting with '\
            'recursion' in output.data)
        self.assertTrue('ORGANIZER:pingou' in output.data)
        self.assertEqual(output.data.count('BEGIN:VEVENT'), 45)
        self.assertEqual(output.data.count('END:VEVENT'), 45)

    def test_ical_all(self):
        """ Test the ical_all function. """
        self.__setup_db()

        output = self.app.get('/ical/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('BEGIN:VCALENDAR' in output.data)
        self.assertTrue('SUMMARY:test-meeting2' in output.data)
        self.assertTrue('DESCRIPTION:This is a test meeting with '\
            'recursion' in output.data)
        self.assertTrue('ORGANIZER:pingou' in output.data)
        self.assertEqual(output.data.count('BEGIN:VEVENT'), 50)
        self.assertEqual(output.data.count('END:VEVENT'), 50)

    def test_view_meeting(self):
        """ Test the view_meeting function. """
        self.__setup_db()

        output = self.app.get('/meeting/5/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title> test-meeting-st-1  - Fedocal</title>' \
            in output.data)
        self.assertTrue('<h4> Meeting: test-meeting-st-1</h4>' \
            in output.data)
        self.assertTrue('This is a test meeting at the same time' in
            output.data)

    def test_view_meeting_page(self):
        """ Test the view_meeting_page function. """
        self.__setup_db()

        output = self.app.get('/meeting/5/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title> test-meeting-st-1  - Fedocal</title>' \
            in output.data)
        self.assertTrue('<h4> Meeting: test-meeting-st-1</h4>' \
            in output.data)
        self.assertTrue('This is a test meeting at the same time' in
            output.data)

        output = self.app.get('/meeting/5/0/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('<title> test-meeting-st-1  - Fedocal</title>' \
            not in output.data)
        self.assertTrue('<h4> Meeting: test-meeting-st-1</h4>' \
            in output.data)
        self.assertTrue('This is a test meeting at the same time' in
            output.data)

    def test_is_admin(self):
        """ Test the is_admin function. """
        app = flask.Flask('fedocal')

        with app.test_request_context():
            flask.g.fas_user = None
            self.assertFalse(fedocal.is_admin())
            flask.g.fas_user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
            self.assertTrue(fedocal.is_admin())

    def test_get_timezone(self):
        """ Test the get_timezone. """
        app = flask.Flask('fedocal')

        with app.test_request_context():
            flask.g.fas_user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
            self.assertEqual(fedocal.get_timezone(), 'Europe/Paris')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Flasktests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
