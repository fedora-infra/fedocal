#-*- coding: utf-8 -*-

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

## These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

__version__ = '0.9.2'

import datetime
import logging
import os
import urllib
import urlparse
from dateutil import parser
from logging.handlers import SMTPHandler

import flask
import markdown
import vobject
from dateutil.relativedelta import relativedelta
from flask_fas_openid import FAS
from functools import wraps
from pytz import common_timezones
from sqlalchemy.exc import SQLAlchemyError
from werkzeug import secure_filename

import fedocal.forms as forms
import fedocal.fedocallib as fedocallib
import fedocal.proxy
from fedocal.fedocallib.exceptions import FedocalException
from fedocal.fedocallib.model import (Calendar, Meeting)

import fedocal.fedocallib.fedmsgshim as fedmsg

# Create the application.
APP = flask.Flask(__name__)

# set up FAS
APP.config.from_object('fedocal.default_config')

if 'FEDOCAL_CONFIG' in os.environ:
    APP.config.from_envvar('FEDOCAL_CONFIG')

# Points the template and static folders to the desired theme
APP.template_folder = os.path.join(
    APP.template_folder, APP.config['THEME_FOLDER'])
APP.static_folder = os.path.join(
    APP.static_folder, APP.config['THEME_FOLDER'])

FAS = FAS(APP)
APP.wsgi_app = fedocal.proxy.ReverseProxied(APP.wsgi_app)
SESSION = fedocallib.create_session(APP.config['DB_URL'])

# Set up the logger
## Send emails for big exception
mail_handler = SMTPHandler(
    APP.config.get('SMTP_SERVER', '127.0.0.1'),
    'nobody@fedoraproject.org',
    APP.config.get('MAIL_ADMIN', APP.config['EMAIL_ERROR']),
    'Fedocal error')
mail_handler.setFormatter(logging.Formatter('''
    Message type:       %(levelname)s
    Location:           %(pathname)s:%(lineno)d
    Module:             %(module)s
    Function:           %(funcName)s
    Time:               %(asctime)s

    Message:

    %(message)s
'''))
mail_handler.setLevel(logging.ERROR)
if not APP.debug:
    APP.logger.addHandler(mail_handler)

## Send classic logs into syslog
handler = logging.StreamHandler()
handler.setLevel(APP.config.get('log_level', 'INFO'))
APP.logger.addHandler(handler)

LOG = APP.logger


import fedocal.api


def authenticated():
    return hasattr(flask.g, 'fas_user') and flask.g.fas_user


def cla_plus_one_required(function):
    """ Flask decorator to retrict access to CLA+1.
To use this decorator you need to have a function named 'auth_login'.
Without that function the redirect if the user is not logged in will not
work.
"""
    @wraps(function)
    def decorated_function(*args, **kwargs):
        """ Decorated function, actually does the work. """
        if not authenticated():
            return flask.redirect(flask.url_for('auth_login',
                                                next=flask.request.url))
        elif not flask.g.fas_user.cla_done:
            flask.flash('You must sign the CLA (Contributor License '
                        'Agreement to use fedocal', 'errors')
            return flask.redirect(flask.url_for('.index'))
        else:
            if len(flask.g.fas_user.groups) == 0:
                flask.flash('You must be in one more group than the CLA',
                            'errors')
                return flask.redirect(flask.url_for('index'))
        return function(*args, **kwargs)
    return decorated_function


@APP.context_processor
def inject_variables():
    """ With this decorator we can set some variables to all templates.
    """
    calendars = Calendar.get_all(SESSION)
    user_admin = is_admin()

    return dict(
        calendars=calendars,
        version=__version__,
        admin=user_admin,
        user_tz=get_timezone())


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
    if text:
        return markdown.markdown(text)


# pylint: disable=W0613
@APP.teardown_request
def shutdown_session(exception=None):
    """ Remove the DB session at the end of each request. """
    SESSION.remove()


## Local function
def is_admin():
    """ Return whether the user is admin for this application or not. """
    if not authenticated() \
            or not flask.g.fas_user.cla_done \
            or len(flask.g.fas_user.groups) < 1:
        return False

    admins = APP.config['ADMIN_GROUP']
    if isinstance(admins, basestring):
        admins = set([admins])
    else:  # pragma: no cover
        admins = set(admins)
    groups = set(flask.g.fas_user.groups)
    return not groups.isdisjoint(admins)


def is_calendar_admin(calendarobj):
    """ Return whether the user is admin for the specified calendar
    (object).
    """
    if not authenticated():
        return False
    elif is_admin():
        return True
    elif calendarobj.calendar_admin_group:
        admin_groups = [
            item.strip()
            for item in calendarobj.calendar_admin_group.split(',')
        ]
        return bool(
            set(flask.g.fas_user.groups).intersection(set(admin_groups)))
    else:
        return False


def is_calendar_manager(calendarobj):
    """ Return whether the user is a manager for the specified calendar
    (object).
    """
    if not authenticated():
        return False
    elif is_calendar_admin(calendarobj):
        return True
    else:
        editor_groups = []
        if calendarobj.calendar_editor_group:
            editor_groups = [
                item.strip()
                for item in calendarobj.calendar_editor_group.split(',')
            ]
        if len(editor_groups) == 0:
            return True
        return bool(
            set(flask.g.fas_user.groups).intersection(set(editor_groups)))


def is_meeting_manager(meeting):
    """ Return whether the user is one of the manager of the specified
    meeting (object).
    """
    if not authenticated():
        return False
    else:
        return flask.g.fas_user.username in meeting.meeting_manager


def get_timezone():
    """ Return the user's timezone, default to UTC. """
    tzone = 'UTC'
    if authenticated():
        if flask.g.fas_user['timezone']:
            tzone = flask.g.fas_user['timezone']
    tzone = flask.request.args.get('tzone', tzone)
    return tzone


