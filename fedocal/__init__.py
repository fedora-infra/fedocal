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

## These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources


import ConfigParser
import os
import datetime
from urlparse import urljoin, urlparse
import vobject

import flask
from flask_fas import FAS, cla_plus_one_required

import forms as forms
import fedocallib as fedocallib
from fedocallib.model import (Calendar, Meeting, Reminder)

CONFIG = ConfigParser.ConfigParser()
if os.path.exists('/etc/fedocal.cfg'):  # pragma: no cover
    CONFIG.readfp(open('/etc/fedocal.cfg'))
else:
    CONFIG.readfp(open(os.path.join(os.path.dirname(
        os.path.abspath(__file__)),
        'fedocal.cfg')))

# Create the application.
APP = flask.Flask(__name__)
# set up FAS
FAS = FAS(APP)
APP.secret_key = CONFIG.get('fedocal', 'secret_key')
SESSION = fedocallib.create_session(CONFIG.get('fedocal', 'db_url'))

@APP.context_processor
def inject_calendars():
    """ With this decorator we add the list of all the calendars
    available to all the function, so the variable calendars is available
    in all templates.
    """
    calendars = Calendar.get_all(SESSION)

    return dict(calendars=calendars)


@APP.template_filter('WeekHeading')
def reverse_filter(weekdays):
    """ Template filter returning the heading string which is located in
    between the two navigation buttons on the agenda template.
    """
    return "%s - %s" % (weekdays[0].strftime('%d %b'),
        weekdays[-1].strftime('%d %b %Y'))


@APP.teardown_request
def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    SESSION.remove()


## Local function
def is_admin():
    """ Return wether the user is admin for this application or not. """
    if not flask.g.fas_user:
        return False
    else:
        if CONFIG.get('fedocal', 'admin_group') in flask.g.fas_user.groups:
            return True
    return False


def get_timezone():
    """ Return the user's timezone, default to UTC. """
    tzone = 'UTC'
    if flask.g.fas_user:
        if flask.g.fas_user['timezone']:
            tzone = flask.g.fas_user['timezone']
    return tzone


## Flask application
@APP.route('/')
def index():
    """ Displays the index page with containing the first calendar (by
    order of creation and if any) for the current week.
    """
    calendars = Calendar.get_all(SESSION)
    if calendars:
        return calendar(calendars[0].calendar_name)
    else:
        auth_form = forms.LoginForm()
        admin = is_admin()
        return flask.render_template('agenda.html',
            calendar=None,
            auth_form=auth_form,
            admin=admin)


@APP.route('/<calendar_name>/')
def calendar(calendar_name):
    """ Display the current week for a specific calendar.

    :arg calendar_name: the name of the calendar that one would like to
        consult.
    """
    return calendar_fullday(calendar_name, year=None, month=None,
        day=None)


@APP.route('/<calendar_name>/<int:year>/<int:month>/<int:day>/')
def calendar_fullday(calendar_name, year, month, day):
    """ Display the week of a specific date for a specified calendar.

    :arg calendar_name: the name of the calendar that one would like to
        consult.
    :arg year: the year of the date one would like to consult.
    :arg month: the month of the date one would like to consult.
    :arg day: the day of the date one would like to consult.
    """
    calendarobj = Calendar.by_id(SESSION, calendar_name)
    week_start = fedocallib.get_start_week(year, month, day)
    weekdays = fedocallib.get_week_days(year, month, day)
    day_index = fedocallib.get_week_day_index(year, month, day)
    tzone = get_timezone()
    meetings = fedocallib.get_meetings(SESSION, calendarobj, year,
        month, day, tzone=tzone)
    next_week = fedocallib.get_next_week(week_start.year,
        week_start.month, week_start.day)
    prev_week = fedocallib.get_previous_week(week_start.year,
        week_start.month, week_start.day)
    auth_form = forms.LoginForm()
    admin = is_admin()
    month_name = week_start.strftime('%B')
    curmonth_cal = fedocallib.get_html_monthly_cal(year=year,
        month=month, calendar_name=calendar_name)
    return flask.render_template('agenda.html',
        calendar=calendarobj,
        month=month_name,
        weekdays=weekdays,
        day_index=day_index,
        meetings=meetings,
        tzone=tzone,
        next_week=next_week,
        prev_week=prev_week,
        auth_form=auth_form,
        curmonth_cal=curmonth_cal,
        admin=admin)


