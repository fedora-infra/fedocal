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

from datetime import datetime
from datetime import date
from datetime import timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from week import Week
from model import Calendar, Reminder, Meeting


WEEK = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday',
        'Saturday', 'Sunday']


def create_session(db_url, debug=False, pool_recycle=3600):
    """ Create the Session object to use to query the database.

    :arg db_url, URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :arg debug, a boolean specifying wether we should have the verbose
    output of sqlalchemy or not.
    :return a Session that can be used to query the database.
    """
    engine = create_engine(db_url, echo=debug, pool_recycle=pool_recycle)
    session = sessionmaker(bind=engine)
    return session()


def get_calendars(session):
    """ Retrieve the list of Calendar from the database. """
    return Calendar.get_all(session)


def get_week(session, calendar, year=None, month=None, day=None):
    """ For a given date, retrieve the corresponding week.
    For any missing parameters (ie: None), use the value of the current
    day.
    :arg calendar, the name of the calendar of interest.
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
    week = Week(session, calendar, week_start)
    return week

