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

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..', '..'))

import fedocal
import fedocal.fedocallib as fedocallib
from fedocal.tests import Modeltests, DB_PATH, TODAY
from test_fedocallib import FakeUser


class FlaskApitests(Modeltests):
    """ Flask application API tests. """

    def __setup_db(self):
        """ Add a calendar and some meetings so that we can play with
        something. """
        from test_meeting import Meetingtests
        meeting = Meetingtests('test_init_meeting')
        meeting.session = self.session
        meeting.test_init_meeting()

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApitests, self).setUp()

        fedocal.APP.config['TESTING'] = True
        fedocal.CONFIG.set('fedocal', 'db_url',
            'sqlite:///%s' % DB_PATH)
        self.app = fedocal.APP.test_client()

    def test_api(self):
        """ Test the index function. """
        rv = self.app.get('/api')
        self.assertEqual(rv.status_code, 301)

        rv = self.app.get('/api/')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('<title> API   - Fedocal</title>' in rv.data)
        self.assertTrue('<h1>API documentation</h1>' in rv.data)
        self.assertTrue('<code>/api/date/calendar_name/</code>' \
            in rv.data)
        self.assertTrue('<code>/api/place/region/calendar_name/</code>' \
            in rv.data)

    def test_api_date_default(self):
        """ Test the api_date_default function. """
        rv = self.app.get('/api/date/foobar')
        self.assertEqual(rv.status_code, 301)

        rv = self.app.get('/api/date/foobar/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": []}')

        self.__setup_db()

        rv = self.app.get('/api/date/test_calendar/')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('"retrieval": "ok"' in rv.data)
        self.assertTrue(' "meeting_manager": "pingou, shaiton",' in \
            rv.data)
        self.assertTrue('"meeting_name": "test-meeting2"' in rv.data)
        self.assertEqual(rv.data.count('meeting_name'), 6)

        rv = self.app.get('/api/date/test_calendar4/')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('"retrieval": "ok"' in rv.data)
        self.assertEqual(rv.data.count('meeting_name'), 2)

    def test_api_date(self):
        """ Test the api_date function. """
        end_date = TODAY + timedelta(days=11)
        rv = self.app.get('/api/date/foobar/%s/%s' %(TODAY, end_date))
        self.assertEqual(rv.status_code, 301)

        rv = self.app.get('/api/date/foobar/%s/%s/' %(TODAY, end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": []}')

        self.__setup_db()

        rv = self.app.get('/api/date/test_calendar/%s/%s/' %(TODAY,
            end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('"retrieval": "ok"' in rv.data)
        self.assertTrue(' "meeting_manager": "pingou, shaiton",' in \
            rv.data)
        self.assertTrue('"meeting_name": "Another test meeting2",' in \
            rv.data)
        self.assertEqual(rv.data.count('meeting_name'), 4)

        end_date = TODAY + timedelta(days=2)
        rv = self.app.get('/api/date/test_calendar4/%s/%s/' %(TODAY,
            end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('"retrieval": "ok"' in rv.data)
        self.assertEqual(rv.data.count('meeting_name'), 2)

    def test_api_place_default(self):
        """ Test the api_place_default function. """
        rv = self.app.get('/api/place/EMEA/foobar')
        self.assertEqual(rv.status_code, 301)

        rv = self.app.get('/api/place/EMEA/foobar/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": []}')

        self.__setup_db()

        rv = self.app.get('/api/place/APAC/test_calendar4/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": []}')

        rv = self.app.get('/api/place/NA/test_calendar4/')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('"retrieval": "ok"' in rv.data)
        self.assertEqual(rv.data.count('meeting_name'), 1)

        rv = self.app.get('/api/place/EMEA/test_calendar4/')
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('"retrieval": "ok"' in rv.data)
        self.assertEqual(rv.data.count('meeting_name'), 1)

    def test_api_place(self):
        """ Test the api_place function. """
        end_date = TODAY + timedelta(days=2)
        rv = self.app.get('/api/place/EMEA/foobar/%s/%s' %(TODAY,
            end_date))
        self.assertEqual(rv.status_code, 301)

        rv = self.app.get('/api/place/EMEA/foobar/%s/%s/' %(TODAY,
            end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": []}')

        self.__setup_db()

        rv = self.app.get('/api/place/APAC/test_calendar4/%s/%s/' %(
            TODAY, end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": []}')

        rv = self.app.get('/api/place/NA/test_calendar4/%s/%s/' %(
            TODAY, end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('"retrieval": "ok"' in rv.data)
        self.assertEqual(rv.data.count('meeting_name'), 1)

        rv = self.app.get('/api/place/EMEA/test_calendar4/%s/%s/' %(
            TODAY, end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertTrue('"retrieval": "ok"' in rv.data)
        self.assertEqual(rv.data.count('meeting_name'), 1)

        end_date = TODAY + timedelta(days=1)

        rv = self.app.get('/api/place/NA/test_calendar4/%s/%s/' %(
            TODAY, end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": []}')

        rv = self.app.get('/api/place/EMEA/test_calendar4/%s/%s/' %(
            TODAY, end_date))
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": []}')

    def test_api_date_place_error(self):
        """ Test the api_date and api_place functions with wrongly
        formated input. """
        rv = self.app.get('/api/date/foobar/2000-01/2000-02/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": [], "error": '\
            '"Date format invalid"}')

        rv = self.app.get('/api/place/EMEA/foobar/2000-01/2000-02/')
        self.assertEqual(rv.status_code, 200)
        self.assertEqual(rv.data,
            '{ "retrieval": "notok", "meeting": [], "error": '\
            '"Date format invalid"}')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApitests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