def chunks(item_list, chunks_size):
    """ Yield successive n-sized chunks from item_list.
    """
    for i in xrange(0, len(item_list), chunks_size):
        yield item_list[i: i + chunks_size]


def is_safe_url(target):
    """ Checks that the target url is safe and sending to the current
    website not some other malicious one.
    """
    ref_url = urlparse.urlparse(flask.request.host_url)
    test_url = urlparse.urlparse(
        urlparse.urljoin(flask.request.host_url, target))
    return test_url.scheme in ('http', 'https') and \
        ref_url.netloc == test_url.netloc


def validate_input_file(input_file):
    ''' Validate the submitted input file.

    This validation has four layers:
      - extension of the file provided
      - MIMETYPE of the file provided

    :arg input_file: a File object of the candidate submitted/uploaded and
        for which we want to check that it compliants with our expectations.
    '''

    extension = os.path.splitext(
        secure_filename(input_file.filename))[1][1:].lower()
    if extension not in APP.config.get('ALLOWED_EXTENSIONS', []):
        raise FedocalException(
            'The submitted candidate has the file extension "%s" which is '
            'not an allowed format' % extension)

    mimetype = input_file.mimetype.lower()
    if mimetype not in APP.config.get(
            'ALLOWED_MIMETYPES', []):  # pragma: no cover
        raise FedocalException(
            'The submitted candidate has the MIME type "%s" which is '
            'not an allowed MIME type' % mimetype)


## Flask application
@APP.route('/')
def index():
    """ Displays the index page presenting all the calendars available.
    """
    calendars_enabled = Calendar.by_status(SESSION, 'Enabled')
    calendars_disabled = Calendar.by_status(SESSION, 'Disabled')
    return flask.render_template(
        'index.html',
        calendars=calendars_enabled,
        calendars_table=chunks(calendars_enabled, 3),
        calendars_table2=chunks(calendars_disabled, 3))


# pylint: disable=R0914
@APP.route('/<calendar_name>/')
@APP.route('/<calendar_name>/<int:year>/')
@APP.route('/<calendar_name>/<int:year>/<int:month>/')
@APP.route('/<calendar_name>/<int:year>/<int:month>/<int:day>/')
def calendar(calendar_name, year=None, month=None, day=None, mid=None):
    """ Display the week of a specific date for a specified calendar.

    :arg calendar_name: the name of the calendar that one would like to
        consult.
    :arg year: the year of the date one would like to consult.
    :arg month: the month of the date one would like to consult.
    :arg day: the day of the date one would like to consult.
    """
    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if not calendarobj:
        flask.flash(
            'No calendar named %s could not be found' % calendar_name,
            'errors')
        return flask.redirect(flask.url_for('index'))

    week_start = fedocallib.get_start_week(year, month, day)
    weekdays = fedocallib.get_week_days(year, month, day)
    week = fedocallib.get_week(SESSION, calendarobj, year, month, day)

    tzone = get_timezone()
    meetings = fedocallib.format_week_meeting(
        week.meetings, tzone, week_start)
    full_day_meetings = fedocallib.format_full_day_meeting(
        week.full_day_meetings, week_start)

    # Information required for the pagination
    next_week = fedocallib.get_next_week(
        week_start.year, week_start.month, week_start.day)
    prev_week = fedocallib.get_previous_week(
        week_start.year, week_start.month, week_start.day)
    month_name = week_start.strftime('%B')

    day_index = None
    today = datetime.date.today()
    if today > week_start and today < week_start + datetime.timedelta(days=7):
        day_index = fedocallib.get_week_day_index(
            today.year, today.month, today.day)

    inyear = year
    if not year:
        inyear = today.year
    inmonth = month
    if not month:
        inmonth = today.month

    busy_days = fedocallib.get_days_of_month_calendar(
        SESSION, calendarobj, year=inyear, month=inmonth,
        tzone=tzone)

    curmonth_cal = fedocallib.get_html_monthly_cal(
        year=year, month=month, day=day, calendar_name=calendar_name,
        busy_days=busy_days)

    return flask.render_template(
        'agenda.html',
        calendar=calendarobj,
        month=month_name,
        weekdays=weekdays,
        day_index=day_index,
        meetings=meetings,
        full_day_meetings=full_day_meetings,
        tzone=tzone,
        tzones=common_timezones,
        next_week=next_week,
        prev_week=prev_week,
        curmonth_cal=curmonth_cal,
        calendar_admin=is_calendar_admin(calendarobj))


