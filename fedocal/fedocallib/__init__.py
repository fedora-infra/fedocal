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

from datetime import datetime
from datetime import date
from datetime import time
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

from week import Week
from model import Calendar, Reminder, Meeting

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


# pylint: disable=R0913,R0914
def get_meetings(session, calendar, year=None, month=None, day=None,
    tzone='UTC'):
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
    week = get_week(session, calendar, year, month, day)
    meetings = {}
    fmt = '%Hh%M'
    for hour in HOURS[:-1]:
        for key in ['%sh00', '%sh30']:
            key = key % (hour)
            # pylint: disable=W0612
            meetings[key] = [None for cnt2 in range(0, 7)]
    for meeting in week.meetings:
        start = meeting.meeting_time_start.hour
        stop = meeting.meeting_time_stop.hour
        order = range(0, stop - start)
        invorder = order[:]
        invorder.reverse()
        cnt = 0
        for item in order:
            start_time = start + item
            key = convert_time(
                    datetime(2000, 01, 01, int(start_time), 0, 0),
                    'UTC',
                    tzone).strftime(fmt)
            day = meeting.meeting_date.weekday()
            if key in meetings:
                if meetings[key][day]:
                    meetings[key][day].append(meeting)
                else:
                    meetings[key][day] = [meeting]
            cnt = cnt + 1
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
    return Meeting.get_by_date(session, calendar, start_date,
        end_date)


def get_meetings_by_date_and_region(session, calendar, start_date,
    end_date, region):
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
    elif today.date() == indate and today.hour > int(start_time):
        return False
    else:
        return True


def get_past_meeting_of_user(session, username, from_date=date.today()):
    """ Return all past meeting which specified username is among the
    managers.
    :arg session: the database session to use
    :arg username: the FAS user name that you would like to have the
        past meetings for.
    :arg from_date: the date from which the futur meetings should be
        retrieved. Defaults to today
    """
    meetings = Meeting.get_past_meeting_of_user(session, username,
        from_date)
    return meetings


# pylint: disable=C0103
def get_future_single_meeting_of_user(session, username,
    from_date=date.today()):
    """ Return all future meeting which specified username is among the
    managers.

    :arg session: the database session to use
    :arg username: the FAS user name that you would like to have the
        past meetings for.
    :arg from_date: the date from which the futur meetings should be
        retrieved. Defaults to today
    """
    meetings = Meeting.get_future_single_meeting_of_user(session,
        username, from_date)
    return meetings


# pylint: disable=C0103
def get_future_regular_meeting_of_user(session, username,
    from_date=date.today()):
    """ Return all future recursive meeting which specified username is
    among the managers.

    :arg session: the database session to use
    :arg username: the FAS user name that you would like to have the
        past meetings for.
    :arg from_date: the date from which the futur meetings should be
        retrieved. Defaults to today
    """
    meetings = Meeting.get_future_regular_meeting_of_user(session,
        username, from_date)
    return meetings


def agenda_is_free(session, calendar, meeting_date,
    time_start, time_stop):
    """Check if there is already someting planned in this agenda at that
    time.

    :arg session: the database session to use
    :arg calendar: the name of the calendar of interest.
    :arg meeting_date: the date of the meeting (as Datetime object)
    :arg time_start: the time at which the meeting starts (as int)
    :arg time_stop: the time at which the meeting stops (as int)
    """
    meetings = Meeting.get_by_time(session, calendar, meeting_date,
        time(time_start), time(time_stop))
    if not meetings:
        return True
    else:
        return False


def is_user_managing_in_calendar(session, calendar_name, fas_user):
    """ Returns True if the user is in a group set as manager of the
    calendar and False otherwise. It will also return True if there are
    no groups set to manage the calendar.

    :arg session: the database session to use
    :arg calendar_name: the name of the calendar of interest.
    :arg fas_user: a FAS user object with all the info.
    """
    manager_groups = Calendar.get_manager_groups(session, calendar_name)
    if not manager_groups:
        return True
    else:
        return len(
                    set(manager_groups).intersection(
                    set(fas_user.groups))
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
    new_date = new_date - timedelta(minutes=new_date.minute,
                                    seconds=new_date.second,
                                    microseconds=new_date.microsecond)
    return new_date


def retrieve_meeting_to_remind(session):
    """ Retrieve all the meetings for which we have to send a reminder.

    :arg session: the database session to use.
    """
    today = datetime.utcnow()
    # Retrieve meeting planned in less than 12h
    new_date = _generate_date_rounded_to_the_hour(today, 12)
    meetings = Meeting.get_meeting_with_reminder(session,
        new_date.date(), new_date.time(), 'H-12')
    new_date = _generate_date_rounded_to_the_hour(today, 24)
    meetings.extend(Meeting.get_meeting_with_reminder(session,
        new_date.date(), new_date.time(), 'H-24'))
    new_date = _generate_date_rounded_to_the_hour(today, 48)
    meetings.extend(Meeting.get_meeting_with_reminder(session,
        new_date.date(), new_date.time(), 'H-48'))
    new_date = _generate_date_rounded_to_the_hour(today, 168)
    meetings.extend(Meeting.get_meeting_with_reminder(session,
        new_date.date(), new_date.time(), 'H-168'))

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
    meeting.meeting_time_start = meeting.meeting_time_start.replace(
        tzinfo=utc)
    start.value = datetime.combine(meeting.meeting_date,
        meeting.meeting_time_start)
    stop = entry.add('dtend')
    meeting.meeting_time_stop = meeting.meeting_time_stop.replace(
        tzinfo=utc)
    stop.value = datetime.combine(meeting.meeting_date,
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


def get_html_monthly_cal(day=None, month=None, year=None,
    calendar_name=None):
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
