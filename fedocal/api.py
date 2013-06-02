#-*- coding: UTF-8 -*-

"""
 (c) 2012 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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

from dateutil import parser
from sqlalchemy.exc import SQLAlchemyError

import fedocal.fedocallib as fedocallib
import fedocal.forms as forms

from fedocal import APP, SESSION
import fedocal


### API
@APP.route('/api/')
def api():
    """ Display the api information page. """
    auth_form = forms.LoginForm()
    admin = fedocal.is_admin()
    return flask.render_template('api.html', auth_form=auth_form,
                                 admin=admin)


@APP.route('/api/calendars/', methods=['GET', 'POST'])
def api_calendars():
    """ Returns all the calendars present in fedocal.

    """
    calendars = fedocallib.get_calendars(SESSION)

    output = '{ "retrieval": "ok", "calendars": [\n'
    for calendar in calendars:
        output += str(calendar.to_json()) + '\n'
    output += ']}'
    return flask.Response(output)


@APP.route('/api/meetings/', methods=['GET', 'POST'])
def api_meetings():
    """ Returns all the meetings for the specified calendar for the
    time frame between today - 30 days to today + 180 days.

    :arg calendar_name: the name of the calendar to retrieve information
        from.
    """
    startd = flask.request.args.get('start', None)
    if startd is None:
        startd = datetime.date.today() - datetime.timedelta(days=30)
    else:
        try:
            startd = parser.parse(startd).date()
        except ValueError:
            output = '{ "retrieval": "notok", "meeting": [], '\
                     '"error": "Invalid start date format: %s" }' % startd
            return flask.Response(output)

    endd = flask.request.args.get( 'end', None)
    if endd is None:
        endd = datetime.date.today() + datetime.timedelta(days=180)
    else:
        try:
            endd = parser.parse(endd).date()
        except ValueError:
            output = '{ "retrieval": "notok", "meeting": [], '\
                     '"error": "Invalid end date format: %s" }' % endd
            return flask.Response(output)

    calendar_name = flask.request.args.get('calendar', None)
    region = flask.request.args.get('region', None)

    status = 200
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
        meetings = None
        status = 500  #TODO: see if this code is the correct one

    if not meetings:
        output = '{ "retrieval": "notok", "meeting": []}'
    else:
        output = '{ "retrieval": "ok", "meeting": [\n'
        cnt = 0
        for meeting in meetings:
            output = output + meeting.to_json()
            cnt = cnt + 1
            if cnt != len(meetings):
                output = output + ','
        output = output + '\n]}'
    return flask.Response(output)