@APP.route('/ical/<calendar_name>/')
def ical_out(calendar_name):
    """ Returns a iCal feed of the calendar from today - 1 month to
    today + 6 month.

    :arg calendar_name: the name of the calendar for which one would
        like to get the iCal feed.
    """
    startd = datetime.date.today() - datetime.timedelta(days=30)
    endd = datetime.date.today() + datetime.timedelta(days=180)
    meetings = fedocallib.get_meetings_by_date(SESSION, calendar_name,
        startd, endd)
    ical = vobject.iCalendar()
    fedocallib.add_meetings_to_vcal(ical, meetings)
    return flask.Response(ical.serialize(), mimetype='text/calendar')


# CLA + 1
@APP.route('/mine/')
@cla_plus_one_required
def my_meetings():
    """ Method to visualize and manage the meeting in which you are
    involved, either because you created them or because someone gave
    you manager rights to the meeting.
    """
    regular_meetings = fedocallib.get_future_regular_meeting_of_user(SESSION,
        flask.g.fas_user.username)
    single_meetings = fedocallib.get_future_single_meeting_of_user(SESSION,
        flask.g.fas_user.username)
    past_meetings = fedocallib.get_past_meeting_of_user(SESSION,
        flask.g.fas_user.username)
    admin = is_admin()
    return flask.render_template('my_meeting.html',
        title='My meeting', regular_meetings=regular_meetings,
        single_meetings=single_meetings, pas_meetings=past_meetings,
        admin=admin)


@APP.route('/login/', methods=('GET', 'POST'))
def auth_login():
    """ Method to log into the application. """
    if flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    form = forms.LoginForm()
    if form.validate_on_submit():
        if FAS.login(form.username.data, form.password.data):
            flask.flash('Welcome, %s' % flask.g.fas_user.username)
            return flask.redirect(flask.url_for('index'))
        else:
            flask.flash('Incorrect username or password')
    return flask.redirect(flask.url_for('index'))


@APP.route('/logout/')
def auth_logout():
    """ Method to log out from the application. """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    FAS.logout()
    flask.flash('You have been logged out')
    return flask.redirect(flask.url_for('index'))


# CLA + 1 (and admin)
@APP.route('/calendar/add/', methods=('GET', 'POST'))
@cla_plus_one_required
def add_calendar():
    """ Add a calendar to the database.
    This function is only accessible to admin of the webapp.
    """
    if not flask.g.fas_user or not is_admin():
        return flask.redirect(flask.url_for('index'))
    form = forms.AddCalendarForm()
    if form.validate_on_submit():
        calendarobj = Calendar(
            form.calendar_name.data,
            form.calendar_description.data,
            form.calendar_manager_groups.data,
            bool(form.calendar_multiple_meetings.data),
            bool(form.calendar_regional_meetings.data),
            )
        try:
            calendarobj.save(SESSION)
            SESSION.commit()
        except Exception, err:
            print err
            flask.flash('Could not add this calendar to the database')
            return flask.render_template('add_calendar.html',
                form=form)
        flask.flash('Calendar added')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('add_calendar.html', form=form)