@APP.route('/list/<calendar_name>/')
@APP.route('/list/<calendar_name>/<int:year>/')
@APP.route('/list/<calendar_name>/<int:year>/<int:month>/')
@APP.route('/list/<calendar_name>/<int:year>/<int:month>/<int:day>/')
def calendar_list(calendar_name, year=None, month=None, day=None):
    """ Display in a list form all the meetings of a given calendar.
    By default it displays all the meetings of the current year but this
    can be more restricted to a month or even a day.

    :arg calendar_name: the name of the calendar that one would like to
        consult.
    :arg year: the year of the date one would like to consult.
    :arg month: the month of the date one would like to consult.
    :arg day: the day of the date one would like to consult.
    """
    subject = flask.request.args.get('subject', None)
    delta = flask.request.args.get('delta', None)
    end = flask.request.args.get('end', None)

    if delta:
        try:
            delta = int(delta)
        except:
            delta = None
    if end:
        try:
            end = parser.parse(end).date()
        except:
            end = None

    today = datetime.date.today()
    inyear = year
    if not year:
        inyear = today.year
    inmonth = month
    if not month:
        inmonth = 1
    inday = day
    if not day:
        inday = 1
    start_date = datetime.date(inyear, inmonth, inday)

    if end:
        end_date = end
    elif delta:
        end_date = start_date + relativedelta(days=+delta)
    elif not month and not day:
        end_date = start_date \
            + relativedelta(years=+1) \
            - datetime.timedelta(days=1)
    elif not day:
        end_date = start_date \
            + relativedelta(months=+1) \
            - datetime.timedelta(days=1)
    else:
        end_date = start_date + relativedelta(days=+1)

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if not calendarobj:
        flask.flash(
            'No calendar named %s could not be found' % calendar_name,
            'errors')
        return flask.redirect(flask.url_for('index'))

    tzone = get_timezone()
    meetings = fedocallib.get_by_date(
        SESSION, calendarobj, start_date, end_date, tzone,
        name=subject)

    month_name = datetime.date.today().strftime('%B')

    week_start = fedocallib.get_start_week(year, month, day)
    weekdays = fedocallib.get_week_days(year, month, day)
    next_week = fedocallib.get_next_week(
        week_start.year, week_start.month, week_start.day)
    prev_week = fedocallib.get_previous_week(
        week_start.year, week_start.month, week_start.day)

    inmonth = month
    if not month:
        inmonth = today.month

    busy_days = fedocallib.get_days_of_month_calendar(
        SESSION, calendarobj, year=inyear, month=inmonth,
        tzone=tzone)

    curmonth_cal = fedocallib.get_html_monthly_cal(
        year=year, month=month, day=day, calendar_name=calendar_name,
        busy_days=busy_days)

    return flask.render_template(
        'meeting_list.html',
        calendar=calendarobj,
        month=month_name,
        meetings=meetings,
        tzone=tzone,
        year=inyear,
        week_start=week_start,
        weekdays=weekdays,
        next_week=next_week,
        prev_week=prev_week,
        curmonth_cal=curmonth_cal,
        calendar_admin=is_calendar_admin(calendarobj),
        today=datetime.date.today())


@APP.route('/ical/')
def ical_all():
    """ Returns a iCal feed of all calendars from today - 1 month to
    today + 6 month.
    """
    startd = datetime.date.today() - datetime.timedelta(days=30)
    endd = datetime.date.today() + datetime.timedelta(days=180)
    ical = vobject.iCalendar()
    meetings = []
    for calendarobj in Calendar.get_all(SESSION):
        meetings.extend(fedocallib.get_by_date(
            SESSION, calendarobj, startd, endd, extended=False))
    fedocallib.add_meetings_to_vcal(ical, meetings)
    headers = {}
    filename = secure_filename('all_calendars-%s.ical' % (
        datetime.datetime.utcnow().strftime('%Y-%m-%d %Hh%M'))
    )
    headers["Content-Disposition"] = "attachment; filename=%s" % filename
    return flask.Response(
        ical.serialize(),
        mimetype='text/calendar',
        headers=headers)


@APP.route('/ical/<calendar_name>/')
def ical_out(calendar_name):
    """ Returns a iCal feed of the calendar from today - 1 month to
    today + 6 month.

    :arg calendar_name: the name of the calendar for which one would
        like to get the iCal feed.
    """
    startd = datetime.date.today() - datetime.timedelta(days=30)
    endd = datetime.date.today() + datetime.timedelta(days=180)
    calendarobj = Calendar.by_id(SESSION, calendar_name)

    if not calendarobj:
        return flask.abort(404)

    meetings = fedocallib.get_by_date(
        SESSION, calendarobj, startd, endd, extended=False, tzone=False)
    ical = vobject.iCalendar()
    fedocallib.add_meetings_to_vcal(ical, meetings)
    headers = {}
    filename = secure_filename('%s-%s.ical' % (
        calendar_name,
        datetime.datetime.utcnow().strftime('%Y-%m-%d %Hh%M'))
    )
    headers["Content-Disposition"] = "attachment; filename=%s" % filename
    output = ical.serialize()
    output = output.replace('TZID:', 'TZID:fedocal_')
    output = output.replace('TZID=', 'TZID=fedocal_')
    return flask.Response(
        output,
        mimetype='text/calendar',
        headers=headers)


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
    return flask.render_template(
        'my_meeting.html',
        title='My meeting', regular_meetings=regular_meetings,
        single_meetings=single_meetings, pas_meetings=past_meetings,
        tzone=tzone)


@APP.route('/login/', methods=('GET', 'POST'))
def auth_login():
    """ Method to log into the application using FAS OpenID. """

    return_point = flask.url_for('index')
    if 'next' in flask.request.args:
        if is_safe_url(flask.request.args['next']):
            return_point = flask.request.args['next']

    if authenticated():
        return flask.redirect(return_point)

    groups = set()
    for calendar in fedocallib.get_calendars(SESSION):
        groups.update(calendar.admin_groups)
        groups.update(calendar.editor_groups)

    if isinstance(APP.config['ADMIN_GROUP'], basestring):
        groups.update([APP.config['ADMIN_GROUP']])
    else:
        groups.update(APP.config['ADMIN_GROUP'])

    return FAS.login(return_url=return_point, groups=groups)


