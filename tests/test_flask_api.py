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
from __future__ import unicode_literals, absolute_import, print_function

import json
import unittest
import sys
import os

from datetime import date
from datetime import timedelta

import six

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedocal
import fedocal.api
import fedocal.fedocallib as fedocallib
from tests import Modeltests, TODAY


# pylint: disable=E1103
class FlaskApitests(Modeltests):
    """ Flask application API tests. """

    maxDiff = None

    def __setup_db(self):
        """ Add a calendar and some meetings so that we can play with
        something. """
        from .test_meeting import Meetingtests
        meeting = Meetingtests('test_init_meeting')
        meeting.session = self.session
        meeting.test_init_meeting()

    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        super(FlaskApitests, self).setUp()

        fedocal.APP.config['TESTING'] = True
        fedocal.SESSION = self.session
        fedocal.api.SESSION = self.session
        self.app = fedocal.APP.test_client()

    def test_api(self):
        """ Test the index function. """
        output = self.app.get('/api')
        self.assertTrue(output.status_code in [301, 308])

        output = self.app.get('/api/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '<title>API - Fedocal</title>', output_text)
        self.assertIn(
            '<h1 class="title">API documentation</h1>', output_text)

    def test_api_date_default(self):
        """ Test the api_date_default function. """
        output = self.app.get('/api/meetings/?calendar=test_calendar')
        self.assertEqual(output.status_code, 400)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "meetings": [],
                "error": "Invalid calendar provided: test_calendar"
            })

        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=180)

        self.__setup_db()

        output = self.app.get('/api/meetings/?calendar=test_calendar')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            ' "meeting_manager": ["pingou", "shaiton"]', output_text)
        self.assertIn('"meeting_name": "test-meeting2"', output_text)
        self.assertEqual(output_text.count('meeting_name'), 49)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data['arguments']['start'],
            start_date.strftime('%Y-%m-%d'))

        output = self.app.get('/api/meetings/?calendar=test_calendar4')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output.status_code, 200)
        self.assertEqual(output_text.count('meeting_name'), 3)

    def test_api_date(self):
        """ Test the api_date function. """
        end_date = TODAY + timedelta(days=10)
        output = self.app.get(
            '/api/meetings/?calendar=foobar&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 400)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "meetings": [],
                "error": "Invalid calendar provided: foobar"
            })

        self.__setup_db()

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar&start=%s&end=%s' % (
                TODAY - timedelta(days=50), end_date - timedelta(days=45)
            )
        )
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "meetings": [],
                "arguments": {
                    "start": "%s" % (TODAY - timedelta(days=50)).strftime('%Y-%m-%d'),
                    "calendar": "test_calendar",
                    "end": "%s" % (end_date - timedelta(days=45)).strftime('%Y-%m-%d'),
                    "location": None
                }
            }
        )

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '"meeting_manager": ["pingou", "shaiton"]', output_text)
        self.assertIn(
            '"meeting_name": "Another test meeting2"', output_text)
        self.assertEqual(output_text.count('meeting_name'), 8)

        end_date = TODAY + timedelta(days=2)
        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('meeting_name'), 2)

        end_date = TODAY + timedelta(days=2)
        output = self.app.get(
            '/api/meetings/?start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('meeting_name'), 6)

    def test_api_date_error(self):
        """ Test the api_date function with wrong input. """
        self.__setup_db()

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar&start=%s&end=2012-09-aw'
            % (TODAY))
        self.assertEqual(output.status_code, 400)
        output_text = output.get_data(as_text=True)
        self.assertIn('"error": "Invalid end date format: ', output_text)

    def test_api_place_default(self):
        """ Test the api_place_default function. """
        start_date = date.today() - timedelta(days=30)
        end_date = date.today() + timedelta(days=180)

        output = self.app.get(
            '/api/meetings/?location=EMEA')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "meetings": [],
                "arguments": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "calendar": None,
                    "end": end_date.strftime('%Y-%m-%d'),
                    "location": "EMEA"
                }
            }
        )

        self.__setup_db()

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=APAC')
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "meetings": [],
                "arguments": {
                    "start": start_date.strftime('%Y-%m-%d'),
                    "calendar": "test_calendar4",
                    "end": end_date.strftime('%Y-%m-%d'),
                    "location": "APAC"
                }
            }
        )

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=NA')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('meeting_name'), 1)

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=EMEA')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('meeting_name'), 2)

    def test_api_place(self):
        """ Test the api_place function. """
        end_date = TODAY + timedelta(days=25)
        output = self.app.get(
            '/api/meetings/?location=APAC&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "meetings": [],
                "arguments": {
                    "start": TODAY.strftime('%Y-%m-%d'),
                    "calendar": None,
                    "end": end_date.strftime('%Y-%m-%d'),
                    "location": "APAC"
                }
            }
        )

        self.__setup_db()

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=APAC'
            '&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "meetings": [],
                "arguments": {
                    "start": TODAY.strftime('%Y-%m-%d'),
                    "calendar": "test_calendar4",
                    "end": end_date.strftime('%Y-%m-%d'),
                    "location": "APAC"
                }
            }
        )

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=NA'
            '&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('meeting_name'), 1)

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=EMEA'
            '&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('meeting_name'), 2)

        output = self.app.get(
            '/api/meetings/?location=EMEA&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('meeting_name'), 2)

        end_date = TODAY + timedelta(days=1)

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=NA'
            '&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "arguments": {
                    "start": TODAY.strftime('%Y-%m-%d'),
                    "calendar": "test_calendar4",
                    "end": end_date.strftime('%Y-%m-%d'),
                    "location": "NA"
                },
                "meetings": []
            }
        )

        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=EMEA'
            '&start=%s&end=%s' % (
                TODAY, end_date
            )
        )
        self.assertEqual(output.status_code, 200)
        data = json.loads(output.get_data(as_text=True))
        self.assertEqual(
            data,
            {
                "meetings": [],
                "arguments": {
                    "start": TODAY.strftime('%Y-%m-%d'),
                    "calendar": "test_calendar4",
                    "end": end_date.strftime('%Y-%m-%d'),
                    "location": "EMEA"
                }
            }
        )

    def test_api_place_error(self):
        """ Test the api_date function with wrong input. """
        self.__setup_db()

        end_date = TODAY + timedelta(days=1)
        output = self.app.get(
            '/api/meetings/?calendar=test_calendar4&location=EMEA'
            '&end=%s&start=2012-12-as' % (end_date)
        )
        self.assertEqual(output.status_code, 400)
        output_text = output.get_data(as_text=True)
        self.assertIn(
            '"error": "Invalid start date format: ', output_text)

    def test_api_calendars(self):
        """ Test the api_calendars function. """
        output = self.app.get('/api/calendars/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(
            output_text,
            '{"calendars": []}')

        self.__setup_db()

        output = self.app.get('/api/calendars/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('calendar_name'), 5)

        output = self.app.get('/api/calendars/?callback="abcd"')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text.count('calendar_name'), 5)
        if six.PY3:
            self.assertTrue(output_text.startswith('"abcd"([b\'{"calendars":'))
        else:
            self.assertTrue(output_text.startswith('"abcd"([\'{"calendars":'))

    def test_api_locations(self):
        """ Test the api_locations function. """
        output = self.app.get('/api/locations/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text, '{"locations": []}')

        self.__setup_db()

        output = self.app.get('/api/locations/')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text, '{"locations": ["EMEA", "NA"]}')

        output = self.app.get('/api/locations/?callback="abcd"')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        if six.PY3:
            self.assertEqual(
                output_text, '"abcd"([b\'{"locations": ["EMEA", "NA"]}\']);')
        else:
            self.assertEqual(
                output_text, '"abcd"([\'{"locations": ["EMEA", "NA"]}\']);')

    def test_api_search_locations(self):
        """ Test the api_search_locations function. """
        output = self.app.get('/api/locations/search/')
        self.assertEqual(output.status_code, 400)
        output_text = output.get_data(as_text=True)
        self.assertEqual(
            output_text,
            '{"error": "no keyword provided"}')

        self.__setup_db()

        output = self.app.get('/api/locations/search/?keyword=ME')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        self.assertEqual(output_text, '{"locations": ["EMEA"]}')

        output = self.app.get(
            '/api/locations/search/?keyword=ME&callback="abcd"')
        self.assertEqual(output.status_code, 200)
        output_text = output.get_data(as_text=True)
        if six.PY3:
            self.assertEqual(
                output_text, '"abcd"([b\'{"locations": ["EMEA"]}\']);')
        else:
            self.assertEqual(
                output_text, '"abcd"([\'{"locations": ["EMEA"]}\']);')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FlaskApitests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
