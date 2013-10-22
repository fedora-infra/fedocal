# -*- coding: utf-8 -*-

"""
fedocallib - Back-end library for the fedocal project.

Copyright (C) 2012 Pierre-Yves Chibon
Author: Pierre-Yves Chibon <pingou@pingoured.fr>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.
See http://www.gnu.org/copyleft/gpl.html  for the full text of the
license.
"""

import vobject
import pytz
import operator

from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from week import Week
from model import Calendar, Reminder, Meeting
import dbaction as dbaction
from exceptions import UserNotAllowed, InvalidMeeting

from fedora_calendar import FedocalCalendar


HOURS = ['00', '01', '02', '03', '04', '05', '06', '07', '08', '09',
         '10', '11', '12', '13', '14', '15', '16', '17', '18', '19',
         '20', '21', '22', '23', '24']


def convert_time(timeobj, tzfrom, tzto):
    """ Convert a given datetime object from a specified timezone to
    the other specified.

    :arg timeobj: a datetime object to convert
    :arg tzfrom: the timezone from which to convert
    :arg tzto: the timezone to which to convert
    """
    timez_from = pytz.timezone(tzfrom)
    timez_to = pytz.timezone(tzto)
    timeobj_from = timez_from.localize(timeobj)
    timeobj_to = timeobj_from.astimezone(timez_to)
    return timeobj_to


def convert_meeting_timezone(meeting, tzfrom, tzto):
    """ Convert a given meeting from one specified timezone to another
    specified one.

    :arg meeting: a Meeting object representing the meeting to convert
        from one timezone to the other.
    :arg tzfrom: the timezone from which to convert
    :arg tzto: the timezone to which to convert
    """
    meeting_start = convert_time(
        datetime(
            meeting.meeting_date.year,
            meeting.meeting_date.month,
            meeting.meeting_date.day,
            meeting.meeting_time_start.hour,
            meeting.meeting_time_start.minute),
        tzfrom, tzto)
    meeting_stop = convert_time(
        datetime(
            meeting.meeting_date_end.year,
            meeting.meeting_date_end.month,
            meeting.meeting_date_end.day,
            meeting.meeting_time_stop.hour,
            meeting.meeting_time_stop.minute),
        tzfrom, tzto)
    meeting.meeting_date = meeting_start.date()
    meeting.meeting_date_end = meeting_stop.date()
    meeting.meeting_time_start = meeting_start.time()
    meeting.meeting_time_stop = meeting_stop.time()
    return meeting


def create_session(db_url, debug=False, pool_recycle=3600):
    """ Create the Session object to use to query the database.

    :arg db_url: URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :arg debug: a boolean specifying wether we should have the verbose
        output of sqlalchemy or not.
    :return a Session that can be used to query the database.
    """
    engine = create_engine(db_url, echo=debug, pool_recycle=pool_recycle)
    scopedsession = scoped_session(sessionmaker(bind=engine))
    return scopedsession


def get_calendars(session):
    """ Retrieve the list of Calendar from the database. """
    return Calendar.get_all(session)


def get_start_week(year=None, month=None, day=None):
    """ For a given date, retrieve the day the week started.
    For any missing parameters (ie: None), use the value of the current
    day.

    :kwarg year: year to consider when searching a week.
    :kwarg month: month to consider when searching a week.
    :kwarg day: day to consider when searching a week.
    :return a Date of the day the week started either based on the
        current utc date or based on the information.
    """
    now = datetime.utcnow()
    if not year:
        year = now.year
    if not month:
        month = now.month
    if not day:
        day = now.day
    week_day = date(year, month, day)
    week_start = week_day - timedelta(days=week_day.weekday())
    return week_start


def get_stop_week(year=None, month=None, day=None):
    """ For a given date, retrieve the day the week stops.
    For any missing parameters (ie: None), use the value of the current
    day.

    :kwarg year: year to consider when searching a week.
    :kwarg month: month to consider when searching a week.
    :kwarg day: day to consider when searching a week.
    :return a Date of the day the week started either based on the
        current utc date or based on the information.
    """
    week_start = get_start_week(year, month, day)
    week_stop = week_start + timedelta(days=6)
    return week_stop


