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
from flask.ext.fas import FAS, cla_plus_one_required

import forms
import fedocallib
from fedocallib.model import Calendar, Meeting, Reminder, Recursive

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
    month = fedocallib.MONTH[week_start.month - 1]
    return flask.render_template('agenda.html',
        calendar=calendar,
        calendars=calendars,
        month=month,
        weekdays=weekdays,
        meetings=meetings,
        next_week=next_week,
        prev_week=prev_week,
        auth_form=auth_form,
        admin=admin)


# CLA + 1
@APP.route('/mine/')
@cla_plus_one_required
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
        return flask.redirect(flask.url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        if fas.login(form.username.data, form.password.data):
            flask.flash('Welcome, %s' % flask.g.fas_user.username)
            return flask.redirect(flask.url_for('index'))
        else:
            flask.flash('Incorrect username or password')
    return flask.redirect(flask.url_for('index'))


@APP.route('/logout')
def auth_logout():
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    fas.logout()
    flask.flash('You have been logged out')
    return flask.redirect(flask.url_for('index'))


# CLA + 1 (and admin)
@APP.route('/calendar/add', methods=('GET', 'POST'))
@cla_plus_one_required
def add_calendar():
    """ Add a calendar to the database.
    This function is only accessible to admin of the webapp.
    """
    if not flask.g.fas_user or not is_admin():
        return flask.redirect(flask.url_for('index'))
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
        return flask.redirect(flask.url_for('index'))
    else:
        flask.flash('Incorrect information entered to add a new agenda')
    return flask.render_template('add_calendar.html', form=form)


# CLA + 1
@APP.route('/<calendar>/add', methods=('GET', 'POST'))
@cla_plus_one_required
def add_meeting(calendar):
    """ Add a meeting to the database.
    This function is only available to CLA+1 member or members of the
    group administrating of the said calendar.
    :arg calendar, name of the calendar in which to add the meeting.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    form = forms.AddMeetingForm()
    if form.validate_on_submit():
        session = fedocallib.create_session(
            CONFIG.get('fedocal', 'db_url'))
        calendar = Calendar.by_id(session, calendar)
        if not fedocallib.is_user_managing_in_calendar(session,
            calendar.calendar_name, flask.g.fas_user):
                flask.flash('You are not allowed to add a meeting to this calendar')
                return flask.redirect(flask.url_for('index'))
        if not fedocallib.is_date_in_future(form.meeting_date.data,
            form.meeting_time_start.data):
                flask.flash('The date you entered is in the past')
                return flask.redirect(flask.url_for('add_meeting',
                    calendar=calendar.calendar_name))
        elif int(form.meeting_time_start.data) > int(form.meeting_time_stop.data):
            flask.flash('The start time you have entered is later than the stop time.')
            return flask.redirect(flask.url_for('add_meeting',
                calendar=calendar.calendar_name))
        elif fedocallib.agenda_is_free(session,
                calendar,
                form.meeting_date.data,
                int(form.meeting_time_start.data),
                int(form.meeting_time_stop.data)):
            manager = '%s,' % flask.g.fas_user.username
            meeting = Meeting(
                form.meeting_name.data,
                manager,
                form.meeting_date.data,
                '%s:00:00' % form.meeting_time_start.data,
                '%s:00:00' % form.meeting_time_stop.data,
                calendar.calendar_name,
                None, None)
            meeting.save(session)
            try:
                session.flush()
            except Exception, err:
                print 'add_meeting:', err
                flask.flash('Could not add this meeting to this calendar')
                flask.render_template('add_meeting.html',
                    calendar=calendar.calendar_name,  form=form)
            if form.remind_when.data and form.remind_who.data:
                reminder = Reminder(form.remind_when.data,
                                    form.remind_who.data,
                                    None)
                reminder.save(session)
                try:
                    session.flush()
                    meeting.reminder = reminder
                    session.flush()
                except Exception, err:
                    print 'add_meeting:', err
                    flask.flash('Could not add this reminder to this meeting')
                    flask.render_template('add_meeting.html',
                        calendar=calendar.calendar_name,  form=form)
            if form.frequency.data and form.end_repeats.data:
                recursion = Recursive(
                    recursion_frequency = form.frequency.data,
                    recursion_ends = form.end_repeats.data
                    )
                recursion.save(session)
                try:
                    session.flush()
                    meeting.recursion = recursion
                    session.flush()
                except Exception, err:
                    print 'add_meeting:', err
                    flask.flash('Could not add this reminder to this meeting')
                    flask.render_template('add_meeting.html',
                        calendar=calendar.calendar_name,  form=form)
                fedocallib.save_recursive_meeting(session, meeting)
            try:
                session.commit()
            except Exception, err:
                flask.flash('Something went wrong while commiting to the DB.')
                flask.render_template('add_meeting.html',
                    calendar=calendar.calendar_name,  form=form)
            flask.flash('Meeting added')
            return flask.redirect(flask.url_for('calendar',
                calendar=calendar.calendar_name))
        else:
            flask.flash('The start time you have entered is already occupied.')
            return flask.render_template('add_meeting.html',
                calendar=calendar.calendar_name, form=form)
    return flask.render_template('add_meeting.html', calendar=calendar,
        form=form)


# CLA + 1
@APP.route('/meeting/edit/<int:meeting_id>', methods=('GET', 'POST'))
@cla_plus_one_required
def edit_meeting(meeting_id):
    """ Edit a specific meeting based on the meeting identifier.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    session = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))
    if not flask.g.fas_user.username in Meeting.get_managers(session, meeting_id):
        flask.flash('You are not one of the manager of this meeting, you are not allowed to edit it.')
        return flask.redirect(flask.url_for('index'))
    meeting = Meeting.by_id(session, meeting_id)
    if not fedocallib.is_date_in_future(meeting.meeting_date,
        meeting.meeting_time_start.hour) :
        flask.flash('This meeting has already occured, you may not change it anymore')
        return flask.redirect(flask.url_for('index'))
    # You are not allowed to remove yourself from the managers.
    meeting.meeting_manager = meeting.meeting_manager.replace(
        '%s,' % flask.g.fas_user.username, '')
    editform = forms.AddMeetingForm(meeting=meeting)
    if editform.validate_on_submit():
        try:
            meeting.meeting_name = editform.meeting_name.data
            meeting.meeting_manager = '%s,%s' % (flask.g.fas_user.username,
                editform.comanager.data)
            meeting.meeting_date = editform.meeting_date.data
            meeting.meeting_time_start = '%s:00:00' % (
                editform.meeting_time_start.data)
            meeting.meeting_time_stop = '%s:00:00' % (
                editform.meeting_time_stop.data)
            meeting.save(session)
            session.commit()
        except Exception, err:
            print 'edit_meeting:',  err
            flask.flash('Could not update this meeting.')
        flask.flash('Meeting updated')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('edit_meeting.html', meeting=meeting,
        form=editform)


