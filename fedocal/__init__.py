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

__version__ = '0.1.2'

import datetime
import os
from dateutil.relativedelta import relativedelta

import flask
import markdown
import vobject
from flask.ext.fas import FAS
from functools import wraps
from sqlalchemy.exc import SQLAlchemyError

import forms as forms
import fedocal.fedocallib as fedocallib
import fedocallib.dbaction
from fedocal.fedocallib.exceptions import FedocalException
from fedocal.fedocallib.model import (Calendar, Meeting)

# Create the application.
APP = flask.Flask(__name__)
# set up FAS
APP.config.from_object('fedocal.default_config')

if 'FEDOCAL_CONFIG' in os.environ:
    APP.config.from_envvar('FEDOCAL_CONFIG')

FAS = FAS(APP)
SESSION = fedocallib.create_session(APP.config['DB_URL'])


import fedocal.api


def cla_plus_one_required(function):
    """ Flask decorator to retrict access to CLA+1.
To use this decorator you need to have a function named 'auth_login'.
Without that function the redirect if the user is not logged in will not
work.
"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        valid = True
        if flask.g.fas_user is None:
            flask.flash('Login required', 'errors')
            valid = False
        else:
            non_cla_groups = [
                x.name
                for x in flask.g.fas_user.approved_memberships
                if x.group_type != 'cla']
            if len(non_cla_groups) == 0:
                valid = False
                flask.flash('You must be in one more group than the CLA',
                            'errors')
        if not valid:
            return flask.redirect(flask.url_for('auth_login',
                                                next=flask.request.url))
        else:
            return function(*args, **kwargs)
    return decorated_function


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


@APP.template_filter('markdown')
def markdown_filter(text):
    """ Template filter converting a string into html content using the
    markdown library.
    """
    return markdown.markdown(text)


# pylint: disable=W0613
@APP.teardown_request
def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    SESSION.remove()


## Local function
def is_admin():
    """ Return whether the user is admin for this application or not. """
    if not flask.g.fas_user:
        return False
    else:
        if APP.config['ADMIN_GROUP'] in flask.g.fas_user.groups:
            return True


def is_calendar_admin(calendar):
    """ Return whether the user is admin for the specified calendar
    (object).
    """
    if not flask.g.fas_user:
        return False
    else:
        admin_groups = [
            item.strip()
            for item in calendar.calendar_admin_group.split(',')
        ]
        if set(flask.g.fas_user.groups).intersection(set(admin_groups)):
            return True


def is_calendar_manager(calendar):
    """ Return whether the user is a manager for the specified calendar
    (object).
    """
    if not flask.g.fas_user:
        return False
    else:
        manager_groups = [
            item.strip()
            for item in calendar.calendar_manager_group.split(',')
        ]
        if len(manager_groups) == 0:
            return True
        if set(flask.g.fas_user.groups).intersection(set(manager_groups)):
            return True


def is_meeting_manager(meeting):
    """ Return whether the user is one of the manager of the specified
    meeting (object).
    """
    if not flask.g.fas_user:
        return False
    else:
        managers = [item.strip()
                    for item in meeting.meeting_manager.split(',')]
        return flask.g.fas_user.username in managers


def get_timezone():
    """ Return the user's timezone, default to UTC. """
    tzone = 'UTC'
    if flask.g.fas_user:
        if flask.g.fas_user['timezone']:
            tzone = flask.g.fas_user['timezone']
    return tzone


def chunks(item_list, n):
    """ Yield successive n-sized chunks from item_list.
    """
    for i in xrange(0, len(item_list), n):
        yield item_list[i:i+n]


## Flask application
@APP.route('/')
def index():
    """ Displays the index page with containing the first calendar (by
    order of creation and if any) for the current week.
    """
    calendars = Calendar.get_all(SESSION)
    auth_form = forms.LoginForm()
    admin = is_admin()
    return flask.render_template(
        'index.html',
        calendars=calendars,
        calendars_table=chunks(calendars, 3),
        auth_form=auth_form,
        admin=admin)


# pylint: disable=R0914
@APP.route('/<calendar_name>/',
           defaults={'year': None, 'month': None, 'day': None})