def get_next_week(year=None, month=None, day=None):
    """ For a given date, retrieve the day when the next week starts.
    For any missing parameters (ie: None), use the value of the current
    day.

    :kwarg year: year to consider when searching a week.
    :kwarg month: month to consider when searching a week.
    :kwarg day: day to consider when searching a week.
    :return a Date of the day the week started either based on the
        current utc date or based on the information.
    """
    week_start = get_start_week(year, month, day)
    next_week_start = week_start + timedelta(days=7)
    return next_week_start


def get_previous_week(year=None, month=None, day=None):
    """ For a given date, retrieve the day when the previous week starts.
    For any missing parameters (ie: None), use the value of the current
    day.

    :kwarg year: year to consider when searching a week.
    :kwarg month: month to consider when searching a week.
    :kwarg day: day to consider when searching a week.
    :return a Date of the day the week started either based on the
        current utc date or based on the information.
    """
    week_start = get_start_week(year, month, day)
    previous_week_start = week_start - timedelta(days=7)
    return previous_week_start


def get_week(session, calendar, year=None, month=None, day=None):
    """ For a given date, retrieve the corresponding week.
    For any missing parameters (ie: None), use the value of the current
    day.

    :arg session: the database session to use
    :arg calendar: the Calendar object of interest.
    :kwarg year: year to consider when searching a week.
    :kwarg month: month to consider when searching a week.
    :kwarg day: day to consider when searching a week.
    :return a Week object corresponding to the week asked either based
        on the current utc date of based on the information specified.
    """
    week_start = get_start_week(year, month, day)
    week = Week(session, calendar, week_start)
    return week


def get_week_days(year=None, month=None, day=None):
    """ For a given date, retrieve the corresponding week and return the
    list of all the days in the week with their dates.
    For any missing parameters (ie: None), use the value of the current
    day.

    This function provides the 'Day date' string used at the header of
    the agenda table.

    :kwarg year: year to consider when searching a week.
    :kwarg month: month to consider when searching a week.
    :kwarg day: day to consider when searching a week.
    :return a list of 'Day date' string corresponding to the week asked
        either based on the current utc date or based on the information
        specified.
    """
    week_start = get_start_week(year, month, day)
    weekdays = []
    for i in range(0, 7):
        curday = week_start + timedelta(days=i)
        weekdays.append(curday)
    return weekdays


def get_week_day_index(year=None, month=None, day=None):
    """ For a specified date, find the index of this day in the week.

    This function provides the 'Day index' string used to highlight the
    current day in the calendar view.

    :kwarg year: year to consider when searching a week.
    :kwarg month: month to consider when searching a week.
    :kwarg day: day to consider when searching a week.
    :return a list of 'Day date' string corresponding to the week asked
        either based on the current utc date or based on the information
        specified.
    """
    today = date.today()
    if not year:
        year = today.year
    if not month:
        month = today.month
    if not day:
        day = today.day
    return date(year, month, day).isoweekday()


def _format_week_meeting(meetings, meeting_list, tzone, week_start):
    """ Return a dictionnary representing the meeting of the week in the
    appropriate format for the meeting provided in the meeting_list.
    """
    fmt = '%Hh%M'
    #week_start = convert_time(week_start, 'UTC', tzone)
    for meeting in meeting_list:
        start_delta = 0
        if meeting.meeting_time_start.minute < 15:
            start_delta = - meeting.meeting_time_start.minute
        elif 15 <= meeting.meeting_time_start.minute <= 45:
            start_delta = 30 - meeting.meeting_time_start.minute
        elif meeting.meeting_time_start.minute > 45:
            start_delta = 60 - meeting.meeting_time_start.minute

        stop_delta = 0
        if meeting.meeting_time_stop.minute < 15:
            stop_delta = - meeting.meeting_time_stop.minute
        elif 15 <= meeting.meeting_time_stop.minute <= 45:
            stop_delta = 30 - meeting.meeting_time_stop.minute
        elif meeting.meeting_time_stop.minute > 45:
            stop_delta = 60 - meeting.meeting_time_stop.minute

        startdt = datetime(
            meeting.meeting_date.year,
            meeting.meeting_date.month, meeting.meeting_date.day,
            meeting.meeting_time_start.hour,
            meeting.meeting_time_start.minute, 0
        ) + timedelta(minutes=start_delta)
        startdt = convert_time(startdt, 'UTC', tzone)

        stopdt = datetime(
            meeting.meeting_date_end.year,
            meeting.meeting_date_end.month,
            meeting.meeting_date_end.day,
            meeting.meeting_time_stop.hour,
            meeting.meeting_time_stop.minute, 0
        ) + timedelta(minutes=stop_delta)
        stopdt = convert_time(stopdt, 'UTC', tzone)

        if stopdt < startdt:
            stopdt = stopdt + timedelta(days=1)

        t_time = startdt
        while t_time < stopdt:
            if t_time < week_start \
                    or t_time >= (week_start + timedelta(days=7)):
                t_time = t_time + timedelta(minutes=30)
                continue
            day = t_time.weekday()
            key = t_time.strftime(fmt)
            if key in meetings:
                if meetings[key][day]:
                    meetings[key][day].append(meeting)
                else:
                    meetings[key][day] = [meeting]
            t_time = t_time + timedelta(minutes=30)
    return meetings