# CLA + 1
@APP.route('/<calendar_name>/add/', methods=('GET', 'POST'))
@cla_plus_one_required
def add_meeting(calendar_name):
    """ Add a meeting to the database.
    This function is only available to CLA+1 member or members of the
    group administrating of the said calendar.

    :arg calendar_name, name of the calendar in which to add the meeting.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    form = forms.AddMeetingForm()
    tzone = get_timezone()
    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if form.validate_on_submit():
        if not fedocallib.is_user_managing_in_calendar(SESSION,
            calendarobj.calendar_name, flask.g.fas_user):
            flask.flash('You are not allowed to add a meeting to'\
                ' this calendar')
            return flask.redirect(flask.url_for('index'))
        if not fedocallib.is_date_in_future(form.meeting_date.data,
            form.meeting_time_start.data):
            flask.flash('The date you entered is in the past')
            return flask.redirect(flask.url_for('add_meeting',
                calendar_name=calendarobj.calendar_name, form=form,
                tzone=tzone))
        elif int(form.meeting_time_start.data) > \
            int(form.meeting_time_stop.data):
            flask.flash('The start time you have entered is later than'\
                ' the stop time.')
            flask.render_template('add_meeting.html',
                    calendar=calendarobj, form=form, tzone=tzone)
        elif bool(calendarobj.calendar_multiple_meetings) or \
            (not bool(calendarobj.calendar_multiple_meetings) and \
            fedocallib.agenda_is_free(SESSION,
                calendarobj,
                form.meeting_date.data,
                int(form.meeting_time_start.data),
                int(form.meeting_time_stop.data)
            )):

            manager = '%s,' % flask.g.fas_user.username
            end_date = form.end_repeats.data
            if not end_date and form.frequency.data:
                end_date = datetime.date(2025, 12, 31)
            frequency = form.frequency.data
            if not frequency:
                frequency = None
            region = form.meeting_region.data
            if not calendarobj.calendar_regional_meetings or not region:
                region = None
            meeting_end_date = form.meeting_date_end.data
            if not meeting_end_date:
                meeting_end_date = form.meeting_date.data
            
            tzone = get_timezone()
            meeting_time_start = fedocallib.convert_time(
                datetime.datetime(2000, 1, 1,
                    int(form.meeting_time_start.data), 0),
                tzone, 'UTC')
            meeting_time_stop = fedocallib.convert_time(
                datetime.datetime(2000, 1, 1,
                    int(form.meeting_time_stop.data), 0),
                tzone, 'UTC')
            meeting = Meeting(
                meeting_name=form.meeting_name.data,
                meeting_manager=manager,
                meeting_date=form.meeting_date.data,
                meeting_date_end=meeting_end_date,
                meeting_time_start=meeting_time_start.time(),
                meeting_time_stop=meeting_time_stop.time(),
                meeting_information=form.information.data,
                calendar_name=calendarobj.calendar_name,
                reminder_id=None,
                meeting_region=region,
                recursion_frequency=frequency,
                recursion_ends=end_date)
            meeting.save(SESSION)
            try:
                SESSION.flush()
            except Exception, err:
                print 'add_meeting:', err
                flask.flash('Could not add this meeting to this calendar')
                return flask.render_template('add_meeting.html',
                    calendar=calendarobj, form=form, tzone=tzone)

            if form.remind_when.data and form.remind_who.data:
                reminder = Reminder(form.remind_when.data,
                                    form.remind_who.data,
                                    None)
                reminder.save(SESSION)
                try:
                    SESSION.flush()
                    meeting.reminder = reminder
                    SESSION.flush()
                except Exception, err:
                    print 'add_meeting:', err
                    flask.flash('Could not add this reminder to this meeting')
                    return flask.render_template('add_meeting.html',
                        calendar=calendarobj, form=form, tzone=tzone)

            try:
                SESSION.commit()
            except Exception, err:
                flask.flash(
                    'Something went wrong while commiting to the DB.')
                flask.render_template('add_meeting.html',
                    calendar=calendarobj, form=form, tzone=tzone)

            flask.flash('Meeting added')
            return flask.redirect(flask.url_for('calendar',
                calendar_name=calendarobj.calendar_name))
        else:
            flask.flash(
                'The start time you have entered is already occupied.')
            return flask.render_template('add_meeting.html',
                calendar=calendarobj, form=form, tzone=tzone)
    return flask.render_template('add_meeting.html',
        calendar=calendarobj, form=form, tzone=tzone)


# CLA + 1
@APP.route('/meeting/edit/<int:meeting_id>/', methods=('GET', 'POST'))
@cla_plus_one_required
def edit_meeting(meeting_id):
    """ Edit a specific meeting based on the meeting identifier.

    :arg meeting_id: the identifier of the meeting to edit.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    if not flask.g.fas_user.username in \
        Meeting.get_managers(SESSION, meeting_id):
        flask.flash('You are not one of the manager of this meeting, '\
            'you are not allowed to edit it.')
        return flask.redirect(flask.url_for('index'))
    meeting = Meeting.by_id(SESSION, meeting_id)
    calendarobj = Calendar.by_id(SESSION, meeting.calendar_name)
    if not fedocallib.is_date_in_future(meeting.meeting_date,
        meeting.meeting_time_start.hour):
        flask.flash('This meeting has already occured, you may not '\
            'change it anymore')
        return flask.redirect(flask.url_for('index'))
    form = forms.AddMeetingForm()
    if form.validate_on_submit():
        try:
            meeting.meeting_name = form.meeting_name.data
            meeting.meeting_manager = '%s,%s' % (
                flask.g.fas_user.username, form.comanager.data)
            meeting.meeting_date = form.meeting_date.data
            meeting_end_date = form.meeting_date_end.data
            if not meeting_end_date:
                meeting_end_date = form.meeting_date.date
            meeting.meeting_end_date = meeting_end_date
            meeting.meeting_time_start = datetime.time(int(
                    form.meeting_time_start.data))
            meeting_time_stop=datetime.time(int(
                    form.meeting_time_stop.data))
            meeting.meeting_information = form.information.data

            region = form.meeting_region.data
            if not region:
                region = None
            meeting.meeting_region=region

            frequency = form.frequency.data
            if not frequency:
                frequency = None
            meeting.recursion_frequency = frequency

            ends_date = form.end_repeats.data
            if not ends_date:
                ends_date = datetime.date(2025, 12, 31)
            meeting.recursion_ends = ends_date

            if form.remind_when.data and form.remind_who.data:
                if meeting.reminder_id:
                    meeting.reminder.reminder_offset = form.remind_when.data
                    meeting.reminder.reminder_to = form.remind_who.data
                    meeting.reminder.save(SESSION)
                else:
                    reminder = Reminder(form.remind_when.data,
                                    form.remind_who.data,
                                    None)
                    reminder.save(SESSION)
                    try:
                        SESSION.flush()
                        meeting.reminder = reminder
                        SESSION.flush()
                    except Exception, err:
                        print 'edit_meeting:', err
                        flask.flash('Could not edit the reminder of '\
                            'this meeting')
                        return flask.render_template('edit_meeting.html',
                            meeting=meeting, calendar=calendarobj,
                            form=form)
            elif meeting.reminder_id:
                try:
                    meeting.reminder.delete(SESSION)
                except Exception, err:
                    print 'edit_meeting:', err

            meeting.save(SESSION)
            SESSION.commit()
        except Exception, err:
            print 'edit_meeting:',  err
            flask.flash('Could not update this meeting.')
            return flask.redirect(flask.url_for('edit_meeting',
                meeting_id=meeting_id))
        flask.flash('Meeting updated')
        return flask.redirect(flask.url_for('view_meeting',
            meeting_id=meeting_id))
    else:
        form = forms.AddMeetingForm(meeting=meeting)
    return flask.render_template('edit_meeting.html', meeting=meeting,
            calendar=calendarobj, form=form)