@APP.route('/logout/')
def auth_logout():
    """ Method to log out from the application. """
    if not authenticated():
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
    if not authenticated():  # pragma: no cover
        return flask.redirect(flask.url_for('index'))
    if not is_admin():
        flask.flash('You are not a fedocal admin, you are not allowed '
                    'to add calendars.', 'errors')
        return flask.redirect(flask.url_for('index'))

    status = fedocallib.get_calendar_statuses(SESSION)

    form = forms.AddCalendarForm(status=status)
    # pylint: disable=E1101
    if form.validate_on_submit():
        calendarobj = Calendar(
            calendar_name=form.calendar_name.data,
            calendar_contact=form.calendar_contact.data,
            calendar_description=form.calendar_description.data,
            calendar_editor_group=form.calendar_editor_groups.data,
            calendar_admin_group=form.calendar_admin_groups.data,
            calendar_status=form.calendar_status.data
        )
        try:
            calendarobj.save(SESSION)
            SESSION.commit()
        except SQLAlchemyError, err:
            SESSION.rollback()
            LOG.debug('Error in add_calendar')
            LOG.exception(err)
            flask.flash('Could not add this calendar to the database',
                        'errors')
            return flask.render_template('add_calendar.html',
                                         form=form)

        flask.flash('Calendar added')
        fedmsg.publish(topic="calendar.new", msg=dict(
            agent=flask.g.fas_user.username,
            calendar=calendarobj.to_json(),
        ))
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
    if not authenticated():  # pragma: no cover
        return flask.redirect(flask.url_for('index'))

    calendarobj = Calendar.by_id(SESSION, calendar_name)

    if not calendarobj:
        flask.flash(
            'No calendar named %s could not be found' % calendar_name,
            'errors')
        return flask.redirect(flask.url_for('index'))

    calendars = Calendar.get_all(SESSION)

    if calendarobj.calendar_status != 'Enabled':
        flask.flash('This calendar is "%s", you are not allowed to add '
                    'meetings anymore.' % calendarobj.calendar_status,
                    'errors')
        return flask.redirect(flask.url_for('calendar',
                              calendar_name=calendar_name))

    if not is_calendar_manager(calendarobj):
        flask.flash('You are not one of the editors of this calendar, '
                    'or one of its admins, you are not allowed to add '
                    'new meetings.', 'errors')
        return flask.redirect(flask.url_for('calendar',
                                            calendar_name=calendar_name))

    tzone = get_timezone()
    form = forms.AddMeetingForm(calendars=calendars)
    form.calendar_name.data = calendar_name
    calendarobj = Calendar.by_id(SESSION, calendar_name)
    # pylint: disable=E1101
    if form.validate_on_submit():
        tzone = form.meeting_timezone.data or tzone
        try:
            information = form.information.data
            # If a wiki_link is specified add it at the end of the
            # description
            if form.wiki_link.data.strip():
                wiki_link = form.wiki_link.data.strip()
                if wiki_link not in information:
                    information += '\n\nMore information available at:'\
                        '\n[%s](%s)' % (wiki_link, wiki_link)
            meeting = fedocallib.add_meeting(
                session=SESSION,
                calendarobj=calendarobj,
                fas_user=flask.g.fas_user,
                meeting_name=form.meeting_name.data,
                meeting_date=form.meeting_date.data,
                meeting_date_end=form.meeting_date_end.data,
                meeting_time_start=form.meeting_time_start.data,
                meeting_time_stop=form.meeting_time_stop.data,
                comanager=form.comanager.data,
                meeting_information=information,
                meeting_location=form.meeting_location.data,
                tzone=tzone,
                frequency=form.frequency.data,
                end_repeats=form.end_repeats.data,
                remind_when=form.remind_when.data,
                reminder_from=form.reminder_from.data,
                remind_who=form.remind_who.data,
                full_day=form.full_day.data,
                admin=is_admin())
        except FedocalException, err:
            flask.flash(err, 'warnings')
            return flask.render_template(
                'add_meeting.html', calendar=calendarobj, form=form,
                tzone=tzone)
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            LOG.debug('Error in add_meeting')
            LOG.exception(err)
            flask.flash('Could not add this meeting to this calendar',
                        'errors')
            return flask.render_template(
                'add_meeting.html', calendar=calendarobj, form=form,
                tzone=tzone)

        flask.flash('Meeting added')
        fedmsg.publish(topic="meeting.new", msg=dict(
            agent=flask.g.fas_user.username,
            meeting=meeting.to_json(),
            calendar=calendarobj.to_json(),
        ))
        return flask.redirect(flask.url_for(
            'calendar', calendar_name=calendarobj.calendar_name,
            year=form.meeting_date.data.year,
            month=form.meeting_date.data.month,
            day=form.meeting_date.data.day))
    elif flask.request.method == 'GET':
        form = forms.AddMeetingForm(timezone=tzone, calendars=calendars)

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
    if not authenticated():  # pragma: no cover
        return flask.redirect(flask.url_for('index'))
    meeting = Meeting.by_id(SESSION, meeting_id)
    if not meeting:
        flask.flash(
            'The meeting #%s could not be found' % meeting_id, 'errors')
        return flask.redirect(flask.url_for('index'))

    calendarobj = Calendar.by_id(SESSION, meeting.calendar_name)

    if calendarobj.calendar_status != 'Enabled':
        flask.flash('This calendar is "%s", you are not allowed to edit its '
                    'meetings anymore.' % calendarobj.calendar_status,
                    'errors')
        return flask.redirect(flask.url_for('calendar',
                              calendar_name=calendarobj.calendar_name))

    if not (is_meeting_manager(meeting)
            or is_calendar_admin(calendarobj)):
        flask.flash('You are not one of the manager of this meeting, '
                    'or an admin, you are not allowed to edit it.',
                    'errors')
        return flask.redirect(flask.url_for('view_meeting',
                                            meeting_id=meeting_id))

    calendars = Calendar.get_all(SESSION)

    tzone = get_timezone()
    form = forms.AddMeetingForm(calendars=calendars)
    # pylint: disable=E1101
    if form.validate_on_submit():
        if meeting.calendar_name != form.calendar_name.data:
            calendarobj = Calendar.by_id(SESSION, form.calendar_name.data)
            if calendarobj.calendar_status != 'Enabled':
                flask.flash('This calendar is "%s", you are not allowed to '
                            'add meetings to it anymore.' %
                            calendarobj.calendar_status, 'errors')
                return flask.redirect(
                    flask.url_for('calendar',
                                  calendar_name=calendarobj.calendar_name)
                )
        tzone = form.meeting_timezone.data or tzone
        action = flask.request.form.get('action', 'Edit')
        try:
            fedocallib.edit_meeting(
                session=SESSION,
                meeting=meeting,
                calendarobj=calendarobj,
                fas_user=flask.g.fas_user,
                meeting_name=form.meeting_name.data,
                meeting_date=form.meeting_date.data,
                meeting_date_end=form.meeting_date_end.data,
                meeting_time_start=form.meeting_time_start.data,
                meeting_time_stop=form.meeting_time_stop.data,
                comanager=form.comanager.data,
                meeting_information=form.information.data,
                meeting_location=form.meeting_location.data,
                tzone=tzone,
                recursion_frequency=form.frequency.data,
                recursion_ends=form.end_repeats.data,
                remind_when=form.remind_when.data,
                reminder_from=form.reminder_from.data,
                remind_who=form.remind_who.data,
                full_day=form.full_day.data,
                edit_all_meeting=action == 'Edit all',
                admin=is_admin())
        except FedocalException, err:
            flask.flash(err, 'warnings')
            return flask.render_template(
                'edit_meeting.html', meeting=meeting, calendar=calendarobj,
                form=form, tzone=tzone)
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            LOG.debug('Error in edit_meeting')
            LOG.exception(err)
            flask.flash('Could not update this meeting.', 'errors')
            return flask.render_template(
                'edit_meeting.html', meeting=meeting,
                calendar=calendarobj, form=form, tzone=tzone)

        flask.flash('Meeting updated')
        fedmsg.publish(topic="meeting.update", msg=dict(
            agent=flask.g.fas_user.username,
            meeting=meeting.to_json(),
            calendar=calendarobj.to_json(),
        ))
        return flask.redirect(flask.url_for('view_meeting',
                              meeting_id=meeting_id))
    elif flask.request.method == 'GET':
        from_date = flask.request.args.get('from_date', None)
        date_limit = None
        if from_date:
            try:
                date_limit = parser.parse(
                    from_date).date() + datetime.timedelta(days=6)
            except:
                pass

        meeting = fedocallib.update_date_rec_meeting(
            meeting, action='next', date_limit=date_limit)

        form = forms.AddMeetingForm(
            meeting=meeting, timezone=tzone, calendars=calendars)
    return flask.render_template(
        'edit_meeting.html', meeting=meeting, calendar=calendarobj,
        form=form, tzone=tzone, meeting_id=meeting_id)


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
    from_date = flask.request.args.get('from_date', None)
    org_meeting = meeting = Meeting.by_id(SESSION, meeting_id)
    tzone = get_timezone()
    if not meeting:
        flask.flash('No meeting could be found for this identifier',
                    'errors')
        return flask.redirect(flask.url_for('index'))

    meeting = fedocallib.convert_meeting_timezone(
        meeting, meeting.meeting_timezone, tzone)

    meeting_utc = fedocallib.convert_meeting_timezone(
        org_meeting, org_meeting.meeting_timezone, 'UTC')

    editor = False
    if is_meeting_manager(meeting) or is_calendar_admin(
            meeting.calendar):
        editor = True

    date_limit = None
    if from_date:
        try:
            date_limit = parser.parse(from_date).date()
        except:
            pass

    next_meeting = fedocallib.update_date_rec_meeting(
        meeting_utc, action='next', date_limit=date_limit)

    return flask.render_template(
        'view_meeting.html',
        full=full,
        meeting=meeting,
        meeting_utc=meeting_utc,
        next_meeting=next_meeting,
        org_meeting=org_meeting,
        tzone=tzone,
        title=meeting.meeting_name,
        editor=editor,
        from_date=from_date)


