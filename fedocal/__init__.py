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
from urlparse import urljoin, urlparse

import flask
from flask.ext.fas import FAS

import forms
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
# set up FAS
fas = FAS(APP)
APP.secret_key = CONFIG.get('fedocal', 'secret_key')


def is_safe_url(target):
    ref_url = urlparse(flask.request.host_url)
    test_url = urlparse(urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
            ref_url.netloc == test_url.netloc


def safe_redirect_back(next=None, fallback=('index', {})):
    targets = []
    if next:
        targets.append(next)
    if 'next' in flask.request.args and \
       flask.request.args['next']:
        targets.append(flask.request.args['next'])
    targets.append(flask.url_for(fallback[0], **fallback[1]))
    for target in targets:
        if is_safe_url(target):
            return flask.redirect(target)


def is_admin():
    """ Return wether the user is admin for this application or not. """
    if not flask.g.fas_user:
        return False
    else:
        print flask.g.fas_user.groups
        if '' in flask.g.fas_user.groups:
            return True
    return False


@APP.route('/')
def index():
    session = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))
    calendars = Calendar.get_all(session)
    return calendar(calendars[0].calendar_name)


@APP.route('/<calendar>')
def calendar(calendar):
    return calendar_fullday(calendar, year=None, month=None, day=None)


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
    auth_form = forms.LoginForm()
    admin = is_admin()
    return flask.render_template('agenda.html',
        calendar=calendar,
        calendars=calendars,
        weekdays=weekdays,
        meetings=meetings,
        next_week=next_week,
        prev_week=prev_week,
        auth_form=auth_form,
        admin=admin)


@APP.route('/login', methods=('GET', 'POST'))
def auth_login():
    if flask.g.fas_user:
        return safe_redirect_back()
    form = forms.LoginForm()
    if form.validate_on_submit():
        if fas.login(form.username.data, form.password.data):
            flask.flash('Welcome, %s' % flask.g.fas_user.username)
            return safe_redirect_back()
        else:
            flask.flash('Incorrect username or password')
    return safe_redirect_back()


@APP.route('/logout')
def auth_logout():
    if not flask.g.fas_user:
        return safe_redirect_back()
    fas.logout()
    flask.flash('You have been logged out')
    return safe_redirect_back()


@APP.route('/calendar/add', methods=('GET', 'POST'))
def add_calendar():
    #if not flask.g.fas_user or not is_admin():
        #return safe_redirect_back()
    form = forms.AddCalendarForm()
    if form.validate_on_submit():
        session = fedocallib.create_session(
            CONFIG.get('fedocal', 'db_url'))
        calendar = Calendar(
            form.calendar_name.data,
            form.calendar_description.data,
            form.calendar_manager_groups.data)
        try:
            calendar.save(session)
            session.commit()
        except Exception, err:
            print err
            flask.flash('Could not add this calendar to the database')
        else:
            flask.flash('Incorrect information entered to add a new agenda')
    return flask.render_template('add_calendar.html', form=form)


if __name__ == '__main__':
    APP.debug = True
    APP.run()
