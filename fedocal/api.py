# -*- coding: utf-8 -*-

"""
 (c) 2012-2014 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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
from fedocal.doc_utils import load_doc

from fedocal import APP, SESSION, LOG
from fedocal.fedocallib.model import Calendar


def check_callback(response):
    """ Check the callback argument provided with the request to allow
    JQuery ajax calls.
    """
    callback = flask.request.args.get('callback', None)
    if callback:
        response = flask.Response(
            response="%s(%s);" % (callback, response.response),
            status=response.status_code,
            mimetype='application/javascript',
        )
    return response


# API
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
    api_html = load_doc(api)
    meetings_api_html = load_doc(api_meetings)
    calendars_api_html = load_doc(api_calendars)
    return flask.render_template(
        'api.html',
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
                "calendar_description": "test",
                "calendar_editor_group": "packager2",
                "calendar_admin_group": "packager",
                "calendar_contact": "test",
                "calendar_name": "test"
            },
            {
                "calendar_description": "asd",
                "calendar_editor_group": "",
                "calendar_admin_group": "",
                "calendar_contact": "asd",
                "calendar_name": "Another test"
            }
        ]
    }
    """
    @flask.after_this_request
    def callback(response):
        """ Handle case the query was an JQuery ajax call. """
        return check_callback(response)

    calendars = fedocallib.get_calendars(SESSION)

    output = {"calendars": [calendar.to_json() for calendar in calendars]}

    return flask.Response(
        response=json.dumps(output),
        status=200,
        mimetype='application/json'
    )


@APP.route('/api/locations/', methods=['GET', 'POST'])
def api_locations():
    """
Retrieve locations
==================

The ``/api/locations/`` endpoint returns the locations where meetings are
happening.

Response format
---------------

Sample response:

.. code-block:: javascript

    {
        "locations": [

        ]
    }
    """
    @flask.after_this_request
    def callback(response):
        """ Handle case the query was an JQuery ajax call. """
        return check_callback(response)

    list_locations = fedocallib.get_locations(SESSION)

    output = {"locations": list_locations}

    return flask.Response(
        response=json.dumps(output),
        status=200,
        mimetype='application/json'
    )


@APP.route('/api/locations/search/', methods=['GET'])
def api_locations_search():
    """
Retrieve locations
==================

The ``/api/locations/search/`` endpoint can be used to dynamically search
for specified locations.

:arg keyword: Specified using GET parameters this keyword is used to filter
    the list of locations having it in their name.

Response format
---------------

Sample response:

.. code-block:: javascript

    {
        "locations": [
            "EMEA",
            "#fedora-meeting@irc.freenode.net"
        ]
    }
    """
    @flask.after_this_request
    def callback(response):
        """ Handle case the query was an JQuery ajax call. """
        return check_callback(response)

    keyword = flask.request.args.get('keyword', None)

    if not keyword:
        output = {"error": "no keyword provided"}
        return flask.Response(
            response=json.dumps(output),
            status=400,
            mimetype='application/json'
        )

    if '*' not in keyword:
        keyword = '*%s*' % keyword

    list_locations = fedocallib.search_locations(SESSION, keyword)

    # filter out all locations containing '#'
    # https://fedorahosted.org/fedocal/ticket/118
    list_locations = [_loc for _loc in list_locations if _loc.count('#') == 0]

    output = {"locations": list_locations}

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
                "meeting_manager": [ "pingou2" ],
                "meeting_date": "2013-05-27",
                "meeting_name": "test1.5",
                "meeting_location": "None",
                "meeting_timezone": "UTC"
            },
            {
                "meeting_time_start": "06:00:00",
                "meeting_information": "",
                "meeting_time_stop": "07:00:00",
                "calendar_name": "test",
                "meeting_date_end": "2013-05-28",
                "meeting_manager": [ "pingou" ],
                "meeting_date": "2013-05-28",
                "meeting_name": "test3",
                "meeting_location": null,
                "meeting_timezone": "UTC"
            }
        ],
        "arguments": {
            "start": "2013-05-04",
            "calendar": "test",
            "end": "2013-11-30",
            "region": null
        }
    }