@APP.route('/meeting/delete/<int:meeting_id>/', methods=('GET', 'POST'))
@cla_plus_one_required
def delete_meeting(meeting_id):
    """ Delete a specific meeting given its identifier.

    :arg meeting_id: the identifier of the meeting to delete.
    """
    if not authenticated():  # pragma: no cover
        return flask.redirect(flask.url_for('index'))
    meeting = Meeting.by_id(SESSION, meeting_id)

    if not meeting:
        flask.flash(
            'No meeting with this identifier could be found.', 'errors')
        return flask.redirect(flask.url_for('index'))

    if meeting.calendar.calendar_status != 'Enabled':
        flask.flash('This calendar is "%s", you are not allowed to delete '
                    'its meetings anymore.' % (
                        meeting.calendar.calendar_status),
                    'errors')
        return flask.redirect(
            flask.url_for('calendar',
                          calendar_name=meeting.calendar.calendar_name)
        )

    if not (is_meeting_manager(meeting)
            or is_calendar_admin(meeting.calendar)):
        flask.flash('You are not one of the manager of this meeting, '
                    'or an admin, you are not allowed to delete it.',
                    'errors')
        return flask.redirect(flask.url_for('view_meeting',
                                            meeting_id=meeting_id))

    calendars = Calendar.get_all(SESSION)
    deleteform = forms.DeleteMeetingForm()

    from_date = flask.request.args.get('from_date', None)
    if from_date:
        try:
            deleteform.from_date.data = parser.parse(from_date).date()
        except:
            pass
    # pylint: disable=E1101
    if deleteform.validate_on_submit():

        if deleteform.confirm_delete.data:

            if meeting.recursion_frequency:
                fedocallib.delete_recursive_meeting(
                    session=SESSION,
                    meeting=meeting,
                    del_date=deleteform.from_date.data,
                    all_meetings=deleteform.confirm_futher_delete.data)
            else:
                meeting.delete(SESSION)

            try:
                SESSION.commit()
                fedmsg.publish(topic="meeting.delete", msg=dict(
                    agent=flask.g.fas_user.username,
                    meeting=meeting.to_json(),
                    calendar=meeting.calendar.to_json(),
                ))
                flask.flash('Meeting deleted')
            except SQLAlchemyError, err:  # pragma: no cover
                SESSION.rollback()
                LOG.debug('Error in delete_meeting - 2')
                LOG.exception(err)
                flask.flash('Could not delete this meeting.', 'error')

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
    if not is_admin():
        flask.flash('You are not a fedocal admin, you are not allowed '
                    'to delete the calendar.', 'errors')
        return flask.redirect(flask.url_for('index'))

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if not calendarobj:
        flask.flash(
            'No calendar named %s could not be found' % calendar_name,
            'errors')
        return flask.redirect(flask.url_for('index'))
    deleteform = forms.DeleteCalendarForm()
    # pylint: disable=E1101
    if deleteform.validate_on_submit():
        if deleteform.confirm_delete.data:
            for meeting in calendarobj.meetings:
                meeting.delete(SESSION)
            calendarobj.delete(SESSION)
            try:
                SESSION.commit()
                flask.flash('Calendar deleted')
                fedmsg.publish(topic="calendar.delete", msg=dict(
                    agent=flask.g.fas_user.username,
                    calendar=calendarobj.to_json(),
                ))
            except SQLAlchemyError, err:  # pragma: no cover
                SESSION.rollback()
                LOG.debug('Error in delete_calendar')
                LOG.exception(err)
                flask.flash('Could not delete this calendar.', 'errors')
        return flask.redirect(flask.url_for('index'))
    return flask.render_template(
        'delete_calendar.html', form=deleteform, calendarobj=calendarobj)