# pylint: disable=R0913,R0914
def get_meetings(
        session, calendar, year=None, month=None, day=None, tzone='UTC'):
    """ Return a hash of {time: [meeting]} for the asked week. The week
    is returned based either on the current utc week or based on the
    information provided.

    :arg session: the database session to use
    :arg calendar: the name of the calendar of interest.
    :kwarg year: year to consider when searching a week.
    :kwarg month: month to consider when searching a week.
    :kwarg day: day to consider when searching a week.
    :kwarg tzone: the timezone in which the meetings should be displayed
        defaults to UTC.
    """
    week_start = get_start_week(year, month, day)
    week_start = pytz.timezone(tzone).localize(
        datetime(week_start.year, week_start.month, week_start.day, 0, 0,))
    week = get_week(session, calendar, year, month, day)

    # Prepare empty data structure in which we will then insert the meetings
    # This is pretty much the table that will get displayed.
    meetings = {}
    for hour in HOURS[:-1]:
        for key in ['%sh00', '%sh30']:
            key = key % (hour)
            # pylint: disable=W0612
            meetings[key] = [None for cnt2 in range(0, 7)]

    meetings = _format_week_meeting(meetings, week.meetings, tzone,
                                    week_start)
    return meetings


def get_meetings_by_date(session, calendar_name, start_date, end_date):
    """ Return a list of meetings which have or will occur in between
    the two provided dates.

    :arg session: the database session to use
    :arg calendar_name: the name of the calendar of interest.
    :arg start_date: the date from which we would like to retrieve the
        meetings (this day is included in the selection).
    :arg start_date: the date until which we would like to retrieve the
        meetings (this day is excluded from the selection).
    """
    calendar = Calendar.by_id(session, calendar_name)
    return get_by_date(session, calendar, start_date, end_date)


def get_meetings_by_date_and_region(
        session, calendar, start_date, end_date, region):
    """ Return a list of meetings which have or will occur in between
    the two provided dates.

    :arg session: the database session to use
    :arg calendar: the name of the calendar of interest.
    :arg start_date: the date from which we would like to retrieve the
        meetings (this day is included in the selection).
    :arg start_date: the date until which we would like to retrieve the
        meetings (this day is excluded from the selection).
    :arg region: the region in which the meetings should occur.
    """
    calendar = Calendar.by_id(session, calendar)
    return Meeting.get_by_date_and_region(session, calendar, start_date,
                                          end_date, region)


def is_date_in_future(indate, start_time):
    """ Return whether the date is in the future or the past.

    :arg indate: a datetime object of the date to check
        (ie: '2012-09-01')
    :arg start_time: a string of the starting time of the meeting
        (ie: '08')
    """
    today = datetime.utcnow()
    if today.date() > indate:
        return False
    elif today.date() == indate and today.hour > int(start_time.hour):
        return False
    else:
        return True


