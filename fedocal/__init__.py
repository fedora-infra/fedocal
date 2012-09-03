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


def is_admin():
    """ Return wether the user is admin for this application or not. """
    if not flask.g.fas_user:
        return False
    else:
        if CONFIG.get('fedocal', 'admin_group') in flask.g.fas_user.groups:
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


@APP.route('/mine/')
def my_meetings():
    session = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))
    meetings = fedocallib.get_future_meeting_of_user(session,
        flask.g.fas_user.username)
    past_meetings = fedocallib.get_past_meeting_of_user(session,
        flask.g.fas_user.username)
    calendars = Calendar.get_all(session)
    return flask.render_template('my_meeting.html', calendars=calendars,
        title='My meeting',
        meetings=meetings, pas_meetings=past_meetings)


@APP.route('/login', methods=('GET', 'POST'))
def auth_login():
    if flask.g.fas_user:
        return flask.redirect('index')
    form = forms.LoginForm()
    if form.validate_on_submit():
        if fas.login(form.username.data, form.password.data):
            flask.flash('Welcome, %s' % flask.g.fas_user.username)
            return flask.redirect('index')
        else:
            flask.flash('Incorrect username or password')
    return flask.redirect('index')


@APP.route('/logout')
def auth_logout():
    if not flask.g.fas_user:
        return flask.redirect('index')
    fas.logout()
    flask.flash('You have been logged out')
    return flask.redirect('index')


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
        flask.flash('Calendar added')
        return flask.redirect('index')
    else:
        flask.flash('Incorrect information entered to add a new agenda')
    return flask.render_template('add_calendar.html', form=form)


@APP.route('/<calendar>/add', methods=('GET', 'POST'))
def add_meeting(calendar):
    #if not flask.g.fas_user or not is_admin():
        #return safe_redirect_back()
    form = forms.AddMeetingForm()
    if form.validate_on_submit():
        session = fedocallib.create_session(
            CONFIG.get('fedocal', 'db_url'))
        if fedocallib.is_date_in_future(form.meeting_date.data,
            form.meeting_time_start.data):
                flask.flash('The date you entered is in the past')
                return flask.redirect('add_meeting')
        else:
            meeting = Meeting(
                form.meeting_name.data,
                flask.g.fas_user.username,
                form.meeting_date.data,
                '%s:00:00' % form.meeting_time_start.data,
                '%s:00:00' % form.meeting_time_stop.data,
                calendar,
                None)
            try:
                meeting.save(session)
                session.commit()
            except Exception, err:
                print err
                flask.flash('Could not add this meeting to this calendar')
                return flask.redirect('index')
            flask.flash('Meeting added')
            return flask.redirect(flask.url_for('calendar',
                calendar=calendar))
    return flask.render_template('add_meeting.html', calendar=calendar,
        form=form)


if __name__ == '__main__':
    APP.debug = True
    APP.run()
