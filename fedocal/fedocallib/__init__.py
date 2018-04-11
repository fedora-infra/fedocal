# -*- coding: utf-8 -*-

"""
fedocallib - Back-end library for the fedocal project.

Copyright (C) 2012-2014 Pierre-Yves Chibon
Author: Pierre-Yves Chibon <pingou@pingoured.fr>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.
See http://www.gnu.org/copyleft/gpl.html  for the full text of the
license.
"""

import copy
import vobject
import pytz
import operator

from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta
from dateutil import zoneinfo
from dateutil.relativedelta import relativedelta
import dateutil.rrule as rrule

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from fedocal.fedocallib.week import Week
from fedocal.fedocallib.model import (
    CalendarStatus, Calendar, Reminder, Meeting)
from fedocal.fedocallib import dbaction
from fedocal.fedocallib.exceptions import UserNotAllowed, InvalidMeeting

from fedocal.fedocallib.fedora_calendar import FedocalCalendar

from fedocal.fedocal_babel import gettext


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
    # Prevents the actual SQLAlchemy object from being changed
    meeting = copy.copy(meeting)
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


def get_week_of_location(session, location, year=None, month=None, day=None):
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
    week = Week(session, None, week_start, location)
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


def format_full_day_meeting(meeting_list, week_start):
    """ Return a list of list corresponding to an entry per day and for
    each day the list of full_day meeting associated.
    """
    meetings = []
    for cnt in range(7):
        meetings.append([])

    for meeting in meeting_list:
        idx = meeting.meeting_date - week_start
        if idx.days < 0:
            # Skip meetings finishing exactly at 00:00 on the day the week
            # starts
            if meeting.meeting_date_end == week_start \
                    and meeting.meeting_time_stop.hour == 0:
                continue
            idx = idx + timedelta(days=abs(idx.days))
        meetings[int(idx.days)].append(meeting)

        start_day = meeting.meeting_date
        # If the meeting starts before the beginning of the week, consider
        # the beginning of the week as the start day.
        if start_day < week_start:
            start_day = week_start

        end_day = meeting.meeting_date_end
        # If the end day is not the last day of the week, show it one day
        # shorter (otherwise it show on day X while the meeting ends on
        # day X at 00:00)
        if end_day < start_day + timedelta(days=6):
            end_day = end_day - timedelta(days=1)

        duration = end_day - start_day
        if abs(duration.days) > 0:
            cnt = int(idx.days)
            for day in range(1, duration.days + 1):
                key = cnt + day
                if key < len(meetings):
                    meetings[key].append(meeting)

    return meetings


def format_week_meeting(meeting_list, tzone, week_start):
    """ Return a dictionnary representing the meeting of the week in the
    appropriate format for the meeting provided in the meeting_list.
    """
    meetings = {}
    for hour in HOURS[:-1]:
        for key in ['%sh00', '%sh30']:
            key = key % (hour)
            # pylint: disable=W0612
            meetings[key] = [None for cnt2 in range(0, 7)]

    week_start = pytz.timezone(tzone).localize(
        datetime(week_start.year, week_start.month, week_start.day, 0, 0,))
    fmt = '%Hh%M'
    # week_start = convert_time(week_start, 'UTC', tzone)
    for meeting in meeting_list:
        meeting = convert_meeting_timezone(
            meeting, meeting.meeting_timezone, tzone)
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
        # Required to add the tz info, does not actually convert
        startdt = convert_time(
            startdt, meeting.meeting_timezone, meeting.meeting_timezone)

        stopdt = datetime(
            meeting.meeting_date_end.year,
            meeting.meeting_date_end.month,
            meeting.meeting_date_end.day,
            meeting.meeting_time_stop.hour,
            meeting.meeting_time_stop.minute, 0
        ) + timedelta(minutes=stop_delta)
        # Required to add the tz info
        stopdt = convert_time(
            stopdt, meeting.meeting_timezone, meeting.meeting_timezone)

        if stopdt < startdt:  # pragma: no cover
            stopdt = stopdt + timedelta(days=1)

        t_time = startdt
        while t_time < stopdt:
            nweek = week_start + timedelta(days=7)
            if t_time < week_start \
                    or t_time >= nweek:  # pragma: no cover
                # Skip meeting start or ending in another week
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
        meetings.append(convert_meeting_timezone(
            meeting, meeting.meeting_timezone, tzone))
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
        meetings.append(convert_meeting_timezone(
            meeting, meeting.meeting_timezone, tzone))
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
        mtg_conv = convert_meeting_timezone(
            meeting, meeting.meeting_timezone, tzone)
        last_rec = mtg_conv.recursion_ends - timedelta(
            days=mtg_conv.recursion_frequency)
        if last_rec >= from_date:
            meetings.append(mtg_conv)
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
            tzinfo=pytz.timezone(meeting.meeting_timezone))

        meeting_stop_date_time = datetime(
            meeting.meeting_date_end.year,
            meeting.meeting_date_end.month,
            meeting.meeting_date_end.day,
            meeting.meeting_time_stop.hour,
            meeting.meeting_time_stop.minute,
            tzinfo=pytz.timezone(meeting.meeting_timezone))

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