def get_past_meeting_of_user(
        session, username, tzone='UTC', from_date=date.today()):
    """ Return all past meeting which specified username is among the
    managers.
    :arg session: the database session to use
    :arg username: the FAS user name that you would like to have the
        past meetings for.
    :kwarg tzone: the time-zone to which to convert the meetings.
        Defaults to 'UTC'.
    :kwarg from_date: the date from which the futur meetings should be
        retrieved. Defaults to today
    """
    meetings_tmp = Meeting.expand_regular_meetings(
        Meeting.get_past_meeting_of_user(session, username, from_date),
        end_date=from_date)
    meetings = []
    for meeting in meetings_tmp:
        meetings.append(convert_meeting_timezone(meeting, 'UTC', tzone))
    meetings.sort(key=operator.attrgetter('meeting_date'))
    return meetings


# pylint: disable=C0103
def get_future_single_meeting_of_user(
        session, username, tzone='UTC', from_date=date.today()):
    """ Return all future meeting which specified username is among the
    managers.

    :arg session: the database session to use
    :arg username: the FAS user name that you would like to have the
        past meetings for.
    :kwarg tzone: the time-zone to which to convert the meetings.
        Defaults to 'UTC'.
    :kwarg from_date: the date from which the futur meetings should be
        retrieved. Defaults to today
    """
    meetings_tmp = Meeting.get_future_single_meeting_of_user(
        session, username, from_date)
    meetings = []
    for meeting in meetings_tmp:
        meetings.append(convert_meeting_timezone(meeting, 'UTC', tzone))
    return meetings


# pylint: disable=C0103
def get_future_regular_meeting_of_user(
        session, username, tzone='UTC', from_date=date.today()):
    """ Return all future recursive meeting which specified username is
    among the managers.

    :arg session: the database session to use.
    :arg username: the FAS user name that you would like to have the
        past meetings for.
    :kwarg tzone: the time-zone to which to convert the meetings.
        Defaults to 'UTC'.
    :kwarg from_date: the date from which the futur meetings should be
        retrieved. Defaults to today.
    """
    meetings_tmp = Meeting.get_future_regular_meeting_of_user(
        session, username, from_date)
    meetings = []
    for meeting in meetings_tmp:
        meetings.append(convert_meeting_timezone(meeting, 'UTC', tzone))
    return meetings


def agenda_is_free(
        session, calendarobj,
        meeting_date,
        meeting_date_end):
    """Check if there is already someting planned in this agenda at that
    time on that day.

    :arg session: the database session to use
    :arg calendar: the name of the calendar of interest.
    :arg meeting_date: the date of the meeting (as Datetime object)
    :arg meeting_date_end: the end date of the meeting (as Datetime
        object)
    :arg time_start: the time at which the meeting starts (as int)
    :arg time_stop: the time at which the meeting stops (as int)
    """
    meetings = Meeting.get_overlaping_meetings(
        session, calendarobj,
        meeting_date.date(),
        meeting_date_end.date())
    agenda_free = True

    for meeting in set(meetings):
        meeting_start_date_time = datetime(
            meeting.meeting_date.year,
            meeting.meeting_date.month,
            meeting.meeting_date.day,
            meeting.meeting_time_start.hour,
            meeting.meeting_time_start.minute,
            tzinfo=pytz.utc)

        meeting_stop_date_time = datetime(
            meeting.meeting_date_end.year,
            meeting.meeting_date_end.month,
            meeting.meeting_date_end.day,
            meeting.meeting_time_stop.hour,
            meeting.meeting_time_stop.minute,
            tzinfo=pytz.utc)

        if meeting_date <= meeting_start_date_time \
                and meeting_date_end > meeting_start_date_time:
            agenda_free = False
        elif meeting_date < meeting_stop_date_time \
                and meeting_date_end >= meeting_stop_date_time:
            agenda_free = False
        elif meeting_date < meeting_start_date_time \
                and meeting_date_end > meeting_stop_date_time:
            agenda_free = False
        elif meeting_date > meeting_start_date_time \
                and meeting_date_end < meeting_stop_date_time:
            agenda_free = False
        elif meeting_date == meeting_start_date_time \
                and meeting_date_end == meeting_stop_date_time:
            agenda_free = False

    return agenda_free