@APP.route('/calendar/clear/<calendar_name>/', methods=('GET', 'POST'))
def clear_calendar(calendar_name):
    """ Clear the specified calendar from all its meetings.

    :arg calendar_name: the identifier of the calendar to delete.
    """
    if not authenticated():  # pragma: no cover
        return flask.redirect(flask.url_for('index'))

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if not calendarobj:
        flask.flash(
            'No calendar named %s could not be found' % calendar_name,
            'errors')
        return flask.redirect(flask.url_for('index'))

    if not is_calendar_admin(calendarobj):
        flask.flash('You are not an admin of this calendar, you are not '
                    'allowed to clear the calendar.', 'errors')
        return flask.redirect(flask.url_for('index'))

    clearform = forms.ClearCalendarForm()
    # pylint: disable=E1101
    if clearform.validate_on_submit():
        if clearform.confirm_delete.data:
            try:
                fedocallib.clear_calendar(SESSION, calendarobj)
                SESSION.commit()
                flask.flash('Calendar cleared')
            except SQLAlchemyError, err:  # pragma: no cover
                SESSION.rollback()
                LOG.debug('Error in clear_calendar')
                LOG.exception(err)
                flask.flash('Could not clear this calendar.', 'errors')
        fedmsg.publish(topic="calendar.clear", msg=dict(
            agent=flask.g.fas_user.username,
            calendar=calendarobj.to_json(),
        ))
        return flask.redirect(flask.url_for('index'))
    return flask.render_template(
        'clear_calendar.html', form=clearform, calendarobj=calendarobj)


# pylint: disable=R0915,R0912,R0911
# CLA + 1
@APP.route('/calendar/edit/<calendar_name>/', methods=('GET', 'POST'))
@cla_plus_one_required
def edit_calendar(calendar_name):
    """ Edit a specific calendar based on the calendar identifier.

    :arg calendar_name: the identifier of the calendar to edit.
    """
    if not authenticated():  # pragma: no cover
        return flask.redirect(flask.url_for('index'))
    if not is_admin():
        flask.flash('You are not a fedocal admin, you are not allowed '
                    'to edit the calendar.', 'errors')
        return flask.redirect(flask.url_for('index'))

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if not calendarobj:
        flask.flash(
            'No calendar named %s could not be found' % calendar_name,
            'errors')
        return flask.redirect(flask.url_for('index'))

    status = fedocallib.get_calendar_statuses(SESSION)
    form = forms.AddCalendarForm(status=status)
    # pylint: disable=E1101
    if form.validate_on_submit():
        try:
            calendarobj.calendar_name = form.calendar_name.data
            calendarobj.calendar_contact = form.calendar_contact.data
            calendarobj.calendar_description = form.calendar_description.data
            calendarobj.calendar_editor_group = \
                form.calendar_editor_groups.data
            calendarobj.calendar_admin_group = \
                form.calendar_admin_groups.data
            calendarobj.calendar_status = form.calendar_status.data
            calendarobj.save(SESSION)
            SESSION.commit()
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            LOG.debug('Error in edit_calendar')
            LOG.exception(err)
            flask.flash('Could not update this calendar.', 'errors')
            return flask.render_template(
                'edit_calendar.html', form=form, calendar=calendarobj)

        flask.flash('Calendar updated')
        fedmsg.publish(topic="calendar.update", msg=dict(
            agent=flask.g.fas_user.username,
            calendar=calendarobj.to_json(),
        ))
        return flask.redirect(flask.url_for(
            'calendar', calendar_name=calendarobj.calendar_name))
    elif flask.request.method == 'GET':
        form = forms.AddCalendarForm(calendar=calendarobj, status=status)
    return flask.render_template('edit_calendar.html', form=form,
                                 calendar=calendarobj)


@APP.route('/markdown/', methods=['POST'])
@cla_plus_one_required
def markdown_preview():
    """ Return the provided markdown text in html.

    The text has to be provided via the parameter 'content' of a POST query.
    """
    return flask.render_template(
        'markdown.html', content=flask.request.form['content'])


@APP.route('/admin/')
def admin():
    """ Displays the index page for the admin section.
    """
    if not authenticated():
        return flask.redirect(flask.url_for('index'))
    if not is_admin():
        flask.flash('You are not a fedocal admin, you are not allowed '
                    'to access the admin part.', 'errors')
        return flask.redirect(flask.url_for('index'))

    calendar_name = flask.request.args.get('calendar', None)
    action = flask.request.args.get('action', None)
    if calendar_name and action and action in ['edit', 'delete']:
        if action == 'edit':
            return flask.redirect(
                flask.url_for(
                    'edit_calendar', calendar_name=calendar_name))
        elif action == 'delete':
            return flask.redirect(
                flask.url_for(
                    'delete_calendar', calendar_name=calendar_name))
    return flask.render_template('admin.html')