def delete_recursive_meeting(
        session, meeting, del_date=None, all_meetings=False):
    """ Delete from the database any future meetings associated with this
    recursion. For recursive meeting, deletion = set the end date to
    today.

    :arg session: the database session to use.
    :arg meeting: the Meeting object from which are removed all further
        meetings.
    """
    if not del_date:
        del_date = date.today()
    if not meeting.recursion_frequency \
            or meeting.recursion_ends < del_date:
        return

    meeting_date = meeting.meeting_date
    meeting_date_end = meeting.meeting_date_end
    cnt = 0
    while meeting_date < del_date:
        if meeting.recursion_ends < meeting_date + \
                timedelta(days=meeting.recursion_frequency):
            break
        meeting_date = meeting.meeting_date + timedelta(
            days=meeting.recursion_frequency * cnt)
        meeting_date_end = meeting.meeting_date_end + timedelta(
            days=meeting.recursion_frequency * cnt)
        cnt = cnt + 1

    if all_meetings:
        # If the meeting_date is before the meeting.meeting_date, just delete
        # the meeting
        if meeting.meeting_date >= meeting_date:
            meeting.delete(session)
        else:
            # End the recursion at the desired date
            meeting.recursion_ends = meeting_date - timedelta(days=1)
            meeting.save(session)
        session.commit()
    else:
        original_rec_end = meeting.recursion_ends
        # End recursion
        meeting.recursion_ends = meeting_date - timedelta(days=1)
        meeting.save(session)

        # Re-create after deletion has occured
        new_meeting = meeting.copy()

        new_meeting.add_manager(session, meeting.meeting_manager)
        new_meeting.meeting_date = meeting_date + timedelta(
            days=meeting.recursion_frequency)
        new_meeting.meeting_date_end = meeting_date_end + timedelta(
            days=meeting.recursion_frequency)
        new_meeting.recursion_ends = original_rec_end

        new_meeting.save(session)


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

        if new_date.date() != end_date.date():
            # in case the end_date is day after (ie: 23:45 + 30min), make
            # the end_date as start_date at 23:59
            end_date = datetime(
                new_date.year, new_date.month, new_date.day, 23, 59)

        meetings.extend(Meeting.get_meeting_with_reminder(
            session, new_date.date(), new_date.time(), end_date.time(),
            'H-%s' % reminder_time))

    return meetings