def agenda_is_free_in_future(
        session, calendarobj, meeting_date, meeting_date_end,
        recursion_ends,
        time_start, time_stop,
        meeting_id=None):
    """For recursive meeting, check for meetings happening at the
    specified time between the specified date and to the end of the
    recursion.

    :arg session: the database session to use
    :arg calendarobj: the calendar of interest.
    :arg meeting_date: the date of the meeting (as Datetime object)
    :arg meeting_date_end: the end date of the meeting (as Datetime
        object)
    :arg recursion_ends: the end date of the recursion
    :arg time_start: the time at which the meeting starts (as int)
    :arg time_stop: the time at which the meeting stops (as int)
    :kwarg meeting_id: a meeting identifier allowing to check if a
        potentially conflicting meeting isn't in fact a future iteration
        of the current meeting.
    """
    meetings = get_by_date(
        session, calendarobj, meeting_date, recursion_ends)
    agenda_free = True
    for meeting in set(meetings):
        if meeting.meeting_date != meeting_date:
            continue
        if meeting_id and meeting.meeting_id == meeting_id:
            continue
        if time_start <= meeting.meeting_time_start \
                and meeting.meeting_time_start < time_stop:
            agenda_free = False
            break
        elif time_start < meeting.meeting_time_stop \
                and meeting.meeting_time_stop <= time_stop:
            agenda_free = False
            break
        elif time_start < meeting.meeting_time_start \
                and time_stop > meeting.meeting_time_stop:
            agenda_free = False
            break
        elif time_start > meeting.meeting_time_start \
                and time_stop < meeting.meeting_time_stop:
            agenda_free = False
            break
    return agenda_free


def is_user_managing_in_calendar(session, calendar_name, fas_user):
    """ Returns True if the user is in a group set as editor of the
    calendar and False otherwise. It will also return True if there are
    no groups set as editor the calendar.

    :arg session: the database session to use
    :arg calendar_name: the name of the calendar of interest.
    :arg fas_user: a FAS user object with all the info.
    """
    editor_groups = Calendar.get_editor_groups(session, calendar_name)
    admin_groups = Calendar.get_admin_groups(session, calendar_name)
    if not editor_groups:
        return True
    else:
        return len(
            set(editor_groups).intersection(set(fas_user.groups))
        ) >= 1 or len(
            set(admin_groups).intersection(set(fas_user.groups))
        ) >= 1


def delete_recursive_meeting(session, meeting):
    """ Delete from the database any future meetings associated with this
    recursion. For recursive meeting, deletion = set the end date to
    today.

    :arg session: the database session to use.
    :arg meeting: the Meeting object from which are removed all further
        meetings.
    """
    today = date.today()
    if not meeting.recursion_frequency \
            or meeting.recursion_ends < today:
        return
    else:
        meeting.recursion_ends = today
        meeting.save(session)
        session.commit()


# pylint: disable=C0103
def _generate_date_rounded_to_the_hour(meetingdate, offset):
    """ For a given date, return a new date to which the given offset in
    hours has been added and the time rounded to the hour.

    :arg meetingdate: a datetime object to which to add the offset
        (in hours) and to round to the hour.
    :arg offset: an integer representing the number of hour to add to
        the given date.
    """
    delta = timedelta(hours=offset)
    new_date = meetingdate + delta
    new_date = new_date - timedelta(seconds=new_date.second,
                                    microseconds=new_date.microsecond)
    return new_date


def retrieve_meeting_to_remind(session, offset=30):
    """ Retrieve all the meetings for which we have to send a reminder.

    :arg session: the database session to use.
    :kwarg offset: the frequency at which the cron job is ran in order
        to avoid sending twice the same reminder.
    """
    today = datetime.utcnow()
    meetings = []

    for reminder_time in [12, 24, 48, 168]:
    # Retrieve meeting planned in less than X hours
        new_date = _generate_date_rounded_to_the_hour(today,
                                                      reminder_time)
        end_date = new_date + timedelta(minutes=offset)
        meetings.extend(Meeting.get_meeting_with_reminder(
            session, new_date.date(), new_date.time(), end_date.time(),
            'H-%s' % reminder_time))

    return meetings


