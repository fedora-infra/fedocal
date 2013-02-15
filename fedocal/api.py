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


@APP.route('/api/date/<calendar_name>/')
def api_date_default(calendar_name):
    """ Returns all the meetings for the specified calendar for the
    time frame between today - 30 days to today + 180 days.

    :arg calendar_name: the name of the calendar to retrieve information
        from.
    """
    startd = datetime.date.today() - datetime.timedelta(days=30)
    endd = datetime.date.today() + datetime.timedelta(days=180)
    meetings = fedocallib.get_meetings_by_date(SESSION, calendar_name,
        startd, endd)
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


@APP.route('/api/date/<calendar_name>/<start_date>/<end_date>/')
def api_date(calendar_name, start_date, end_date):
    """ Returns all the meetings for the specified calendar for the
    specified time frame.

    :arg calendar_name: the name of the calendar to retrieve information
        from.
    :arg start_date: the start date of the time frame for which one
        would like to retrieve the meetings.
    :arg end_date: the end date of the time frame for which one would
        like to retrieve the meetings.
    """
    start_date = start_date.split('-')
    end_date = end_date.split('-')
    if len(start_date) != 3 or len(end_date) != 3:
        output = '{ "retrieval": "notok", "meeting": [], "error": '\
            '"Date format invalid"}'
        return flask.Response(output)
    try:
        start_date = [int(item) for item in start_date]
        end_date = [int(item) for item in end_date]
        startd = datetime.date(start_date[0], start_date[1],
            start_date[2])
        endd = datetime.date(end_date[0], end_date[1], end_date[2])
    except ValueError, error:
        output = '{ "retrieval": "notok", "meeting": [], "error": '\
            '"Date format invalid: %s"}' % error
        return flask.Response(output)

    meetings = fedocallib.get_meetings_by_date(SESSION, calendar_name,
        startd, endd)
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


@APP.route('/api/place/<region>/<calendar_name>/')
def api_place_default(region, calendar_name):
    """ Return all the meetings from an agenda in a specified region.
    The meetings are in the time range from today - 30 days to
    today + 180 days.

    :arg region: the name of the region in which the meetings will
        occur.
    :arg calendar_name: the name of the calendar to retrieve information
        from.
    """
    startd = datetime.date.today() - datetime.timedelta(days=30)
    endd = datetime.date.today() + datetime.timedelta(days=180)
    meetings = fedocallib.get_meetings_by_date_and_region(SESSION,
        calendar_name, startd, endd, region)
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


@APP.route('/api/place/<region>/<calendar_name>/<start_date>/<end_date>/')
def api_place(region, calendar_name, start_date, end_date):
    """ Returns all the meetings occuring in a region from an agenda
    and for the specified time frame.

    :arg region: the name of the region in which the meetings will
        occur.
    :arg calendar_name: the name of the calendar to retrieve information
        from.
    :arg start_date: the start date of the time frame for which one
        would like to retrieve the meetings.
    :arg end_date: the end date of the time frame for which one would
        like to retrieve the meetings.
    """
    start_date = start_date.split('-')
    end_date = end_date.split('-')
    if len(start_date) != 3 or len(end_date) != 3:
        output = '{ "retrieval": "notok", "meeting": [], "error": '\
            '"Date format invalid"}'
        return flask.Response(output)
    try:
        start_date = [int(item) for item in start_date]
        end_date = [int(item) for item in end_date]
        startd = datetime.date(start_date[0], start_date[1],
            start_date[2])
        endd = datetime.date(end_date[0], end_date[1], end_date[2])
    except ValueError, error:
        output = '{ "retrieval": "notok", "meeting": [], "error": '\
            '"Date format invalid: %s"}' % error
        return flask.Response(output)

    meetings = fedocallib.get_meetings_by_date_and_region(SESSION,
        calendar_name, startd, endd, region)
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
