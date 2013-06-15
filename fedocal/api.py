#-*- coding: UTF-8 -*-

"""
 (c) 2012-2013 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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
"""


import datetime
import flask
import json

from dateutil import parser
from sqlalchemy.exc import SQLAlchemyError

import fedocal.fedocallib as fedocallib
import fedocal.forms as forms
from fedocal.doc_utils import load_doc

from fedocal import APP, SESSION
import fedocal


def check_callback(response):
    callback = flask.request.args.get('callback', None)
    if callback:
        response = flask.Response(
            response="%s(%s);" % (callback, response.response),
            status=response.status_code,
            mimetype='application/javascript',
        )
    return response


### API
@APP.route('/api/')
def api():
    """
API documentation
=================

Fedocal provides a small read-only API.


The API supports GET and POST requests with the same arguments.

A trailing slash is optional on all API endpoints. There is no
difference between using one and not using one.

Responses are always served as ``application/json`` (unless ``JSONP``
is explicitly requested, in which case fedocal returns the
appropriate ``application/javascript``).

    """
    auth_form = forms.LoginForm()
    admin = fedocal.is_admin()
    api_html = load_doc(api)
    meetings_api_html = load_doc(api_meetings)
    calendars_api_html = load_doc(api_calendars)
    return flask.render_template(
        'api.html',
        auth_form=auth_form,
        admin=admin,
        api_html=api_html,
        calendars_api_html=calendars_api_html,
        meetings_api_html=meetings_api_html)


@APP.route('/api/calendars/', methods=['GET', 'POST'])
def api_calendars():
    """
Retrieve calendars
==================

The ``/api/calendars/`` endpoint returns the meetings meeting the
provided criteria.

Response format
---------------

Sample response:

.. code-block:: javascript

    {
        "calendars": [
            {
                "calendar_multiple_meetings": false,
                "calendar_description": "test",
                "calendar_manager_group": "packager2",
                "calendar_admin_group": "packager",
                "calendar_contact": "test",
                "calendar_regional_meetings": false,
                "calendar_name": "test"
            },
            {
                "calendar_multiple_meetings": false,
                "calendar_description": "asd",
                "calendar_manager_group": "",
                "calendar_admin_group": "",
                "calendar_contact": "asd",
                "calendar_regional_meetings": false,
                "calendar_name": "Another test"
            }
        ]
    }
    """
    @flask.after_this_request
    def callback(response):
        return check_callback(response)

    calendars = fedocallib.get_calendars(SESSION)

    output = {"calendars": [calendar.to_json() for calendar in calendars]}

    return flask.Response(
        response=json.dumps(output),
        status=200,
        mimetype='application/json'
    )


@APP.route('/api/meetings/', methods=['GET', 'POST'])
@APP.route('/api/meetings', methods=['GET', 'POST'])
def api_meetings():
    """
Retrieve meetings
=================

The ``/api/meetings/`` endpoint returns the meetings meeting the
provided criteria.

Response format
----------------

Sample response:

.. code-block:: javascript

    {
        "meetings": [
            {
                "meeting_time_start": "23:00:00",
                "meeting_information": "",
                "meeting_time_stop": "23:00:00",
                "calendar_name": "test",
                "meeting_date_end": "2013-05-27",
                "meeting_manager": "pingou2,",
                "meeting_date": "2013-05-27",
                "meeting_name": "test1.5",
                "meeting_region": "None"
            },
            {
                "meeting_time_start": "06:00:00",
                "meeting_information": "",
                "meeting_time_stop": "07:00:00",
                "calendar_name": "test",
                "meeting_date_end": "2013-05-28",
                "meeting_manager": "pingou,",
                "meeting_date": "2013-05-28",
                "meeting_name": "test3",
                "meeting_region": null
            }
        ],
        "arguments": {
            "start": "2013-05-04",
            "calendar": "test",
            "end": "2013-11-30",
            "region": null
        }
    }


The ``arguments`` item in the root dictionary contains all possible
arguments, and displays the value used (the default if the argument
was not provided).

Time arguments
--------------

Below is a table describing what timeframe messages are received from
depending on what combination of time options you provide.

========= ======= =================
``start`` ``end`` Message timeframe
========= ======= =================
no        no      the last 30 days and the coming 180 days
**yes**   no      from ``start`` until the coming 180 days
no        **yes** the last 30 days until ``end``
**yes**   **yes** between ``start`` and ``end``
========= ======= =================

``start``
  Return results starting at date ``start`` (prefered format is
  "+%Y-%m-%d" see ``date "+%Y-%m-%d"``).

  Default: 30 days ago ``date "+%Y-%m-%d" -d "30 days ago"``

``end``
  Return results ending at date ``end`` (prefered format is
  "+%Y-%m-%d" see ``date "+%Y-%m-%d"``).

  Default: coming 180 days ``date "+%Y-%m-%d" -d "180 days"``

Filter arguments
----------------

``calendar``
  Restrict the meetings to a specific calendar.

  Default: all calendars

``region``
  Restrict the meeting to a specific region.

  If the calendar does not have support for regions enabled, no
  meetings will be found matching this criteria and no meetings will
  be returned.

  Default: all regions

    """
    @flask.after_this_request
    def callback(response):
        return check_callback(response)

    startd = flask.request.args.get('start', None)
    if startd is None:
        startd = datetime.date.today() - datetime.timedelta(days=30)
    else:
        try:
            startd = parser.parse(startd).date()
        except ValueError:
            output = {"meetings": [],
                      "error": "Invalid start date format: %s" % startd}
            return flask.Response(
                response=json.dumps(output),
                status=400,
                mimetype='application/json')

    endd = flask.request.args.get('end', None)
    if endd is None:
        endd = datetime.date.today() + datetime.timedelta(days=180)
    else:
        try:
            endd = parser.parse(endd).date()
        except ValueError:
            output = {"meetings": [],
                      "error": "Invalid end date format: %s" % endd}
            return flask.Response(
                response=json.dumps(output),
                status=400,
                mimetype='application/json')

    calendar_name = flask.request.args.get('calendar', None)
    region = flask.request.args.get('region', None)

    status = 200
    meetings = []
    try:
        if calendar_name:
            if region:
                #print "calendar and region"
                meetings = fedocallib.get_meetings_by_date_and_region(
                    SESSION, calendar_name, startd, endd, region)
            else:
                #print "calendar and no region"
                meetings = fedocallib.get_meetings_by_date(
                    SESSION, calendar_name, startd, endd)
        else:
            meetings = []
            for calendar in fedocallib.get_calendars(SESSION):
                if region:
                    #print "no calendar and region"
                    meetings.extend(fedocallib.get_meetings_by_date_and_region(
                        SESSION, calendar.calendar_name, startd, endd,
                        region))
                else:
                    #print "no calendar and no region"
                    meetings.extend(fedocallib.get_meetings_by_date(
                        SESSION, calendar.calendar_name, startd, endd))
    except SQLAlchemyError:  # pragma: no cover
        status = 500

    output = {}
    output['arguments'] = {
        'start': startd.strftime('%Y-%m-%d'),
        'end': endd.strftime('%Y-%m-%d'),
        'calendar': calendar_name,
        'region': region,
    }
    cnt = 0
    meetings_json = []
    for meeting in meetings:
        meetings_json.append(meeting.to_json())
    output['meetings'] = meetings_json

    return flask.Response(
        response=json.dumps(output),
        status=status,
        mimetype='application/json'
    )