def add_meeting_to_vcal(ical, meeting):
    """ Convert a Meeting object into iCal object and add it to the
    provided calendar.

    :arg ical: the iCal calendar object to which the meetings should
        be added.
    :arg meeting: a single fedocal.model.Meeting object to convert to
        iCal and add to the provided calendar.
    """
    utc = vobject.icalendar.utc
    entry = ical.add('vevent')
    entry.add('summary').value = meeting.meeting_name
    entry.add('description').value = meeting.meeting_information
    entry.add('organizer').value = meeting.meeting_manager

    start = entry.add('dtstart')
    stop = entry.add('dtend')
    if meeting.full_day:
        start.value = meeting.meeting_date
        stop.value = meeting.meeting_date_end
    else:
        meeting.meeting_time_start = meeting.meeting_time_start.replace(
            tzinfo=utc)
        start.value = datetime.combine(meeting.meeting_date,
                                       meeting.meeting_time_start)
        meeting.meeting_time_stop = meeting.meeting_time_stop.replace(
            tzinfo=utc)
        stop.value = datetime.combine(meeting.meeting_date_end,
                                      meeting.meeting_time_stop)


def add_meetings_to_vcal(ical, meetings):
    """ Convert the Meeting objects into iCal object and add them to
    the provided calendar.

    :arg ical: the iCal calendar object to which the meetings should
        be added.
    :arg meetings: a list of fedocal.model.Meeting object to convert to
        iCal and add to the provided calendar.
    """
    for meeting in meetings:
        add_meeting_to_vcal(ical, meeting)


def get_html_monthly_cal(
        day=None, month=None, year=None, calendar_name=None):
    """ Display a monthly calendar as HTML.

    :kwarg day: optionnal day (as int). Defaults to current day
    :kwarg month: optionnal month (as int). Defaults to current month
    :kwarg year: optionnal year. Defaults to current year.
    :kwarg calendar_name: the name of the calendar to which the links
        should point.
    """
    cur_date = date.today()
    if not year:
        year = cur_date.year

    if not month:
        month = cur_date.month

    if not day:
        day = cur_date.day

    htmlcal = FedocalCalendar(day=day, year=year, month=month,
                              calendar_name=calendar_name)
    curmonth_cal_nf = htmlcal.formatmonth()

    return curmonth_cal_nf


def get_by_date(session, calendarobj, start_date, end_date, tzone='UTC'):
    """ Returns all the meetings in a given time period.
    Recursive meetings are expanded as if each was a single meeting.

    :arg session: the database session to use
    :arg calendarobj: the calendar (object) of interest.
    :arg start_date: a Date object representing the beginning of the
        period
    :arg start_date: a Date object representing the ending of the period
    :kwarg tzone: the timezone in which the meetings should be displayed
        defaults to UTC.
    """
    meetings_utc = Meeting.get_by_date(session, calendarobj, start_date,
                                       end_date, no_recursive=True)
    meetings_utc.extend(Meeting.get_regular_meeting_by_date(session,
                        calendarobj, start_date, end_date))
    meetings = []
    for meeting in list(set(meetings_utc)):
        meetings.append(convert_meeting_timezone(
            meeting, 'UTC', tzone))
    meetings.sort(key=operator.attrgetter('meeting_date'))
    return meetings