@APP.route('/goto/')
def goto():
    """ Redirect the user to the begining of the requested Month of the
    specified year.
    """
    calendar_name = flask.request.args.get('calendar', None)
    view_type = flask.request.args.get('type', 'calendar')
    year = flask.request.args.get('year', None)
    month = flask.request.args.get('month', None)
    day = flask.request.args.get('day', None)

    if not calendar_name:
        flask.flash('No calendar specified', 'errors')
        return flask.redirect(flask.url_for('index'))

    now = datetime.datetime.utcnow()
    if not year:
        year = now.year

    try:
        if day:
            day = int(day)
        if month:
            month = int(month)
        if year:
            year = int(year)
        if year and month and day:
            datetime.date(year, month, day)
    except ValueError:
        flask.flash('Invalid date specified', 'errors')
        year = month = day = None

    if year and year < 1900:
        year = month = day = None
        flask.flash('Dates before 1900 are not allowed', 'warnings')

    if view_type not in ['calendar', 'list']:
        view_type = 'calendar'

    function = 'calendar'
    if view_type == 'list':
        function = 'calendar_list'

    if year and month and day:
        url = flask.redirect(
            flask.url_for(function, calendar_name=calendar_name,
                          year=year, month=month, day=day))
    elif year and month:
        url = flask.redirect(
            flask.url_for(function, calendar_name=calendar_name,
                          year=year, month=month))
    else:
        url = flask.redirect(
            flask.url_for(function, calendar_name=calendar_name,
                          year=year))
    return url


@APP.route('/search/')
@APP.route('/search/<keyword>')
def search(keyword=None):
    """ Returns the list of meeting matching the provided keyword.
    """
    keyword = keyword or flask.request.args.get('keyword', None)
    if not keyword:
        flask.flash('No keyword provided for the search', 'errors')
        return flask.redirect(flask.url_for('index'))

    if '*' not in keyword:
        keyword += '*'

    meetings = fedocallib.search_meetings(SESSION, keyword)

    tzone = get_timezone()

    curmonth_cal = fedocallib.get_html_monthly_cal()
    return flask.render_template(
        'meeting_list.html',
        meetings=meetings,
        tzone=tzone,
        curmonth_cal=curmonth_cal,
        keyword=keyword,
        today=datetime.date.today())


@APP.route('/locations/')
def locations():
    """ Returns the list of all locations where meetings happen and thus
    enable to see calendar for a specific location.
    """
    list_locations = fedocallib.get_locations(SESSION)
    return flask.render_template(
        'locations.html',
        locations=chunks(list_locations, 3))


# pylint: disable=R0914
@APP.route('/location/<loc_name>/',
           defaults={'year': None, 'month': None, 'day': None})
@APP.route('/location/<loc_name>/<int:year>/',
           defaults={'month': None, 'day': None})
@APP.route('/location/<loc_name>/<int:year>/<int:month>/',
           defaults={'day': None})
@APP.route('/location/<loc_name>/<int:year>/<int:month>/<int:day>/')
def location(loc_name, year, month, day):
    """ Display the week of a specific date for a specified location.

    :arg calendar_name: the name of the calendar that one would like to
        consult.
    :arg year: the year of the date one would like to consult.
    :arg month: the month of the date one would like to consult.
    :arg day: the day of the date one would like to consult.
    """
    list_locations = fedocallib.get_locations(SESSION)
    if loc_name not in list_locations:
        flask.flash(
            'No location named %s could not be found' % loc_name,
            'errors')
        return flask.redirect(flask.url_for('locations'))

    week_start = fedocallib.get_start_week(year, month, day)
    weekdays = fedocallib.get_week_days(year, month, day)
    week = fedocallib.get_week_of_location(
        SESSION, loc_name, year, month, day)

    tzone = get_timezone()
    meetings = fedocallib.format_week_meeting(
        week.meetings, tzone, week_start)
    full_day_meetings = fedocallib.format_full_day_meeting(
        week.full_day_meetings, week_start)

    next_week = fedocallib.get_next_week(
        week_start.year, week_start.month, week_start.day)
    prev_week = fedocallib.get_previous_week(
        week_start.year, week_start.month, week_start.day)
    month_name = week_start.strftime('%B')

    day_index = None
    today = datetime.date.today()
    if today > week_start and today < week_start + datetime.timedelta(days=7):
        day_index = fedocallib.get_week_day_index(
            today.year, today.month, today.day)

    inyear = year
    if not year:
        inyear = datetime.date.today().year
    inmonth = month
    if not month:
        inmonth = datetime.date.today().month

    busy_days = fedocallib.get_days_of_month_location(
        SESSION, loc_name, year=inyear, month=inmonth,
        tzone=tzone)

    curmonth_cal = fedocallib.get_html_monthly_cal(
        year=year, month=month, day=day, loc_name=loc_name,
        busy_days=busy_days)

    return flask.render_template(
        'agenda.html',
        location=loc_name,
        month=month_name,
        weekdays=weekdays,
        day_index=day_index,
        meetings=meetings,
        full_day_meetings=full_day_meetings,
        tzone=tzone,
        tzones=common_timezones,
        next_week=next_week,
        prev_week=prev_week,
        curmonth_cal=curmonth_cal)


# pylint: disable=R0914
@APP.route('/location/list/<loc_name>/',
           defaults={'year': None, 'month': None, 'day': None})
@APP.route('/location/list/<loc_name>/<int:year>/',
           defaults={'month': None, 'day': None})