The ``meeting_time_start``, ``meeting_time_end``, ``meeting_date`` and
``meeting_date_end`` contain time in "UTC". The ``meeting_timezone`` indicates
the timezone the meeting is registered with. If the ``meeting_timezone`` is not
"UTC", the meeting time will change according to DST rules of the specified
timezone.

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
        """ Handle case the query was an JQuery ajax call. """
        return check_callback(response)

    startd = flask.request.args.get('start', None)
    if startd is None:
        startd = datetime.date.today() - datetime.timedelta(days=30)
    else:
        try:
            startd = parser.parse(startd).date()
        except (ValueError, TypeError):
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
        except (ValueError, TypeError):
            output = {"meetings": [],
                      "error": "Invalid end date format: %s" % endd}
            return flask.Response(
                response=json.dumps(output),
                status=400,
                mimetype='application/json')

    calendar_name = flask.request.args.get('calendar', None)
    location = flask.request.args.get('location', None)
    region = flask.request.args.get('region', None)
    location = location or region

    if calendar_name:
        calendarobj = Calendar.by_id(SESSION, calendar_name)

        if not calendarobj:
            output = {
                "meetings": [],
                "error": "Invalid calendar provided: %s" % calendar_name}
            return flask.Response(
                response=json.dumps(output),
                status=400,
                mimetype='application/json')

    status = 200
    meetings = []
    try:
        if calendar_name:
            if location:
                # print "calendar and region"
                meetings = fedocallib.get_meetings_by_date_and_location(
                    SESSION, calendar_name, startd, endd, location)
            else:
                # print "calendar and no region"
                meetings = fedocallib.get_by_date(
                    SESSION, calendarobj, startd, endd)
        else:
            meetings = []
            if location:
                # print "no calendar and region"
                meetings.extend(
                    fedocallib.get_by_date_at_location(
                        SESSION, location, startd, endd)
                )
            else:
                # print "no calendar and no region"
                for calendar in fedocallib.get_calendars(SESSION):
                    meetings.extend(fedocallib.get_by_date(
                        SESSION, calendar, startd, endd))
    except SQLAlchemyError as err:  # pragma: no cover
        status = 500
        LOG.debug('Error in api_meetings')
        LOG.exception(err)

    output = {}
    output['arguments'] = {
        'start': startd.strftime('%Y-%m-%d'),
        'end': endd.strftime('%Y-%m-%d'),
        'calendar': calendar_name,
        'location': location,
    }

    meetings_json = []
    for meeting in meetings:
        meetings_json.append(meeting.to_json())
    output['meetings'] = meetings_json

    return flask.Response(
        response=json.dumps(output),
        status=status,
        mimetype='application/json'
    )


@APP.route('/api/<username>/shield/<calendar_name>/')
@APP.route('/api/<username>/shield/<calendar_name>')
def api_user_shield(username, calendar_name):
    """
User shield
===========

Provides a small image (a shield) displaying the status of the specified
user on the specified calendar if the user is currently managing a meeting.

Filter arguments
----------------

``connector``
  Changes the 'connector' text used in the image.

  Default: 'in'

``status``
  Changes the 'status' text used in the image.

  Default: the name of the calendar checked

``always``
  Booleans to specify whether to return an image if no meeting is found for
  the specified user on the specified calendar.

  Default: True
  Can be:  False, 0, f

If the user is not managing a meeting, instead of returning the image the
endpoint raises a 404.

    """
    connector = flask.request.args.get('connector', 'in')
    status = flask.request.args.get('status', calendar_name)
    always = flask.request.args.get('always', True)

    if str(always).lower() in ['0', 'false', 'f']:
        always = False
    else:
        always = True

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if not calendarobj:
        flask.abort(400, 'Invalid calendar provided')

    start_date = datetime.datetime.utcnow().date()
    end_date = start_date + datetime.timedelta(days=1)

    meetings = fedocallib.get_by_date(
        SESSION, calendarobj, start_date, end_date, tzone='UTC')

    green, red = 'brightgreen', 'red'

    template = 'https://img.shields.io/badge/%s-%s_%s-%s.png'

    output = None
    for meeting in meetings:
        usernames = [user.username for user in meeting.meeting_manager_user]
        if username in usernames:
            output = template % (username, connector, status, green)
            break

    if output:
        return flask.redirect(output)
    elif always:
        output = template % (username, "not " + connector, status, red)
        return flask.redirect(output)
    else:
        flask.abort(404)