# pylint: disable=R0913,R0914
def add_meeting(
        session, calendarobj, fas_user,
        meeting_name, meeting_date, meeting_date_end,
        meeting_time_start, meeting_time_stop, comanager,
        meeting_information,
        meeting_region, tzone,
        frequency, end_repeats,
        remind_when, remind_who,
        full_day,
        admin=False):
    """ When a user wants to add a meeting to the database, we need to
    perform a number of test first checking that the input is valid
    and then add the desired meeting.
    """
    if not is_user_managing_in_calendar(
            session, calendarobj.calendar_name, fas_user) and not admin:
        raise UserNotAllowed(
            'You are not allowed to add a meeting to this calendar')

    if meeting_date_end is None:
        meeting_date_end = meeting_date

    if full_day:
        meeting_time_start = time(0, 0)
        meeting_time_stop = time(0, 0)
        tzone = 'UTC'

    meeting_time_start = convert_time(
        datetime(meeting_date.year, meeting_date.month, meeting_date.day,
                 meeting_time_start.hour,
                 meeting_time_start.minute),
        tzone, 'UTC')
    meeting_time_stop = convert_time(
        datetime(meeting_date_end.year,
                 meeting_date_end.month,
                 meeting_date_end.day,
                 meeting_time_stop.hour,
                 meeting_time_stop.minute),
        tzone, 'UTC')

    if not is_date_in_future(meeting_date, meeting_time_start):
        raise InvalidMeeting('The date you entered is in the past')

    if meeting_time_start.date() > meeting_time_stop.date():
        raise InvalidMeeting(
            'The start date of your meeting is later than the stop date.')

    if meeting_time_start > meeting_time_stop:
        raise InvalidMeeting(
            'The start time of your meeting is later than the stop time.')

    if full_day:
        meeting_time_stop = meeting_time_stop + timedelta(days=1)

    free_time = agenda_is_free(
        session, calendarobj,
        meeting_time_start,
        meeting_time_stop)

    if not bool(calendarobj.calendar_multiple_meetings) and \
            not bool(free_time):
        raise InvalidMeeting(
            'The start or end time you have entered is already occupied.')

    if frequency and end_repeats:
        futur_meeting_at_time = agenda_is_free_in_future(
            session, calendarobj,
            meeting_time_start.date(), meeting_time_stop.date(),
            end_repeats,
            meeting_time_start.time(), meeting_time_stop.time())

        if not bool(calendarobj.calendar_multiple_meetings) and \
                not(futur_meeting_at_time):
            raise InvalidMeeting(
                'The start or end time you have entered is already '
                'occupied in the future.')

    reminder = None
    if remind_when and remind_who:
        try:
            reminder = dbaction.add_reminder(
                session=session,
                remind_when=remind_when,
                remind_who=remind_who)
        except SQLAlchemyError, err:  # pragma: no cover
            print 'add_reminder:', err
            raise SQLAlchemyError(err)

    reminder_id = None
    if reminder:
        reminder_id = reminder.reminder_id

    managers = '%s,' % fas_user.username
    if comanager:
        managers = managers + comanager

    meeting = dbaction.add_meeting(
        session=session,
        meeting_name=meeting_name,
        meeting_manager=managers,
        meeting_date=meeting_time_start.date(),
        meeting_date_end=meeting_time_stop.date(),
        meeting_time_start=meeting_time_start,
        meeting_time_stop=meeting_time_stop,
        meeting_information=meeting_information,
        calendarobj=calendarobj,
        reminder_id=reminder_id,
        meeting_region=meeting_region,
        recursion_frequency=frequency,
        recursion_ends=end_repeats,
        full_day=full_day)

    session.commit()
    return meeting


