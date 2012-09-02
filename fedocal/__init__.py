#!/usr/bin/python
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

import ConfigParser
import os

import flask

import fedocallib
from fedocallib.model import Calendar, Meeting, Reminder

CONFIG = ConfigParser.ConfigParser()
if os.path.exists('/etc/fedocal.cfg'):
    CONFIG.readfp(open('/etc/fedocal.cfg'))
else:
    CONFIG.readfp(open(os.path.join(os.path.dirname(
        os.path.abspath(__file__)),
        'fedocal.cfg')))

# Create the application.
APP = flask.Flask(__name__)
APP.secret_key = CONFIG.get('fedocal', 'secret_key')


@APP.route('/')
def index():
    session = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))
    calendars = Calendar.get_all(session)
    return calendar(calendars[0].calendar_name)


@APP.route('/<calendar>')
def calendar(calendar):
    session = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))
    calendar = Calendar.by_id(session, calendar)
    calendars = Calendar.get_all(session)
    week_start = fedocallib.get_start_week()
    week_stop = fedocallib.get_stop_week()
    weekdays = fedocallib.get_week_days()
    meetings = fedocallib.get_meetings(session, calendar)
    next_week = fedocallib.get_next_week(week_start.year,
        week_start.month, week_start.day)
    prev_week = fedocallib.get_previous_week(week_start.year,
        week_start.month, week_start.day)
    admin = fedocallib.is_admin()
    return flask.render_template('agenda.html',
        calendar=calendar,
        calendars=calendars,
        weekdays=weekdays,
        meetings=meetings,
        next_week=next_week,
        prev_week=prev_week,
        admin=admin)

@APP.route('/<calendar>/<int:year>/<int:month>/<int:day>')
def calendar_fullday(calendar, year, month, day):
    session = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))
    calendar = Calendar.by_id(session, calendar)
    calendars = Calendar.get_all(session)
    week_start = fedocallib.get_start_week(year, month, day)
    week_stop = fedocallib.get_stop_week(year, month, day)
    weekdays = fedocallib.get_week_days(year, month, day)
    meetings = fedocallib.get_meetings(session, calendar, year, month, day)
    next_week = fedocallib.get_next_week(week_start.year,
        week_start.month, week_start.day)
    prev_week = fedocallib.get_previous_week(week_start.year,
        week_start.month, week_start.day)
    admin = fedocallib.is_admin()
    return flask.render_template('agenda.html',
        calendar=calendar,
        calendars=calendars,
        weekdays=weekdays,
        meetings=meetings,
        next_week=next_week,
        prev_week=prev_week,
        admin=admin)


if __name__ == '__main__':
    APP.debug = True
    APP.run()