@APP.route('/meeting/<int:meeting_id>/', methods=('GET', 'POST'))
def view_meeting(meeting_id):
    """ View a specific meeting given its identifier.

    :arg meeting_id: the identifier of the meeting to visualize.
    """
    return view_meeting_page(meeting_id, True)


@APP.route('/meeting/<int:meeting_id>/<int:full>/', methods=('GET', 'POST'))
def view_meeting_page(meeting_id, full):
    """ View a specific meeting given its identifier.

    :arg meeting_id: the identifier of the meeting to visualize.
    """
    meeting = Meeting.by_id(SESSION, meeting_id)
    if not meeting:
        flask.flash('No meeting could be found for this identifier')
        return flask.redirect(flask.url_for('index'))
    auth_form = forms.LoginForm()
    return flask.render_template('view_meeting.html', full=full,
            meeting=meeting,
            title=meeting.meeting_name, auth_form=auth_form)


@APP.route('/meeting/delete/<int:meeting_id>/', methods=('GET', 'POST'))
@cla_plus_one_required
def delete_meeting(meeting_id):
    """ Delete a specific meeting given its identifier.

    :arg meeting_id: the identifier of the meeting to delete.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    meeting = Meeting.by_id(SESSION, meeting_id)
    calendars = Calendar.get_all(SESSION)
    deleteform = forms.DeleteMeetingForm()
    if deleteform.validate_on_submit():
        if deleteform.confirm_delete.data:
            if deleteform.confirm_futher_delete.data:
                fedocallib.delete_recursive_meeting(SESSION, meeting)
            else:
                meeting.delete(SESSION)
            try:
                SESSION.commit()
            except Exception, err:
                print 'edit_meeting:',  err
                flask.flash('Could not update this meeting.')
        flask.flash('Meeting deleted')
        return flask.redirect(flask.url_for('calendar',
            calendar_name=meeting.calendar_name))
    return flask.render_template('delete_meeting.html',
        form=deleteform,
        meeting=meeting,
        calendars=calendars,
        title=meeting.meeting_name)


### API

@APP.route('/api/')
def api():
    """ Display the api information page. """
    auth_form = forms.LoginForm()
    admin = is_admin()
    return flask.render_template('api.html',
        auth_form=auth_form,
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


if __name__ == '__main__':  # pragma: no cover
    APP.debug = True
    APP.run()