def edit_meeting(
        session, meeting, calendarobj, fas_user,
        meeting_name, meeting_date, meeting_date_end,
        meeting_time_start, meeting_time_stop, comanager,
        meeting_information,
        meeting_region, tzone,
        recursion_frequency, recursion_ends,
        remind_when, remind_who,
        full_day,
        edit_all_meeting=True,
        admin=False):
    """ When a user wants to edit a meeting to the database, we need to
    perform a number of test first checking that the input is valid
    and then edit the desired meeting.
    """
    if not is_user_managing_in_calendar(
            session, calendarobj.calendar_name, fas_user) and not admin:
        raise UserNotAllowed(
            'You are not allowed to add a meeting to this calendar')

    if not meeting_date_end:
        meeting_date_end = meeting_date

    if full_day:
        meeting_time_start = time(0, 0)
        meeting_time_stop = time(0, 0)
        tzone = 'UTC'

    meeting_time_start = convert_time(
        datetime(meeting_date.year, meeting_date.month, meeting_date.day,
                 meeting_time_start.hour,
                 meeting_time_start.minute),
        tzone, 'UTC')
    meeting_time_stop = convert_time(
        datetime(meeting_date_end.year, meeting_date_end.month,
                 meeting_date_end.day,
                 meeting_time_stop.hour,
                 meeting_time_stop.minute),
        tzone, 'UTC')

    if not is_date_in_future(meeting_date, meeting_time_start):
        raise InvalidMeeting('The date you entered is in the past')

    if meeting_time_start.date() > meeting_time_stop.date():
        raise InvalidMeeting(
            'The start date of your meeting is later than the stop date.')

    if meeting_time_start > meeting_time_stop:
        raise InvalidMeeting(
            'The start time of your meeting is later than the stop time.')

    if full_day:
        meeting_time_stop = meeting_time_stop + timedelta(days=1)

    if recursion_frequency and recursion_ends:
        agenda_free = agenda_is_free_in_future(
            session, calendarobj,
            meeting_time_start.date(), meeting_time_stop.date(),
            recursion_ends,
            meeting_time_start.time(), meeting_time_stop.time(),
            meeting_id = meeting.meeting_id)

        if not bool(calendarobj.calendar_multiple_meetings) and \
                not agenda_free:
            raise InvalidMeeting(
                'The start or end time you have entered is already '
                'occupied in the future.')

    ## The information are correct
    ## What we do now:
    # a) the meeting is not recursive -> edit the information as provided
    # b) the meeting is recursive and we update all the meetings
    #     -> recursion_end = today
    #     -> copy meeting to new object
    #     -> update new object
    # c) the meeting is recursive and the update only one meeting
    #     -> recursion_end = today
    #     -> copy meeting to new object w/o recursion
    #     -> update new object
    #     -> copy meeting to new object w/ recursion and date = date + offset

    remove_recursion = False
    if meeting.recursion_frequency:
        old_meeting = Meeting.copy(meeting)
        old_meeting.recursion_ends = meeting_date - timedelta(days=1)
        if old_meeting.recursion_ends > old_meeting.meeting_date:
            old_meeting.save(session)
        if not edit_all_meeting:
            remove_recursion = True
            new_meeting = Meeting.copy(meeting)
            new_meeting.meeting_date = meeting_date + timedelta(
                days=meeting.recursion_frequency)

            dt_start = datetime(
                new_meeting.meeting_date.year,
                new_meeting.meeting_date.month,
                new_meeting.meeting_date.day,
                new_meeting.meeting_time_start.hour,
                new_meeting.meeting_time_start.minute,
                tzinfo=pytz.utc)
            dt_stop = datetime(
                new_meeting.meeting_date_end.year,
                new_meeting.meeting_date_end.month,
                new_meeting.meeting_date_end.day,
                new_meeting.meeting_time_start.hour,
                new_meeting.meeting_time_start.minute,
                tzinfo=pytz.utc)

            free_time = agenda_is_free(
                session, calendarobj,
                dt_start, dt_stop)

            if not bool(calendarobj.calendar_multiple_meetings) and \
                    bool(free_time):
                new_meeting.save(session)

    meeting.meeting_name = meeting_name
    meeting.meeting_manager = '%s,' % fas_user.username
    if comanager:
        meeting.meeting_manager = '%s%s,' % (meeting.meeting_manager,
                                             comanager)

    meeting.meeting_date = meeting_time_start.date()
    meeting.meeting_date_end = meeting_time_stop.date()
    meeting.meeting_time_start = meeting_time_start.time()
    meeting.meeting_time_stop = meeting_time_stop.time()
    meeting.meeting_information = meeting_information

    region = meeting_region
    if not region:
        region = None
    meeting.meeting_region = region

    recursion_frequency = recursion_frequency
    if not recursion_frequency:
        recursion_frequency = None
    meeting.recursion_frequency = recursion_frequency

    if not recursion_ends:
        recursion_ends = date(2025, 12, 31)
    meeting.recursion_ends = recursion_ends

    if remind_when and remind_who:
        if meeting.reminder_id:
            meeting.reminder.reminder_offset = remind_when
            meeting.reminder.reminder_to = remind_who
            meeting.reminder.save(session)
        else:
            reminder = Reminder(remind_when,
                                remind_who,
                                None)
            reminder.save(session)
            session.flush()
            meeting.reminder = reminder
            session.flush()
    elif meeting.reminder_id:
        meeting.reminder.delete(session)
        meeting.reminder_id = None

    if remove_recursion:
        meeting.recursion_frequency = None
        meeting.recursion_ends = None

    meeting.save(session)
    session.commit()
    return meeting