def add_meeting_to_vcal(ical, meeting, reminder=None):
    """ Convert a Meeting object into iCal object and add it to the
    provided calendar.

    :arg ical: the iCal calendar object to which the meetings should
        be added.
    :arg meeting: a single fedocal.model.Meeting object to convert to
        iCal and add to the provided calendar.
    :kwarg reminder: None or a datetime.timedelta instance.
    """
    entry = ical.add('vevent')
    entry.add('summary').value = meeting.meeting_name
    if meeting.meeting_information:
        entry.add('description').value = meeting.meeting_information
    entry.add('organizer').value = ', '.join(meeting.meeting_manager)
    if meeting.meeting_location:
        entry.add('location').value = meeting.meeting_location

    start = entry.add('dtstart')
    stop = entry.add('dtend')
    if meeting.full_day:
        start.value = meeting.meeting_date
        stop.value = meeting.meeting_date_end
        entry.add('transp').value = 'TRANSPARENT'
    else:
        tz = zoneinfo.gettz(meeting.meeting_timezone)

        dti_start = datetime.combine(
            meeting.meeting_date, meeting.meeting_time_start)
        start.value = dti_start.replace(tzinfo=tz)

        dti_end = datetime.combine(
            meeting.meeting_date_end, meeting.meeting_time_stop)
        stop.value = dti_end.replace(tzinfo=tz)

    if meeting.recursion_frequency and meeting.recursion_ends:
        newrule = rrule.rruleset()
        freq = meeting.recursion_frequency / 7
        recursion_ends = datetime.combine(
            meeting.recursion_ends, time(0)).replace(tzinfo=pytz.utc)
        newrule.rrule(
            rrule.rrule(
                freq=rrule.WEEKLY,
                interval=freq,
                dtstart=start.value,
                until=recursion_ends))
        entry.rruleset = newrule

    if reminder:
        valarm = entry.add('valarm')
        valarm.add('trigger').value = reminder
        valarm.add('action').value = 'DISPLAY'
        valarm.add('description').value = (
            '[{calendar_name}] [Fedocal] Reminder meeting: {meeting_name}'
        ).format(calendar_name=meeting.calendar_name,
                 meeting_name=meeting.meeting_name)


def add_meetings_to_vcal(ical, meetings, reminder=None):
    """ Convert the Meeting objects into iCal object and add them to
    the provided calendar.

    :arg ical: the iCal calendar object to which the meetings should
        be added.
    :arg meetings: a list of fedocal.model.Meeting object to convert to
        iCal and add to the provided calendar.
    :kwarg reminder: None or a datetime.timedelta instance.
    """
    for meeting in meetings:
        add_meeting_to_vcal(ical, meeting, reminder)