@APP.route('/meeting/<int:meeting_id>', methods=('GET', 'POST'))
def view_meeting(meeting_id):
    """ View a specific meeting given its identifier.
    """
    session = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))
    meeting = Meeting.by_id(session, meeting_id)
    if not meeting:
        flask.flash('No meeting could be found for this identifier')
        return flask.redirect(flask.url_for('index'))
    calendars = Calendar.get_all(session)
    auth_form = forms.LoginForm()
    return flask.render_template('view_meeting.html', meeting=meeting,
        calendars=calendars, title=meeting.meeting_name,
        auth_form=auth_form)


@APP.route('/meeting/delete/<int:meeting_id>', methods=('GET', 'POST'))
@cla_plus_one_required
def delete_meeting(meeting_id):
    """ Delete a specific meeting given its identifier.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    session = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))
    meeting = Meeting.by_id(session, meeting_id)
    calendar = meeting.calendar_name
    calendars = Calendar.get_all(session)
    deleteform = forms.DeleteMeetingForm()
    if deleteform.validate_on_submit():
        if deleteform.confirm_delete.data:
            if deleteform.confirm_futher_delete.data:
                fedocallib.delete_recursive_meeting(session, meeting)
            else:
                meeting.delete(session)
            try:
                session.commit()
            except Exception, err:
                print 'edit_meeting:',  err
                flask.flash('Could not update this meeting.')
        flask.flash('Meeting deleted')
        return flask.redirect(flask.url_for('calendar', calendar=calendar))
    return flask.render_template('delete_meeting.html', form=deleteform,
        meeting=meeting, calendars=calendars, title=meeting.meeting_name)


if __name__ == '__main__':
    APP.debug = True
    APP.run()