@APP.route('/location/list/<loc_name>/<int:year>/<int:month>/',
           defaults={'day': None})
@APP.route('/location/list/<loc_name>/<int:year>/<int:month>/<int:day>/')
def location_list(loc_name, year, month, day):
    """ Display the list of meetings for a specified location.

    :arg calendar_name: the name of the calendar that one would like to
        consult.
    :arg year: the year of the date one would like to consult.
    :arg month: the month of the date one would like to consult.
    :arg day: the day of the date one would like to consult.
    """
    """ Display in a list form all the meetings of a given calendar.
    By default it displays all the meetings of the current year but this
    can be more restricted to a month or even a day.

    :arg loc_name: the name of the location that one would like to
        consult.
    :arg year: the year of the date one would like to consult.
    :arg month: the month of the date one would like to consult.
    :arg day: the day of the date one would like to consult.
    """
    list_locations = fedocallib.get_locations(SESSION)
    if loc_name not in list_locations:
        flask.flash(
            'No location named %s could not be found' % loc_name,
            'errors')
        return flask.redirect(flask.url_for('locations'))

    today = datetime.date.today()
    inyear = year
    if not year:
        inyear = today.year
    inmonth = month
    if not month:
        inmonth = 1
    inday = day
    if not day:
        inday = 1
    start_date = datetime.date(inyear, inmonth, inday)
    if not month and not day:
        end_date = start_date \
            + relativedelta(years=+1) \
            - datetime.timedelta(days=1)
    elif not day:
        end_date = start_date \
            + relativedelta(months=+1) \
            - datetime.timedelta(days=1)
    else:
        end_date = start_date + relativedelta(days=+1)

    tzone = get_timezone()
    meetings = fedocallib.get_by_date_at_location(
        SESSION, loc_name, start_date, end_date, tzone)

    month_name = datetime.date.today().strftime('%B')

    week_start = fedocallib.get_start_week(year, month, day)
    weekdays = fedocallib.get_week_days(year, month, day)
    next_week = fedocallib.get_next_week(
        week_start.year, week_start.month, week_start.day)
    prev_week = fedocallib.get_previous_week(
        week_start.year, week_start.month, week_start.day)

    if not month:
        inmonth = today.month

    busy_days = fedocallib.get_days_of_month_location(
        SESSION, loc_name, year=inyear, month=inmonth,
        tzone=tzone)

    curmonth_cal = fedocallib.get_html_monthly_cal(
        year=year, month=month, day=day, loc_name=loc_name,
        busy_days=busy_days)

    return flask.render_template(
        'meeting_list.html',
        calendar=None,
        location=loc_name,
        month=month_name,
        meetings=meetings,
        tzone=tzone,
        year=inyear,
        week_start=week_start,
        weekdays=weekdays,
        next_week=next_week,
        prev_week=prev_week,
        curmonth_cal=curmonth_cal,
        today=datetime.date.today())


@APP.route('/updatetz/')
def update_tz():
    """ Update the timezone using the value set in the drop-down list and
    send back the user to where it came from.
    """
    url = flask.url_for('index')
    if flask.request.referrer:  # pragma: no cover
        urltmp = urllib.unquote(flask.request.referrer.split('?', 1)[0])
        if is_safe_url(urltmp):
            url = urltmp
    else:
        flask.flash('Invalid referred url', 'warnings')

    tzone = flask.request.args.get('tzone', None)
    if tzone:
        return flask.redirect('%s?tzone=%s' % (url, tzone))
    else:
        return flask.redirect(url)


@APP.route('/calendar/upload/<calendar_name>/', methods=('GET', 'POST'))
@cla_plus_one_required
def upload_calendar(calendar_name):
    """ Page used to upload a iCalendar file into a specific calendar.
    """
    if not authenticated():  # pragma: no cover
        return flask.redirect(flask.url_for('index'))

    calendarobj = Calendar.by_id(SESSION, calendar_name)
    if not calendarobj:
        flask.flash(
            'No calendar named %s could not be found' % calendar_name,
            'errors')
        return flask.redirect(flask.url_for('index'))

    if not is_calendar_admin(calendarobj):
        flask.flash('You are not an admin for this calendar, you are not '
                    'allowed to upload a iCalendar file to it.', 'errors')
        return flask.redirect(flask.url_for('index'))

    form = forms.UploadIcsForm()
    # pylint: disable=E1101
    if form.validate_on_submit():
        ical_file = flask.request.files['ics_file']

        try:
            validate_input_file(ical_file)
        except FedocalException as err:
            LOG.debug('ERROR: Uploaded file is invalid - user: "%s" '
                      'file: "%s"',
                      flask.g.fas_user.username, ical_file.filename)
            LOG.exception(err)
            flask.flash(err.message, 'error')
            return flask.render_template(
                'upload_calendar.html', form=form, calendar=calendarobj)

        try:
            fedocallib.add_vcal_file(
                SESSION, calendarobj, ical_file, flask.g.fas_user, is_admin())
            flask.flash('Calendar uploaded')
        except FedocalException as err:  # pragma: no cover
            flask.flash(err.message, 'error')
            return flask.render_template(
                'upload_calendar.html', form=form, calendar=calendarobj)
        except SQLAlchemyError, err:  # pragma: no cover
            SESSION.rollback()
            LOG.debug('Error in upload_calendar')
            LOG.exception(err)
            flask.flash('Could not upload this iCalendar file.', 'errors')
            return flask.render_template(
                'upload_calendar.html', form=form, calendar=calendarobj)

        fedmsg.publish(topic="calendar.upload", msg=dict(
            agent=flask.g.fas_user.username,
            calendar=calendarobj.to_json(),
        ))
        return flask.redirect(flask.url_for(
            'calendar', calendar_name=calendarobj.calendar_name))

    return flask.render_template(
        'upload_calendar.html', form=form, calendar=calendarobj)