@APP.route('/<calendar_name>/<int:year>/<int:month>/<int:day>/')
def calendar(calendar_name, year, month, day):
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
    tzone = get_timezone()
    meetings = fedocallib.get_meetings(
        SESSION, calendarobj, year, month, day, tzone=tzone)
    next_week = fedocallib.get_next_week(
        week_start.year, week_start.month, week_start.day)
    prev_week = fedocallib.get_previous_week(
        week_start.year, week_start.month, week_start.day)
    auth_form = forms.LoginForm()
    admin = is_admin()
    month_name = week_start.strftime('%B')

    day_index = None
    today = datetime.date.today()
    if today > week_start and today < week_start + datetime.timedelta(days=7):
        day_index = fedocallib.get_week_day_index(
            today.year, today.month, today.day)

    curmonth_cal = fedocallib.get_html_monthly_cal(
        year=year, month=month, day=day, calendar_name=calendar_name)
    return flask.render_template(
        'agenda.html',
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


@APP.route('/list/<calendar_name>/',
           defaults={'year': None, 'month': None, 'day': None})
@APP.route('/list/<calendar_name>/<int:year>/',
           defaults={'month': None, 'day': None})
@APP.route('/list/<calendar_name>/<int:year>/<int:month>/',
           defaults={'day': None})
@APP.route('/list/<calendar_name>/<int:year>/<int:month>/<int:day>/')
def calendar_list(calendar_name, year, month, day):
    """ Display in a list form all the meetings of a given calendar.
    By default it displays all the meetings of the current year but this
    can be more restricted to a month or even a day.

    :arg calendar_name: the name of the calendar that one would like to
        consult.
    :arg year: the year of the date one would like to consult.
    :arg month: the month of the date one would like to consult.
    :arg day: the day of the date one would like to consult.
    """
    inyear = year
    if not year:
        inyear = datetime.date.today().year
    inmonth = month
    if not month:
        inmonth = 1
    inday = day
    if not day:
        inday = 1
    start_date = datetime.date(inyear, inmonth, inday)
    if not month and not day:
        end_date = start_date + relativedelta(years=+1)
    elif not day:
        end_date = start_date + relativedelta(months=+1)
    else:
        end_date = start_date + relativedelta(days=+1)

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    tzone = get_timezone()
    meetings = fedocallib.get_by_date(
        SESSION, calendarobj, start_date, end_date, tzone)

    month_name = datetime.date.today().strftime('%B')
    auth_form = forms.LoginForm()
    admin = is_admin()

    curmonth_cal = fedocallib.get_html_monthly_cal(
        year=year, month=month, day=day, calendar_name=calendar_name)
    return flask.render_template(
        'meeting_list.html',
        calendar=calendarobj,
        month=month_name,
        meetings=meetings,
        tzone=tzone,
        year=inyear,
        auth_form=auth_form,
        curmonth_cal=curmonth_cal,
        admin=admin)


@APP.route('/ical/')
def ical_all():
    """ Returns a iCal feed of all calendars from today - 1 month to
    today + 6 month.
    """
    startd = datetime.date.today() - datetime.timedelta(days=30)
    endd = datetime.date.today() + datetime.timedelta(days=180)
    ical = vobject.iCalendar()
    meetings = []
    for calendar in Calendar.get_all(SESSION):
        meetings.extend(fedocallib.get_meetings_by_date(
            SESSION, calendar.calendar_name, startd, endd))
    fedocallib.add_meetings_to_vcal(ical, meetings)
    return flask.Response(ical.serialize(), mimetype='text/calendar')


@APP.route('/ical/<calendar_name>/')
def ical_out(calendar_name):
    """ Returns a iCal feed of the calendar from today - 1 month to
    today + 6 month.

    :arg calendar_name: the name of the calendar for which one would
        like to get the iCal feed.
    """
    startd = datetime.date.today() - datetime.timedelta(days=30)
    endd = datetime.date.today() + datetime.timedelta(days=180)
    meetings = fedocallib.get_meetings_by_date(
        SESSION, calendar_name, startd, endd)
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
    tzone = get_timezone()
    regular_meetings = fedocallib.get_future_regular_meeting_of_user(
        SESSION, flask.g.fas_user.username, tzone=tzone)
    single_meetings = fedocallib.get_future_single_meeting_of_user(
        SESSION, flask.g.fas_user.username, tzone=tzone)
    past_meetings = fedocallib.get_past_meeting_of_user(
        SESSION, flask.g.fas_user.username, tzone=tzone)
    admin = is_admin()
    return flask.render_template(
        'my_meeting.html',
        title='My meeting', regular_meetings=regular_meetings,
        single_meetings=single_meetings, pas_meetings=past_meetings,
        admin=admin, tzone=tzone)


@APP.route('/login/', methods=('GET', 'POST'))
def auth_login():
    """ Method to log into the application. """
    if flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    form = forms.LoginForm()
    # pylint: disable=E1101
    if form.validate_on_submit():
        if FAS.login(form.username.data, form.password.data):
            flask.flash('Welcome, %s' % flask.g.fas_user.username)
            return flask.redirect(flask.url_for('index'))
        else:
            flask.flash('Incorrect username or password', 'errors')
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
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    if not is_admin():
        flask.flash('You are not a fedocal admin, you are not allowed '
                    'to add calendars.', 'errors')
        return flask.redirect(flask.url_for('index'))

    form = forms.AddCalendarForm()
    # pylint: disable=E1101
    if form.validate_on_submit():
        calendarobj = Calendar(
            calendar_name=form.calendar_name.data,
            calendar_contact=form.calendar_contact.data,
            calendar_description=form.calendar_description.data,
            calendar_manager_group=form.calendar_manager_groups.data,
            calendar_admin_group=form.calendar_admin_groups.data,
            calendar_multiple_meetings=bool(
                form.calendar_multiple_meetings.data),
            calendar_regional_meetings=bool(
                form.calendar_regional_meetings.data),
        )
        try:
            calendarobj.save(SESSION)
            SESSION.commit()
        except SQLAlchemyError, err:
            SESSION.rollback()
            print 'add_calendar:', err
            flask.flash('Could not add this calendar to the database',
                        'errors')
            return flask.render_template('add_calendar.html',
                                         form=form)
        flask.flash('Calendar added')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template('add_calendar.html', form=form)


# pylint: disable=R0915,R0912,R0911
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
    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if not (is_calendar_manager(calendarobj)
            or is_calendar_admin(calendarobj)
            or is_admin()):
        flask.flash('You are not one of the manager of this calendar, '
                    'or one of its admins, you are not allowed to add '
                    'new meetings.', 'errors')
        return flask.redirect(flask.url_for('calendar',
                                            calendar_name=calendar_name))

    form = forms.AddMeetingForm()
    tzone = get_timezone()
    calendarobj = Calendar.by_id(SESSION, calendar_name)
    # pylint: disable=E1101
    if form.validate_on_submit():
        try:
            fedocallib.add_meeting(
                session=SESSION,
                calendarobj=calendarobj,
                fas_user=flask.g.fas_user,
                meeting_name=form.meeting_name.data,
                meeting_date=form.meeting_date.data,
                meeting_date_end=form.meeting_date_end.data,
                meeting_time_start=form.meeting_time_start.data,
                meeting_time_stop=form.meeting_time_stop.data,
                comanager=form.comanager.data,
                meeting_information=form.information.data,
                meeting_region=form.meeting_region.data,
                tzone=get_timezone(),
                frequency=form.frequency.data,
                end_repeats=form.end_repeats.data,
                remind_when=form.remind_when.data,
                remind_who=form.remind_who.data,
                full_day=form.full_day.data,
                admin=is_admin())
        except FedocalException, err:
            flask.flash(err, 'warnings')
            return flask.render_template(
                'add_meeting.html', calendar=calendarobj, form=form,
                tzone=tzone)
        except SQLAlchemyError, err:
            SESSION.rollback()
            print 'add_meeting:', err
            flask.flash('Could not add this meeting to this calendar',
                        'errors')
            return flask.render_template(
                'add_meeting.html', calendar=calendarobj, form=form,
                tzone=tzone)

        flask.flash('Meeting added')
        return flask.redirect(flask.url_for(
            'calendar', calendar_name=calendarobj.calendar_name,
            year=form.meeting_date.data.year,
            month=form.meeting_date.data.month,
            day=form.meeting_date.data.day))

    return flask.render_template(
        'add_meeting.html', calendar=calendarobj, form=form, tzone=tzone)


# pylint: disable=R0915,R0912,R0911
# CLA + 1
@APP.route('/meeting/edit/<int:meeting_id>/', methods=('GET', 'POST'))
@cla_plus_one_required
def edit_meeting(meeting_id):
    """ Edit a specific meeting based on the meeting identifier.

    :arg meeting_id: the identifier of the meeting to edit.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    meeting = Meeting.by_id(SESSION, meeting_id)
    calendarobj = Calendar.by_id(SESSION, meeting.calendar_name)
    if not (is_meeting_manager(meeting)
            or is_calendar_admin(meeting.calendarobj)
            or is_admin()):
        flask.flash('You are not one of the manager of this meeting, '
                    'or an admin, you are not allowed to edit it.',
                    'errors')
        return flask.redirect(flask.url_for('view_meeting',
                                            meeting_id=meeting_id))

    tzone = get_timezone()
    form = forms.AddMeetingForm()
    # pylint: disable=E1101
    if form.validate_on_submit():
        try:
            fedocallib.edit_meeting(
                session=SESSION,
                meeting=meeting,
                calendarobj=calendarobj,
                fas_user=flask.g.fas_user,
                meeting_name=form.meeting_name.data,
                meeting_date=form.meeting_date.data,
                meeting_date_end=None,
                meeting_time_start=form.meeting_time_start.data,
                meeting_time_stop=form.meeting_time_stop.data,
                comanager=form.comanager.data,
                meeting_information=form.information.data,
                meeting_region=form.meeting_region.data,
                tzone=get_timezone(),
                recursion_frequency=form.frequency.data,
                recursion_ends=form.end_repeats.data,
                remind_when=form.remind_when.data,
                remind_who=form.remind_who.data,
                full_day=form.full_day.data,
                edit_all_meeting=form.recursive_edit.data,
                admin=is_admin())
        except FedocalException, err:
            flask.flash(err, 'warnings')
            return flask.render_template(
                'edit_meeting.html', meeting=meeting, calendar=calendarobj,
                form=form, tzone=tzone)
        except SQLAlchemyError, err:
            SESSION.rollback()
            print 'edit_meeting:', err
            flask.flash('Could not update this meeting.', 'errors')
            return flask.render_template(
                'edit_meeting.html', meeting=meeting,
                calendar=calendarobj, form=form, tzone=tzone)

        flask.flash('Meeting updated')
        return flask.redirect(flask.url_for('view_meeting',
                              meeting_id=meeting_id))
    else:
        if meeting.recursion_frequency and meeting.recursion_ends and \
            fedocallib.is_date_in_future(
                meeting.recursion_ends, meeting.meeting_time_start):
            cnt = 0
            meetingobj = Meeting.copy(meeting)
            while meetingobj.meeting_date < datetime.date.today():
                meetingobj = Meeting.copy(meeting)
                meetingobj.meeting_date = meetingobj.meeting_date + \
                    datetime.timedelta(
                        days=meetingobj.recursion_frequency * cnt)
                cnt = cnt + 1
            meeting = meetingobj
        if not fedocallib.is_date_in_future(
                meeting.meeting_date,
                meeting.meeting_time_start):
            flask.flash('This meeting has already occured, you may not '
                        'change it anymore', 'warnings')
            return flask.redirect(flask.url_for('my_meetings'))
        form = forms.AddMeetingForm(meeting=meeting, tzone=get_timezone())
    return flask.render_template(
        'edit_meeting.html', meeting=meeting, calendar=calendarobj,
        form=form, tzone=tzone)


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
    tzone = get_timezone()
    if not meeting:
        flask.flash('No meeting could be found for this identifier',
                    'errors')
        return flask.redirect(flask.url_for('index'))
    meeting = fedocallib.convert_meeting_timezone(meeting, 'UTC', tzone)
    auth_form = forms.LoginForm()
    editor = is_admin()
    if not editor:
        if is_meeting_manager(meeting) or is_calendar_admin(
                meeting.calendar):
            editor = True
    return flask.render_template(
        'view_meeting.html',
        full=full,
        meeting=meeting,
        tzone=tzone,
        title=meeting.meeting_name,
        editor=editor,
        auth_form=auth_form)


@APP.route('/meeting/delete/<int:meeting_id>/', methods=('GET', 'POST'))
@cla_plus_one_required
def delete_meeting(meeting_id):
    """ Delete a specific meeting given its identifier.

    :arg meeting_id: the identifier of the meeting to delete.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    meeting = Meeting.by_id(SESSION, meeting_id)
    if not (is_meeting_manager(meeting)
            or is_calendar_admin(meeting.calendar)
            or is_admin()):
        flask.flash('You are not one of the manager of this meeting, '
                    'or an admin, you are not allowed to delete it.',
                    'errors')
        return flask.redirect(flask.url_for('view_meeting',
                                            meeting_id=meeting_id))

    calendars = Calendar.get_all(SESSION)
    deleteform = forms.DeleteMeetingForm()
    # pylint: disable=E1101
    if deleteform.validate_on_submit():
        if deleteform.confirm_delete.data:
            if deleteform.confirm_futher_delete.data:
                fedocallib.delete_recursive_meeting(SESSION, meeting)
            else:
                meeting.delete(SESSION)
            try:
                SESSION.commit()
            except SQLAlchemyError, err:
                SESSION.rollback()
                print 'edit_meeting:', err
                flask.flash('Could not update this meeting.', 'error')
        flask.flash('Meeting deleted')
        return flask.redirect(flask.url_for(
            'calendar', calendar_name=meeting.calendar_name))
    return flask.render_template(
        'delete_meeting.html',
        form=deleteform,
        meeting=meeting,
        calendars=calendars,
        title=meeting.meeting_name)


@APP.route('/calendar/delete/<calendar_name>/', methods=('GET', 'POST'))
@cla_plus_one_required
def delete_calendar(calendar_name):
    """ Delete a specific calendar given its identifier.

    :arg calendar_name: the identifier of the calendar to delete.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    if not is_admin():
        flask.flash('You are not a fedocal admin, you are not allowed '
                    'to delete the calendar.', 'errors')
        return flask.redirect(flask.url_for('index'))

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    deleteform = forms.DeleteCalendarForm()
    # pylint: disable=E1101
    if deleteform.validate_on_submit():
        if deleteform.confirm_delete.data:
            calendarobj.delete(SESSION)
            try:
                SESSION.commit()
            except SQLAlchemyError, err:
                SESSION.rollback()
                print 'delete_calendar:', err
                flask.flash('Could not delete this calendar.', 'errors')
        flask.flash('Calendar deleted')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template(
        'delete_calendar.html', form=deleteform, calendarobj=calendarobj)


# pylint: disable=R0915,R0912,R0911
# CLA + 1
@APP.route('/calendar/edit/<calendar_name>/', methods=('GET', 'POST'))
@cla_plus_one_required
def edit_calendar(calendar_name):
    """ Edit a specific calendar based on the calendar identifier.

    :arg calendar_name: the identifier of the calendar to edit.
    """
    if not flask.g.fas_user:
        return flask.redirect(flask.url_for('index'))
    if not is_admin():
        flask.flash('You are not a fedocal admin, you are not allowed '
                    'to edit the calendar.', 'errors')
        return flask.redirect(flask.url_for('index'))

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    form = forms.AddCalendarForm()
    # pylint: disable=E1101
    if form.validate_on_submit():
        try:
            calendarobj.calendar_name = form.calendar_name.data
            calendarobj.calendar_contact = form.calendar_contact.data
            calendarobj.calendar_description = form.calendar_description.data
            calendarobj.calendar_manager_group = \
                form.calendar_manager_groups.data
            calendarobj.calendar_admin_group = \
                form.calendar_admin_groups.data
            calendarobj.calendar_multiple_meetings = bool(
                form.calendar_multiple_meetings.data)
            calendarobj.calendar_regional_meetings = bool(
                form.calendar_regional_meetings.data)
            calendarobj.save(SESSION)
            SESSION.commit()
        except SQLAlchemyError, err:
            SESSION.rollback()
            print 'edit_calendar:', err
            flask.flash('Could not update this calendar.', 'errors')
            return flask.render_template(
                'edit_calendar.html', form=form, calendar=calendarobj)

        flask.flash('Calendar updated')
        return flask.redirect(flask.url_for(
            'calendar', calendar_name=calendarobj.calendar_name))
    else:
        form = forms.AddCalendarForm(calendar=calendarobj)
    return flask.render_template('edit_calendar.html', form=form,
                                 calendar=calendarobj)
