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
import logging
import unittest
import sys
import os

from datetime import date
from datetime import time
from datetime import timedelta

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
        fedocal.APP.debug = True
        fedocal.APP.logger.handlers = []
        fedocal.APP.logger.setLevel(logging.CRITICAL)
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
        self.assertTrue('href="/test_calendar/">' in output.data)
        self.assertTrue('href="/test_calendar2/">' in output.data)
        self.assertTrue('href="/test_calendar4/">' in output.data)

    def test_calendar(self):
        """ Test the calendar function. """
        self.__setup_db()

        output = self.app.get('/test_calendar')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/test_calendar', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>test_calendar - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/test_calendar2/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>test_calendar2 - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/foorbar/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            'class="errors">No calendar named foorbar could not be found</'
            in output.data)

        output = self.app.get('/test_calendar2/?tzone=Europe/Paris',
                              follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>test_calendar2 - Fedocal</title>' in output.data)

    def test_location(self):
        """ Test the location calendar function. """
        self.__setup_db()

        output = self.app.get('/location/test')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/location/test/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>test - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

    def test_calendar_fullday(self):
        """ Test the calendar_fullday function. """
        self.__setup_db()

        today = date.today()
        output = self.app.get(
            '/test_calendar/%s/%s/%s/' % (
                today.year, today.month, today.day))
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>test_calendar - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get(
            '/test_calendar/%s/%s/%s' % (
                today.year, today.month, today.day))
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/test_calendar/%s/%s/%s/' % (
            today.year, today.month, today.day), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>test_calendar - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

    def test_calendar_list(self):
        """ Test the calendar_list function. """
        self.__setup_db()

        output = self.app.get('/list/test_calendar/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>test_calendar - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/list/foorbar/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            'class="errors">No calendar named foorbar could not be found</'
            in output.data)

        today = date.today()
        output = self.app.get('/list/test_calendar/%s/%s/%s/' % (
            today.year, today.month, today.day))
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>test_calendar - Fedocal</title>' in output.data)
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
            '<title>test_calendar - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/list/test_calendar/%s/%s/' % (
            today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count('<a class="event meeting_'), 12)
        self.assertEqual(output.data.count('<tr'), 20)
        self.assertTrue(
            '<title>test_calendar - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/list/test_calendar/%s/%s/?subject=Another'
            % (today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count('<a class="event meeting_'), 6)
        self.assertEqual(output.data.count('<tr'), 14)
        self.assertTrue(
            '<title>test_calendar - Fedocal</title>' in output.data)
        self.assertTrue(' <a href="/test_calendar/">' in output.data)
        self.assertTrue(' <a href="/test_calendar2/">' in output.data)
        self.assertTrue(' <a href="/test_calendar4/">' in output.data)

        output = self.app.get('/list/test_calendar/%s/%s/?subject=Another past'
            % (today.year, today.month), follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output.data.count('<a class="event meeting_'), 4)
        self.assertEqual(output.data.count('<tr'), 12)
        self.assertTrue(
            '<title>test_calendar - Fedocal</title>' in output.data)
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
        self.assertTrue(
            'DESCRIPTION:This is a test meeting with recursion'
            in output.data)
        self.assertTrue('ORGANIZER:pingou' in output.data)
        self.assertEqual(output.data.count('BEGIN:VEVENT'), 10)
        self.assertEqual(output.data.count('END:VEVENT'), 10)

        output = self.app.get('/ical/foorbar/')
        self.assertEqual(output.status_code, 404)

    def test_ical_all(self):
        """ Test the ical_all function. """
        self.__setup_db()

        output = self.app.get('/ical/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue('BEGIN:VCALENDAR' in output.data)
        self.assertTrue('SUMMARY:test-meeting2' in output.data)
        self.assertTrue(
            'DESCRIPTION:This is a test meeting with recursion'
            in output.data)
        self.assertTrue('ORGANIZER:pingou' in output.data)
        self.assertEqual(output.data.count('BEGIN:VEVENT'), 15)
        self.assertEqual(output.data.count('END:VEVENT'), 15)

    def test_view_meeting(self):
        """ Test the view_meeting function. """
        self.__setup_db()

        output = self.app.get('/meeting/5/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>Meeting test-meeting-st-1 - Fedocal</title>'
            in output.data)
        self.assertTrue(
            '<h2 class="orange"> Meeting: test-meeting-st-1</h2>'
            in output.data)
        self.assertTrue(
            'This is a test meeting at the same time'
            in output.data)

    def test_view_meeting_page(self):
        """ Test the view_meeting_page function. """
        self.__setup_db()

        output = self.app.get('/meeting/5/1/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>Meeting test-meeting-st-1 - Fedocal</title>'
            in output.data)
        self.assertTrue(
            '<h2 class="orange"> Meeting: test-meeting-st-1</h2>'
            in output.data)
        self.assertTrue(
            'This is a test meeting at the same time'
            in output.data)

        output = self.app.get('/meeting/5/0/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>Meeting test-meeting-st-1 - Fedocal</title>'
            not in output.data)
        self.assertTrue(
            '<h2 class="orange"> Meeting: test-meeting-st-1</h2>'
            in output.data)
        self.assertTrue(
            'This is a test meeting at the same time'
            in output.data)

        output = self.app.get('/meeting/50/0/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            'class="errors">No meeting could be found for this identifier</'
            in output.data)

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

    def test_auth_login(self):
        """ Test the auth_login function. """
        app = flask.Flask('fedocal')

        with app.test_request_context():
            flask.g.fas_user = FakeUser(['gitr2spec'])
            output = self.app.get('/login/')
            self.assertEqual(output.status_code, 200)

            output = self.app.get('/login/?next=http://localhost/')
            self.assertEqual(output.status_code, 200)

    @flask10_only
    def test_auth_login_logedin(self):
        """ Test the auth_login function. """
        self.__setup_db()
        user = FakeUser([], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/login/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Home - Fedocal</title>' in output.data)

    def test_locations(self):
        """ Test the locations function. """
        self.__setup_db()

        output = self.app.get('/locations/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<h2>Locations</h2>'
            in output.data)
        self.assertTrue('href="/location/EMEA/">' in output.data)
        self.assertTrue(
            '<span class="calendar_name">EMEA</span>' in output.data)
        self.assertTrue('href="/location/NA/">' in output.data)
        self.assertTrue(
            '<span class="calendar_name">NA</span>' in output.data)

    def test_location(self):
        """ Test the location function. """
        self.__setup_db()

        output = self.app.get('/location/EMEA')
        self.assertEqual(output.status_code, 301)

        output = self.app.get('/location/EMEA', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>EMEA - Fedocal</title>' in output.data)
        self.assertTrue('<a href="/location/EMEA/">' in output.data)
        self.assertTrue('title="Previous week">' in output.data)
        self.assertTrue('title="Next week">' in output.data)
        self.assertTrue(
            '<input type="hidden" name="location" value="EMEA"/>'
            in output.data)

        output = self.app.get('/location/NA/')
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            '<title>NA - Fedocal</title>' in output.data)
        self.assertTrue('<a href="/location/NA/">' in output.data)
        self.assertTrue('title="Previous week">' in output.data)
        self.assertTrue('title="Next week">' in output.data)
        self.assertTrue(
            '<input type="hidden" name="location" value="NA"/>'
            in output.data)

        output = self.app.get('/location/foobar/', follow_redirects=True)
        self.assertEqual(output.status_code, 200)
        self.assertTrue(
            'class="errors">No location named foobar could not be found</'
            in output.data)

    @flask10_only
    def test_admin(self):
        """ Test the admin function. """
        user = None
        with user_set(fedocal.APP, user):
            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Home - Fedocal</title>' in output.data)

        user = FakeUser(['test'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '"errors">You are not a fedocal admin, you are not allowed '
                'to access the admin part.</' in output.data)

        user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/admin/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Admin - Fedocal</title>' in output.data)
            self.assertTrue(
                '<h2>Admin interface</h2>' in output.data)
            self.assertTrue(
                '<option value="delete">Delete</option>' in output.data)

            output = self.app.get(
                '/admin/?calendar=test_calendar&action=edit',
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - Fedocal</title>' in output.data)
            self.assertTrue(
                '<li class="errors">No calendar named test_calendar could '
                'not be found</li>' in output.data)

            self.__setup_db()

            output = self.app.get(
                '/admin/?calendar=test_calendar&action=edit',
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Edit calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                '<h2>Edit calendar</h2>' in output.data)
            self.assertTrue(
                'type="text" value="test_calendar"></td>' in output.data)

            output = self.app.get(
                '/admin/?calendar=test_calendar&action=delete',
                follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Delete calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                '<h4> Calendar: test_calendar</h4>' in output.data)
            self.assertTrue(
                'value="Delete">' in output.data)

    @flask10_only
    def test_add_calendar(self):
        """ Test the add_calendar function. """
        user = None
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            # discoveryfailure happens if there is no network
            self.assertTrue(
                '<title>OpenID transaction in progress</title>'
                in output.data or 'discoveryfailure' in output.data)

        user = FakeUser(['test'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '"errors">You are not a fedocal admin, you are not allowed '
                'to add calendars.</' in output.data)

        user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Add calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                'for="calendar_name">Calendar <span class="error">*</span>'
                in output.data)
            self.assertTrue(
                'contact">Contact email <span class="error">*</span>'
                in output.data)

            csrf_token = output.data.split(
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
            self.assertTrue(
                '<td>This field is required.</td>' in output.data)

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
            self.assertTrue(
                '<li class="message">Calendar added</li>' in output.data)

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
            self.assertTrue(
                '="errors">Could not add this calendar to the database</'
                in output.data)

    @flask10_only
    def test_delete_calendar(self):
        """ Test the delete_calendar function. """
        self.__setup_db()

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/delete/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not a fedocal admin, you are not'
                ' allowed to delete the calendar.</l'
                in output.data)
            self.assertTrue(
                '<title>Home - Fedocal</title>'
                in output.data)

        user = FakeUser(['packager'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/delete/50/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '"errors">No calendar named 50 could not be found</'
                in output.data)
            self.assertTrue('<title>Home - Fedocal</title>' in output.data)

            output = self.app.get('/calendar/delete/test_calendar/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Delete calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                "Are you positively sure that's what you want to do?"
                in output.data)
            self.assertTrue(
                'name="confirm_delete" type="checkbox" value="y"><label'
                in output.data)

            # No data
            data = {}

            output = self.app.post('/calendar/delete/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Delete calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                "Are you positively sure that's what you want to do?"
                in output.data)
            self.assertTrue(
                'name="confirm_delete" type="checkbox" value="y"><label'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # No delete
            data = {
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/delete/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - Fedocal</title>' in output.data)
            self.assertTrue(
                '<span class="calendar_name">test_calendar</span>'
                in output.data)

            # Delete
            data = {
                'confirm_delete': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/delete/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - Fedocal</title>' in output.data)
            self.assertTrue(
                '<li class="message">Calendar deleted</li>'
                in output.data)
            self.assertFalse(
                '<span class="calendar_name">test_calendar</span>'
                in output.data)

    @flask10_only
    def test_clear_calendar(self):
        """ Test the clear_calendar function. """
        self.__setup_db()

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/clear/1/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No calendar named 1 could not be found</li'
                in output.data)

            output = self.app.get('/calendar/clear/test_calendar/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not an admin of this calendar, '
                'you are not allowed to clear the calendar.</l'
                in output.data)
            self.assertTrue(
                '<title>Home - Fedocal</title>'
                in output.data)

        user = FakeUser(['packager'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/clear/test_calendar/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Clear calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                "Are you positively sure that's what you want to do?"
                in output.data)
            self.assertTrue(
                'name="confirm_delete" type="checkbox" value="y"><label'
                in output.data)
            self.assertTrue(
                '>Yes I want to clear this calendar</label>' in output.data)

            # No data
            data = {}

            output = self.app.post('/calendar/clear/test_calendar/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Clear calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                "Are you positively sure that's what you want to do?"
                in output.data)
            self.assertTrue(
                'name="confirm_delete" type="checkbox" value="y"><label'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # No delete
            data = {
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/clear/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - Fedocal</title>' in output.data)
            self.assertTrue(
                '<span class="calendar_name">test_calendar</span>'
                in output.data)

            # Delete
            data = {
                'confirm_delete': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/clear/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Home - Fedocal</title>' in output.data)
            self.assertTrue(
                '<li class="message">Calendar cleared</li>'
                in output.data)
            self.assertTrue(
                '<span class="calendar_name">test_calendar</span>'
                in output.data)

    @flask10_only
    def test_edit_calendar(self):
        """ Test the edit_calendar function. """
        self.__setup_db()

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/edit/test_calendar/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not a fedocal admin, you are '
                'not allowed to edit the calendar.</li>' in output.data)
            self.assertTrue(
                '<title>Home - Fedocal</title>'
                in output.data)

        user = FakeUser(['packager'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/edit/1/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No calendar named 1 could not be found</li'
                in output.data)

            output = self.app.get('/calendar/edit/test_calendar/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Edit calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                "<h2>Edit calendar</h2>"
                in output.data)
            self.assertTrue(
                'class="submit positive button" value="Edit">'
                in output.data)

            # No data
            data = {}

            output = self.app.post('/calendar/edit/test_calendar/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Edit calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                "<h2>Edit calendar</h2>"
                in output.data)
            self.assertTrue(
                'class="submit positive button" value="Edit">'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # No info except the csrf token
            data = {
                'csrf_token': csrf_token,
            }

            output = self.app.post('/calendar/edit/test_calendar/',
                                   data=data, follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertEqual(
                output.data.count('<td>This field is required.</td>'), 2)
            self.assertTrue(
                "<h2>Edit calendar</h2>"
                in output.data)
            self.assertTrue(
                'class="submit positive button" value="Edit">'
                in output.data)

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
            self.assertTrue(
                '<title>Election1 - Fedocal</title>' in output.data)
            self.assertTrue(
                '<li class="message">Calendar updated</li>'
                in output.data)
            self.assertFalse(
                '<span class="calendar_name">test_calendar</span>'
                in output.data)
            self.assertFalse(
                '<span class="calendar_name">election1</span>'
                in output.data)

    @flask10_only
    def test_auth_logout(self):
        """ Test the auth_logout function. """
        user = FakeUser(fedocal.APP.config['ADMIN_GROUP'])
        with user_set(fedocal.APP, user):
            output = self.app.get('/logout/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Home - Fedocal</title>' in output.data)
            self.assertTrue(
                '<li class="message">You have been logged out</li>'
                in output.data)

        user = None
        with user_set(fedocal.APP, user):
            output = self.app.get('/logout/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Home - Fedocal</title>' in output.data)
            self.assertFalse(
                '<li class="message">You have been logged out</li>'
                in output.data)

    @flask10_only
    def test_my_meetings(self):
        """ Test the my_meetings function. """
        self.__setup_db()
        user = FakeUser([], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/mine/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '"errors">You must be in one more group than the CLA</li>'
                in output.data)

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/mine/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>My meeting - Fedocal</title>' in output.data)
            self.assertTrue(
                '<td> Full-day meeting </td>' in output.data)
            self.assertTrue(
                '<td> test-meeting2 </td>' in output.data)
            self.assertTrue(
                '<td> Test meeting with reminder </td>' in output.data)

    @flask10_only
    def test_add_meeting(self):
        """ Test the add_meeting function. """
        self.__setup_db()
        user = FakeUser(['gitr2spec'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar_test/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '"errors">No calendar named calendar_test could not be found</'
                in output.data)

            output = self.app.get('/test_calendar/add/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not one of the editors of this '
                'calendar, or one of its admins, you are not allowed to add'
                ' new meetings.</li>' in output.data)
            self.assertTrue(
                '<title>test_calendar - Fedocal</title>' in output.data)

        user = FakeUser(['fi-apprentice'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/test_calendar/add/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Add meeting - Fedocal</title>' in output.data)
            self.assertTrue(
                'meeting_name">Meeting name <span class="error">*</span></l'
                in output.data)
            self.assertTrue(
                'for="meeting_date">Date <span class="error">*</span></label'
                in output.data)

            csrf_token = output.data.split(
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
            self.assertTrue(
                '<td>This field is required.</td>' in output.data)

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
            self.assertTrue(
                '<td>Time must be of type &#34;HH:MM&#34;</td>'
                in output.data)

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
            self.assertTrue(
                '<td>Time must be of type &#34;HH:MM&#34;</td>'
                in output.data)

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
            self.assertTrue(
                '<li class="warnings">The start date of your meeting is '
                'later than the stop date.</li>' in output.data)
            self.assertTrue(
                '<title>Add meeting - Fedocal</title>' in output.data)

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
            self.assertTrue(
                '<li class="message">Meeting added</li>' in output.data)
            self.assertTrue(
                'href="/meeting/16/?from_date=' in output.data)

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
            self.assertTrue(
                '<title>test_calendar_disabled - Fedocal</title>'
                in output.data)
            self.assertTrue(
                '<li class="errors">This calendar is &#34;Disabled&#34;, '
                'you are not allowed to add meetings anymore.</li>'
                in output.data)

    @flask10_only
    def test_edit_meeting(self):
        """ Test the edit_meeting function. """
        self.__setup_db()
        user = FakeUser(['gitr2spec'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/edit/50/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                'class="errors">The meeting #50 could not be found</li>'
                in output.data)
            self.assertTrue('<title>Home - Fedocal</title>' in output.data)

            output = self.app.get('/meeting/edit/3/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not one of the manager of this '
                'meeting, or an admin, you are not allowed to edit it.</li>'
                in output.data)
            self.assertTrue(
                '<title>Meeting test-meeting23h59 - Fedocal</title>'
                in output.data)

        user = FakeUser(['fi-apprentice'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/edit/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not one of the manager of this '
                'meeting, or an admin, you are not allowed to edit it.</li>'
                in output.data)
            self.assertTrue(
                '<title>Meeting Fedora-fr-test-meeting - Fedocal</title>'
                in output.data)

        user = FakeUser(['fi-apprentice'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/edit/1/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Edit meeting - Fedocal</title>' in output.data)
            self.assertTrue(
                'meeting_name">Meeting name <span class="error">*</span></l'
                in output.data)
            self.assertTrue(
                'for="meeting_date">Date <span class="error">*</span></label'
                in output.data)

            csrf_token = output.data.split(
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
            self.assertTrue(
                '<td>This field is required.</td>' in output.data)

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
            self.assertTrue(
                '<td>Not a valid choice</td>' in output.data)
            self.assertTrue(
                '<title>Edit meeting - Fedocal</title>' in output.data)

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
            self.assertTrue(
                '<li class="warnings">The start date of your meeting is '
                'later than the stop date.</li>' in output.data)
            self.assertTrue(
                '<title>Edit meeting - Fedocal</title>' in output.data)

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
            self.assertTrue(
                '<li class="message">Meeting updated</li>' in output.data)
            self.assertTrue(
                '<title>Meeting guess what? - Fedocal</title>' in output.data)

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
            self.assertTrue(
                '<title>test_calendar_disabled - Fedocal</title>'
                in output.data)
            self.assertTrue(
                '<li class="errors">This calendar is &#34;Disabled&#34;, '
                'you are not allowed to add meetings to it anymore.</li>'
                in output.data)

        user = FakeUser(['packager'], username='pingou')
        with user_set(fedocal.APP, user):
            # Recursive meeting
            output = self.app.get('/meeting/edit/12/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Edit meeting - Fedocal</title>' in output.data)
            self.assertTrue(
                '<h2>Edit meeting Another past test meeting</h2>'
                in output.data)
            self.assertTrue(
                'meeting_name">Meeting name <span class="error">*</span></l'
                in output.data)
            self.assertTrue(
                'for="meeting_date">Date <span class="error">*</span></label'
                in output.data)

    @flask10_only
    def test_delete_meeting(self):
        """ Test the delete_meeting function. """
        self.__setup_db()
        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/delete/50/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '"errors">No meeting with this identifier could be found.</'
                in output.data)
            self.assertTrue('<title>Home - Fedocal</title>' in output.data)

            output = self.app.get('/meeting/delete/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not one of the manager of this '
                'meeting, or an admin, you are not allowed to delete it.</l'
                in output.data)
            self.assertTrue(
                '<title>Meeting Fedora-fr-test-meeting - Fedocal</title>'
                in output.data)

        user = FakeUser(['fi-apprentice'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/delete/1/', follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not one of the manager of this '
                'meeting, or an admin, you are not allowed to delete it.</l'
                in output.data)
            self.assertTrue(
                '<title>Meeting Fedora-fr-test-meeting - Fedocal</title>'
                in output.data)

        user = FakeUser(['fi-apprentice'], username='pingou')
        with user_set(fedocal.APP, user):
            output = self.app.get('/meeting/delete/1/')
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>Delete meeting - Fedocal</title>' in output.data)
            self.assertTrue(
                '<h4> Meeting: Fedora-fr-test-meeting</h4>'
                in output.data)
            self.assertTrue(
                "positively sure that's what you want to do?"
                in output.data)
            self.assertTrue(
                'name="confirm_delete" type="checkbox" value="y"><label'
                in output.data)
            self.assertTrue(
                '<input id="confirm_button" type="submit" class="submit positi'
                in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            # Do not delete
            data = {
                #'confirm_delete': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/delete/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>test_calendar - Fedocal</title>' in output.data)

            # Delete
            data = {
                'confirm_delete': False,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/delete/1/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>test_calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                '<li class="message">Meeting deleted</li>' in output.data)

            # Delete all
            data = {
                'confirm_delete': True,
                'confirm_futher_delete': True,
                'csrf_token': csrf_token,
            }

            output = self.app.post('/meeting/delete/8/', data=data,
                                   follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<title>test_calendar - Fedocal</title>' in output.data)
            self.assertTrue(
                '<li class="message">Meeting deleted</li>' in output.data)

    def test_update_tz(self):
        """ Test the update_tz function. """
        self.__setup_db()

        output = self.app.get('/updatetz/?tzone=Europe/Paris',
                              follow_redirects=True)
        self.assertTrue('<title>Home - Fedocal</title>' in output.data)
        self.assertTrue('<li class="warnings">Invalid referred url</li>'
                        in output.data)

        output = self.app.get('/updatetz/',
                              follow_redirects=True)
        self.assertTrue('<title>Home - Fedocal</title>' in output.data)
        self.assertTrue('<li class="warnings">Invalid referred url</li>'
                        in output.data)

    def test_search(self):
        """ Test the search function. """
        self.__setup_db()

        output = self.app.get('/search/?keyword=*meeting3*',
                              follow_redirects=True)
        self.assertTrue('<title>Search - Fedocal</title>' in output.data)
        self.assertTrue('<p>Result of your search for "*meeting3*"</p>'
                        in output.data)
        self.assertTrue('href="/meeting/4/">'in output.data)
        self.assertTrue('d> <p>Test meeting with past end_recursion.</p> </'
                        in output.data)

        output = self.app.get('/search/',
                              follow_redirects=True)
        self.assertTrue('<title>Home - Fedocal</title>')
        self.assertTrue('class="errors">No keyword provided for the search</'
                        in output.data)

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
        self.assertTrue('<title>Home - Fedocal</title>' in output.data)
        self.assertTrue('<li class="errors">No calendar specified</li>'
                        in output.data)

        output = self.app.get('/goto/?calendar=test_calendar',
                              follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get('/goto/?calendar=test_calendar&month=3',
                              follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get('/goto/?calendar=test_calendar&month=3&day=1',
                              follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get(
            '/goto/?calendar=test_calendar&year=2010&month=3&day=1',
            follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get(
            '/goto/?calendar=test_calendar&year=2010&month=3&day=a',
            follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<li class="errors">Invalid date specified</li>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get(
            '/goto/?calendar=test_calendar&year=2010&month=a',
            follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<li class="errors">Invalid date specified</li>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get('/goto/?calendar=test_calendar&year=a',
                              follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<li class="errors">Invalid date specified</li>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get('/goto/?calendar=test_calendar&year=1870',
                              follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('="warnings">Dates before 1900 are not allowed</li'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get('/goto/?calendar=test_calendar&type=list',
                              follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

        output = self.app.get('/goto/?calendar=test_calendar&type=foobar',
                              follow_redirects=True)
        self.assertTrue('<title>test_calendar - Fedocal</title>'
                        in output.data)
        self.assertTrue('<p>This is a test calendar</p>'
                        in output.data)

    @flask10_only
    def test_upload_calendar(self):
        """ Test the upload_calendar function. """
        self.__setup_db()

        user = FakeUser(['gitr2spec'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/upload/1/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">No calendar named 1 could not be found</li'
                in output.data)

            output = self.app.get('/calendar/upload/test_calendar/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue(
                '<li class="errors">You are not an admin for this calendar, '
                'you are not allowed to upload a iCalendar file to it.</l'
                in output.data)
            self.assertTrue(
                '<title>Home - Fedocal</title>'
                in output.data)

        user = FakeUser(['packager'], username='kevin')
        with user_set(fedocal.APP, user):
            output = self.app.get('/calendar/upload/test_calendar/',
                                  follow_redirects=True)
            self.assertEqual(output.status_code, 200)
            self.assertTrue('<title>Upload calendar - Fedocal</title>'
                            in output.data)
            self.assertTrue('<h2>Upload calendar</h2>' in output.data)

            csrf_token = output.data.split(
                'name="csrf_token" type="hidden" value="')[1].split('">')[0]

            if 'JENKINS' not in os.environ:
                with open(ICS_FILE) as stream:
                    data = {
                        'ics_file': stream,
                        'csrf_token': csrf_token,
                    }
                    output = self.app.post('/calendar/upload/test_calendar/',
                                           follow_redirects=True, data=data)
                    self.assertEqual(output.status_code, 200)
                    self.assertTrue('<title>test_calendar - Fedocal</title>'
                                    in output.data)
                    self.assertTrue('<p>This is a test calendar</p>'
                                    in output.data)
                    self.assertTrue('li class="message">Calendar uploaded</li>'
                                    in output.data)

            with open(ICS_FILE_NOTOK) as stream:
                data = {
                    'ics_file': stream,
                    'csrf_token': csrf_token,
                }
                output = self.app.post('/calendar/upload/test_calendar/',
                                       follow_redirects=True, data=data)
                self.assertEqual(output.status_code, 200)
                self.assertTrue('<title>Upload calendar - Fedocal</title>'
                                in output.data)
                self.assertTrue('<li class="error">The submitted candidate '
                                'has the file extension &#34;&#34; which is'
                                ' not an allowed format</li>'
                                in output.data)


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Flasktests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