def get_html_monthly_cal(
        day=None, month=None, year=None, calendar_name=None, loc_name=None,
        busy_days=[]):
    """ Display a monthly calendar as HTML.

    :kwarg day: optionnal day (as int). Defaults to current day
    :kwarg month: optionnal month (as int). Defaults to current month
    :kwarg year: optionnal year. Defaults to current year.
    :kwarg calendar_name: the name of the calendar to which the links
        should point.
    :kwarg loc_name: the name of the location to which the links
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
                              calendar_name=calendar_name,
                              loc_name=loc_name,
                              busy_days=busy_days)
    curmonth_cal_nf = htmlcal.formatmonth()

    return curmonth_cal_nf


def get_by_date(session, calendarobj, start_date, end_date, tzone='UTC',
                extended=True, name=None):
    """ Returns all the meetings in a given time period.
    Recurring meetings are expanded as if each was a single meeting.

    :arg session: the database session to use
    :arg calendarobj: the calendar (object) of interest.
    :arg start_date: a Date object representing the beginning of the
        period
    :arg start_date: a Date object representing the ending of the period
    :kwarg tzone: the timezone in which the meetings should be displayed
        defaults to UTC.
    :kwarg name: Defaults to None, if set the meetings returned will be
            filtered for this string in their name.

    """
    meetings_utc = Meeting.get_by_date(
        session, calendarobj, start_date, end_date, no_recursive=extended,
        name=name)
    if extended:
        meetings_utc.extend(
            Meeting.get_regular_meeting_by_date(
                session, calendarobj, start_date, end_date, name=name))
    else:
        meetings_utc.extend(
            Meeting.get_active_regular_meeting_by_date(
                session, calendarobj, start_date, name=name))

    meetings = list(set(meetings_utc))
    if tzone:
        meetings = [
            convert_meeting_timezone(
                meeting, meeting.meeting_timezone, tzone)
            for meeting in meetings
        ]
    meetings.sort(key=operator.attrgetter('meeting_date'))
    return meetings


def get_meetings_by_date_and_location(
        session, calendar, start_date, end_date, location):
    """ Return a list of meetings which have or will occur in between
    the two provided dates.

    :arg session: the database session to use
    :arg calendar: the name of the calendar of interest.
    :arg start_date: the date from which we would like to retrieve the
        meetings (this day is included in the selection).
    :arg start_date: the date until which we would like to retrieve the
        meetings (this day is excluded from the selection).
    :arg location: the location in which the meetings occurs.
    """
    calendar = Calendar.by_id(session, calendar)
    return Meeting.get_by_date_and_location(session, calendar, start_date,
                                            end_date, location)


def get_by_date_at_location(
        session, location, start_date, end_date, tzone='UTC'):
    """ Returns all the meetings in a given time period at a given location.
    Recurring meetings are expanded as if each was a single meeting.

    :arg session: the database session to use
    :arg calendarobj: the calendar (object) of interest.
    :arg start_date: a Date object representing the beginning of the
        period
    :arg start_date: a Date object representing the ending of the period
    :kwarg tzone: the timezone in which the meetings should be displayed
        defaults to UTC.
    """
    meetings_utc = Meeting.get_by_date_at_location(
        session, location, start_date, end_date, no_recursive=True)
    meetings_utc.extend(Meeting.get_regular_meeting_by_date_at_location(
        session, location, start_date, end_date))
    meetings = list(set(meetings_utc))
    if tzone:
        meetings = [
            convert_meeting_timezone(
                meeting, meeting.meeting_timezone, tzone)
            for meeting in meetings
        ]
    meetings.sort(key=operator.attrgetter('meeting_date'))
    return meetings


# pylint: disable=R0913,R0914
def add_meeting(
        session, calendarobj, fas_user,
        meeting_name, meeting_date, meeting_date_end,
        meeting_time_start, meeting_time_stop, comanager,
        meeting_information,
        meeting_location, tzone,
        frequency, end_repeats,
        remind_when, reminder_from, remind_who,
        full_day,
        admin=False):
    """ When a user wants to add a meeting to the database, we need to
    perform a number of test first checking that the input is valid
    and then add the desired meeting.
    """
    if not is_user_managing_in_calendar(
            session,
            calendarobj.calendar_name,
            fas_user) and not admin:  # pragma: no cover
        raise UserNotAllowed(
            gettext(
                'You are not allowed to add a meeting to this calendar'
            )
        )

    if meeting_date_end is None:
        meeting_date_end = meeting_date

    if full_day:
        meeting_time_start = time(0, 0)
        meeting_time_stop = time(0, 0)
        tzone = 'UTC'

    meeting_time_start = datetime(
        meeting_date.year, meeting_date.month, meeting_date.day,
        meeting_time_start.hour, meeting_time_start.minute)
    meeting_time_stop = datetime(
        meeting_date_end.year, meeting_date_end.month, meeting_date_end.day,
        meeting_time_stop.hour, meeting_time_stop.minute)

    if meeting_time_start.date() > meeting_time_stop.date():
        raise InvalidMeeting(
            gettext(
                'The start date of your meeting is later than the stop date.'
            )
        )

    if meeting_time_start > meeting_time_stop:
        raise InvalidMeeting(
            gettext(
                'The start time of your meeting is later than the stop time.'
            )
        )

    if full_day:
        meeting_time_stop = meeting_time_stop + timedelta(days=1)

    if meeting_time_start == meeting_time_stop:
        raise InvalidMeeting(
            gettext(
                'The start date of your meeting exactly '
                'the same as the stop date.'
            )
        )

    reminder = None
    if remind_when and remind_who and reminder_from:
        remind_who = ','.join([
            ppl.strip()
            for ppl in remind_who.split(',')
            if ppl.strip()
        ])
        reminder = dbaction.add_reminder(
            session=session,
            remind_when=remind_when,
            reminder_from=reminder_from,
            remind_who=remind_who
        )

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
        meeting_timezone=tzone,
        meeting_information=meeting_information,
        calendarobj=calendarobj,
        reminder_id=reminder_id,
        meeting_location=meeting_location,
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
        meeting_location, tzone,
        recursion_frequency, recursion_ends,
        remind_when, reminder_from, remind_who,
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
            gettext('You are not allowed to add a meeting to this calendar'))

    if not meeting_date_end:
        meeting_date_end = meeting_date

    if full_day:
        meeting_time_start = time(0, 0)
        meeting_time_stop = time(0, 0)
        tzone = 'UTC'

    meeting_time_start = datetime(
        meeting_date.year, meeting_date.month, meeting_date.day,
        meeting_time_start.hour, meeting_time_start.minute)
    meeting_time_stop = datetime(
        meeting_date_end.year, meeting_date_end.month, meeting_date_end.day,
        meeting_time_stop.hour, meeting_time_stop.minute)

    if meeting_time_start.date() > meeting_time_stop.date():
        raise InvalidMeeting(
            gettext(
                'The start date of your meeting is later than the stop date.'
            )
        )

    if meeting_time_start > meeting_time_stop:
        raise InvalidMeeting(
            gettext(
                'The start time of your meeting is later than the stop time.'
            )
        )

    if full_day and meeting_time_start == meeting_time_stop:
        meeting_time_stop = meeting_time_start + timedelta(days=1)

    if meeting_time_start == meeting_time_stop:
        raise InvalidMeeting(
            gettext(
                'The start date of your meeting exactly the same as '
                'the stop date.'
            )
        )

    if meeting.calendar_name != calendarobj.calendar_name:
        meeting.calendar_name = calendarobj.calendar_name

    # The information are correct
    # What we do now:
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

        closest_meeting = update_date_rec_meeting(
            meeting, action='closest', date_limit=meeting_date)

        end_rec = closest_meeting.meeting_date - timedelta(days=1)
        if (meeting_date - closest_meeting.meeting_date).days < 0:
            end_rec = meeting_date + timedelta(
                days=(meeting_date - closest_meeting.meeting_date).days)

        if meeting_date > meeting.meeting_date:
            old_meeting = meeting.copy()
            old_meeting.add_manager(session, meeting.meeting_manager)
            old_meeting.recursion_ends = end_rec
            if old_meeting.recursion_ends > old_meeting.meeting_date:
                old_meeting.save(session)

        if not edit_all_meeting:
            remove_recursion = True
            new_meeting = meeting.copy()
            new_meeting.add_manager(session, meeting.meeting_manager)
            new_meeting.meeting_date = closest_meeting.meeting_date \
                + timedelta(days=meeting.recursion_frequency)
            new_meeting.meeting_date_end = closest_meeting.meeting_date_end \
                + timedelta(days=meeting.recursion_frequency)

            new_meeting.save(session)

    meeting.meeting_name = meeting_name

    meeting.clear_managers(session)
    if fas_user.username not in meeting.meeting_manager:
        meeting.add_manager(session, fas_user.username)
    if comanager:
        meeting.add_manager(session, comanager)

    meeting.meeting_date = meeting_time_start.date()
    meeting.meeting_date_end = meeting_time_stop.date()
    meeting.meeting_time_start = meeting_time_start.time()
    meeting.meeting_time_stop = meeting_time_stop.time()
    meeting.meeting_information = meeting_information
    meeting.meeting_location = meeting_location or None
    meeting.meeting_timezone = tzone

    if edit_all_meeting or not meeting.recursion_ends:
        recursion_frequency = recursion_frequency
        if not recursion_frequency:
            recursion_frequency = None
        meeting.recursion_frequency = recursion_frequency

        if recursion_frequency and not recursion_ends:
            recursion_ends = date(2025, 12, 31)
        meeting.recursion_ends = recursion_ends

    if remind_when and remind_who and reminder_from:
        remind_who = ','.join([
            ppl.strip()
            for ppl in remind_who.split(',')
            if ppl.strip()
        ])
        if meeting.reminder_id:
            meeting.reminder.reminder_offset = remind_when
            meeting.reminder.reminder_from = reminder_from
            meeting.reminder.reminder_to = remind_who
            meeting.reminder.save(session)
        else:
            reminder = dbaction.add_reminder(
                session=session,
                remind_when=remind_when,
                reminder_from=reminder_from,
                remind_who=remind_who)
            meeting.reminder = reminder
            session.flush()
    elif meeting.reminder_id:
        reminder = meeting.reminder
        meeting.reminder_id = None
        session.flush()
        session.delete(reminder)
        session.expunge(reminder)

    if remove_recursion:
        meeting.recursion_frequency = None
        meeting.recursion_ends = None

    meeting.full_day = full_day

    meeting.save(session)
    session.commit()
    return meeting


def get_calendar_statuses(session):
    """ Return the list of all the status available for the calendars. """
    return CalendarStatus.all(session)


def search_meetings(session, keyword):
    """ Return the list of meetings matching the provided keyword.
    """
    keyword = keyword.replace('*', '%')
    return Meeting.search(session, keyword)


def get_locations(session):
    """ Return the list of all the locations where meetings happen according
    to the database.
    """
    return Meeting.get_locations(session)


def search_locations(session, keyword):
    """ Return the list of locations matching the provided keyword.
    """
    keyword = keyword.replace('*', '%')
    return Meeting.search_locations(session, keyword)


def clear_calendar(session, calendar):
    """ Remove all the meetings from the specified calendar.
    """
    return Meeting.clear_from_calendar(session, calendar)


def add_vcal_file(session, calendar, stream, fas_user, admin=False):
    """ Add the meetings from the iCalendar stream provided into the calendar
    specified.
    """
    # Build a dict with all the common timezones storing for each their
    # localize name and their offset (ie: CEST 2:00:00)
    timezone_lookup = dict()
    for tz in pytz.common_timezones:
        name = pytz.timezone(tz).localize(datetime.now()).tzname()
        offset = pytz.timezone(tz).localize(datetime.now()).utcoffset()
        key = (name, offset)
        if key in timezone_lookup:
            timezone_lookup[key].append(tz)
        else:
            timezone_lookup[key] = [tz]

    major_timezones = {
        'CET': 'Europe/Paris',
        'CEST': 'Europe/Paris',
        'EDT': 'US/Eastern',
    }

    meetings = vobject.readOne(stream)
    for meeting in meetings.components():
        if meeting.name == 'VTIMEZONE':
            continue
        meeting_name = ', '.join(
            [el.value for el in meeting.contents.get('summary', [])])
        meeting_description = ', '.join(
            [el.value for el in meeting.contents.get('description', [])]
        ) or None

        tzone = 'UTC'
        full_day = False
        if meeting.contents.get('transp', False):
            full_day = True

        meeting_date = meeting.dtstart.value
        meeting_time_start = time(0, 0)
        if isinstance(meeting_date, datetime):
            tzinfo = meeting_date.tzinfo
            if hasattr(tzinfo, 'zone'):
                tzone = tzinfo.zone
            elif meeting_date.tzname() == 'UTC':
                tzone = 'UTC'
            else:
                tzone = str(tzinfo).split("'")[1]
                if '/' in tzone:
                    tzone = '/'.join(tzone.rsplit('/', 2)[1:])

            try:
                pytz.timezone(tzone)
            except pytz.UnknownTimeZoneError:
                name = meeting_date.tzname()
                key = (meeting_date.tzname(), meeting_date.utcoffset())
                if name in major_timezones:
                    tzone = major_timezones[name]
                elif key in timezone_lookup:
                    tzone = timezone_lookup[key][0]
                else:
                    tzone = meeting_date.tzname()
            meeting_time_start = meeting_date.time()
            meeting_date = meeting_date.date()

        meeting_date_end = meeting_date
        meeting_time_stop = time(0, 0)
        if meeting.name == 'VEVENT':
            meeting_date_end = meeting.dtend.value
        else:
            full_day = True

        if isinstance(meeting_date_end, datetime):
            meeting_time_stop = meeting_date_end.time()
            meeting_date_end = meeting_date_end.date()

        add_meeting(
            session,
            calendarobj=calendar,
            fas_user=fas_user,
            meeting_name=meeting_name,
            meeting_date=meeting_date,
            meeting_date_end=meeting_date_end,
            meeting_time_start=meeting_time_start,
            meeting_time_stop=meeting_time_stop,
            comanager=fas_user.username,
            meeting_information=meeting_description,
            meeting_location=None,
            tzone=tzone,
            frequency=None,
            end_repeats=None,
            remind_when=None,
            reminder_from=None,
            remind_who=None,
            full_day=full_day,
            admin=admin)


def update_date_rec_meeting(meeting, action='last', date_limit=None):
    """ From a recursive meeting, returns a meeting which date corresponds
    either to that of the last recursion that occured, or the next recursion
    that will occur.
    """
    if not date_limit:
        date_limit = date.today()
    if date_limit < meeting.meeting_date:
        date_limit = meeting.meeting_date

    if meeting.recursion_frequency and meeting.recursion_ends:
        meetingobj = Meeting.copy(meeting)
        delta = timedelta(days=meetingobj.recursion_frequency)
        while meetingobj.meeting_date < date_limit:
            if meetingobj.recursion_ends < meetingobj.meeting_date + \
                    delta:  # pragma: no cover
                break
            meetingobj.meeting_date = meetingobj.meeting_date + delta
            meetingobj.meeting_date_end = meetingobj.meeting_date_end + delta
        meetingobj.meeting_manager_user = meeting.meeting_manager_user

        if action == 'closest':
            last_date = meetingobj.meeting_date - delta
            delta_before = last_date - date_limit
            delta_after = meetingobj.meeting_date - date_limit
            if abs(delta_before) < abs(delta_after):
                action = 'last'

        if action == 'last':
            last_date = meetingobj.meeting_date - delta
            if meeting.meeting_date < last_date:
                meetingobj.meeting_date = last_date
                meetingobj.meeting_date_end = meetingobj.meeting_date_end - \
                    delta

        meeting = meetingobj

    return meeting


def __get_days(meetings):
    """ Return a set of all the meeting days for the list of meetings
    provided.
    """
    days = set()
    for meeting in meetings:
        duration = meeting.meeting_date_end - meeting.meeting_date
        if abs(duration.days) > 0:
            for day in range(0, duration.days):
                days.add((meeting.meeting_date + timedelta(days=day)).day)
        else:
            days.add(meeting.meeting_date.day)
    return days


def get_days_of_month_location(session, loc_name, year, month, tzone=None):
    """ Return the list of days having a meeting on the specified month.
    """
    start_date = datetime(year, month, 1).date()
    end_date = start_date \
        + relativedelta(months=+1) \
        - timedelta(days=1)

    meetings = get_by_date_at_location(
        session, loc_name, start_date, end_date, tzone)
    return __get_days(meetings)


def get_days_of_month_calendar(session, calendar, year, month, tzone=None):
    """ Return the list of days having a meeting on the specified month.
    """

    start_date = datetime(year, month, 1).date()
    end_date = start_date \
        + relativedelta(months=+1) \
        - timedelta(days=1)

    meetings = get_by_date(
        session, calendar, start_date, end_date, tzone)
    return __get_days(meetings)
