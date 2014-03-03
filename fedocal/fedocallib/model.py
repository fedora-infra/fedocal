# -*- coding: utf-8 -*-

"""
model - an object mapper to a SQL database representation of the data
        stored in this project.

Copyright (C) 2012-2014 Pierre-Yves Chibon
Author: Pierre-Yves Chibon <pingou@pingoured.fr>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.
See http://www.gnu.org/copyleft/gpl.html  for the full text of the
license.
"""
__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources
import operator

from datetime import date
from datetime import timedelta

from sqlalchemy import (
    Boolean,
    create_engine,
    Column,
    distinct,
    Date,
    Enum,
    ForeignKey,
    ForeignKeyConstraint,
    Integer,
    String,
    Table,
    Text,
    Time,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session
from sqlalchemy.orm import relation as relationship
from sqlalchemy.sql import and_, or_
from sqlalchemy import func as safunc

BASE = declarative_base()


def create_tables(db_url, alembic_ini=None, debug=False):
    """ Creates the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :kwarg alembic_ini, path to the alembic ini file. This is necessary to be
      able to use alembic correctly, but not for the unit-tests.
    :kwarg debug, a boolean specifying wether we should have the verbose
    output of sqlalchemy or not.
    :return a session that can be used to query the database.
    """
    engine = create_engine(db_url, echo=debug)
    BASE.metadata.create_all(engine)

    if alembic_ini is not None:  # pragma: no cover
        # then, load the Alembic configuration and generate the
        # version table, "stamping" it with the most recent rev:
        from alembic.config import Config
        from alembic import command
        alembic_cfg = Config(alembic_ini)
        command.stamp(alembic_cfg, "head")

    scopedsession = scoped_session(sessionmaker(bind=engine))
    fill_default_status(scopedsession)
    return scopedsession


def drop_tables(db_url, engine):  # pragma: no cover
    """ Drops the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    """
    engine = create_engine(db_url)
    BASE.metadata.drop_all(engine)


def fill_default_status(session):
    """ Fill in the default status for the calendar. """
    for str_status in ['Enabled', 'Disabled']:
        status = CalendarStatus(str_status)
        session.add(status)
    session.commit()


class CalendarStatus(BASE):
    """ Calendar_status table.

    This table lists all the status a calendar can have.
    """
    __tablename__ = 'calendar_status'
    status = Column(String(50), primary_key=True)

    def __init__(self, status):
        """ Constructor instanciating the defaults values. """
        self.status = status

    def __repr__(self):  # pragma: no cover
        """ Representation of the CalendarStatus object when printed.
        """
        return "<CalendarStatus('%s')>" % (self.status)

    @classmethod
    def all(cls, session):
        """ Return all the CalendarStatus. """
        return session.query(
            cls
        ).order_by(
            cls.status.desc()
        ).all()


class Calendar(BASE):
    """ Calendar table.

    Define the calendar available in this application.
    """

    __tablename__ = 'calendars'
    calendar_name = Column(String(80), primary_key=True)
    calendar_contact = Column(String(80), nullable=False)
    calendar_description = Column(String(500), nullable=True)
    # 3 groups (3*32)
    calendar_editor_group = Column(String(100), nullable=True)
    calendar_admin_group = Column(String(100), nullable=True)
    calendar_status = Column(
        String(50),
        ForeignKey('calendar_status.status', onupdate="cascade"),
        default='Enabled',
        nullable=False)
    meetings = relationship("Meeting")

    def __init__(
            self, calendar_name, calendar_contact, calendar_description,
            calendar_editor_group=None, calendar_admin_group=None,
            calendar_status='Enabled'):
        """ Constructor instanciating the defaults values. """
        self.calendar_name = calendar_name
        self.calendar_contact = calendar_contact
        self.calendar_description = calendar_description
        self.calendar_editor_group = calendar_editor_group
        self.calendar_admin_group = calendar_admin_group
        self.calendar_status = calendar_status

    def __repr__(self):
        """ Representation of the Calendar object when printed.
        """
        return "<Calendar('%s')>" % (self.calendar_name)

    def to_json(self):
        """ JSON representation of the Calendar object.
        """
        return dict(
            calendar_name=self.calendar_name,
            calendar_contact=self.calendar_contact,
            calendar_description=self.calendar_description,
            calendar_editor_group=self.calendar_editor_group,
            calendar_admin_group=self.calendar_admin_group,
            calendar_status=self.calendar_status
        )

    def save(self, session):
        """ Save the object into the database. """
        session.add(self)

    def delete(self, session):
        """ Remove the object into the database. """
        session.delete(self)

    @classmethod
    def by_id(cls, session, identifier):
        """ Retrieve a Calendar object from the database based on its
        identifier.
        :return None if no calendar matched this identifier.
        """
        return session.query(cls).get(identifier)

    @classmethod
    def get_editor_groups(cls, session, identifier):
        """ Return the list of editors for a given calendar.
        """
        calendar = Calendar.by_id(session, identifier)
        if not calendar or not calendar.calendar_editor_group:
            groups = []
        else:
            groups = [item.strip()
                      for item in calendar.calendar_editor_group.split(',')]
        return groups

    @classmethod
    def get_admin_groups(cls, session, identifier):
        """ Return the list of admin group for a given calendar.
        """
        calendar = Calendar.by_id(session, identifier)
        if not calendar or not calendar.calendar_admin_group:
            groups = []
        else:
            groups = [item.strip()
                      for item in calendar.calendar_admin_group.split(',')]
        return groups

    @classmethod
    def get_all(cls, session):
        """ Retrieve all the Calendar available."""
        return session.query(cls).order_by(cls.calendar_name).all()

    @classmethod
    def by_status(cls, session, status):
        """ Retrieve all the Calendar having a certain status. """
        return session.query(
            cls
        ).filter(
            cls.calendar_status == status
        ).all()


class User(BASE):
    """ User table.

    Store the information about the users of fedocal.
    """
    __tablename__ = 'users'
    username = Column(String(50), primary_key=True)

    def __repr__(self):
        """ Representation of the Reminder object when printed.
        """
        return "<User('%s')>" % (
            self.username)

    @classmethod
    def get_or_create(cls, session, username):
        """ Return an existing or a new user. """
        user = session.query(cls).get(username)
        if not user:
            user = User.create(session, username)
        return user

    @classmethod
    def create(cls, session, username):
        """ Create a new User. """
        user = cls(username=username)
        session.add(user)
        session.flush()
        return user


class MeetingsUsers(BASE):
    __tablename__ = 'meetings_users'
    username = Column(
        String(50),
        ForeignKey(
            'users.username', onupdate='cascade', ondelete='cascade'),
        primary_key=True)
    meeting_id = Column(
        Integer,
        ForeignKey(
            'meetings.meeting_id', onupdate='cascade', ondelete='cascade'),
        primary_key=True)
    meeting = relationship("Meeting")
    user = relationship("User", backref="meetings")

    def __repr__(self):
        """ Representation of the Reminder object when printed.
        """
        return "<MeetingsUsers('%s', '%s')>" % (
            self.meeting_id, self.username)

    @classmethod
    def get_or_create(cls, session, meeting, user):
        """ Return an existing or a new user. """
        meeting_user = session.query(
            cls
        ).filter(
            cls.user == user
        ).filter(
            cls.meeting == meeting
        ).first()
        if not meeting_user:
            meeting_user = MeetingsUsers.create(session, meeting, user)
        return meeting_user

    @classmethod
    def create(cls, session, meeting, user):
        """ Create a new User. """
        meeting_user = cls(meeting=meeting, user=user)
        session.add(meeting_user)
        session.flush()
        return meeting_user


# pylint: disable=R0902
class Meeting(BASE):
    """ Meetings table.

    Store the information about the meetings set in the application.
    """

    __tablename__ = 'meetings'
    meeting_id = Column(Integer, primary_key=True)
    meeting_name = Column(String(200), nullable=False)
    calendar_name = Column(
        String(80),
        ForeignKey('calendars.calendar_name', onupdate="cascade"),
        nullable=False)
    calendar = relationship("Calendar", lazy='joined')
    # 5 person max (32 * 5) + 5 = 165
    meeting_manager_user = relationship('MeetingsUsers', lazy='joined')
    meeting_date = Column(Date, default=safunc.now(), nullable=False)
    meeting_date_end = Column(Date, default=safunc.now(), nullable=False)
    meeting_time_start = Column(Time, default=safunc.now(), nullable=False)
    meeting_time_stop = Column(Time, default=safunc.now(), nullable=False)
    meeting_timezone = Column(Text, nullable=False, default='UTC')
    meeting_information = Column(Text, nullable=True)
    meeting_location = Column(Text, default=None, nullable=True)
    reminder_id = Column(
        Integer,
        ForeignKey('reminders.reminder_id', onupdate="cascade"),
        nullable=True)
    reminder = relationship("Reminder", lazy='joined')
    full_day = Column(Boolean, default=False)

    recursion_frequency = Column(Integer, nullable=True, default=None)
    recursion_ends = Column(Date, nullable=True, default=None)

    # pylint: disable=R0913
    def __init__(
            self, meeting_name,
            meeting_date, meeting_date_end,
            meeting_time_start, meeting_time_stop,
            meeting_information, calendar_name, meeting_timezone='UTC',
            reminder_id=None, meeting_location=None, recursion_frequency=None,
            recursion_ends=None, full_day=False):
        """ Constructor instanciating the defaults values. """
        self.meeting_name = meeting_name
        self.meeting_date = meeting_date
        self.meeting_date_end = meeting_date_end
        self.meeting_time_start = meeting_time_start
        self.meeting_time_stop = meeting_time_stop
        self.meeting_timezone = meeting_timezone
        self.meeting_information = meeting_information
        self.calendar_name = calendar_name
        self.reminder_id = reminder_id
        self.meeting_location = meeting_location
        self.recursion_frequency = recursion_frequency
        self.recursion_ends = recursion_ends
        self.full_day = full_day

    def __repr__(self):
        """ Representation of the Reminder object when printed.
        """
        return "<Meeting('%s', '%s', '%s')>" % (
            self.calendar, self.meeting_name, self.meeting_date)

    def save(self, session):
        """ Save the object into the database. """
        session.add(self)

    def to_json(self):
        """ Return a jsonify string of the object.
        """
        return dict(
            meeting_id=self.meeting_id,
            meeting_name=self.meeting_name,
            meeting_manager=self.meeting_manager,
            meeting_date=self.meeting_date.strftime('%Y-%m-%d'),
            meeting_date_end=self.meeting_date_end.strftime('%Y-%m-%d'),
            meeting_time_start=self.meeting_time_start.strftime('%H:%M:%S'),
            meeting_time_stop=self.meeting_time_stop.strftime('%H:%M:%S'),
            meeting_timezone=self.meeting_timezone,
            meeting_information=self.meeting_information,
            meeting_location=self.meeting_location,
            calendar_name=self.calendar_name
        )

    def add_manager(self, session, meeting_manager):
        """ Add the provided manager(s) to this meeting. """
        if ',' in meeting_manager:
            meeting_manager = meeting_manager.split(',')

        if isinstance(meeting_manager, basestring):
            meeting_manager = [meeting_manager]

        for manager in meeting_manager:
            manager = manager.strip()
            if manager and manager not in self.meeting_manager:
                self.meeting_manager_user.append(
                    MeetingsUsers.get_or_create(
                        session, self, User.get_or_create(session, manager)
                    )
                )

    def clear_managers(self, session):
        """ Remove all the managers related to this meeting. """
        for manager in self.meeting_manager_user:
            session.delete(manager)
        session.commit()

    @property
    def meeting_manager(self):
        """ Return the list of the managers. """
        return sorted(
            [user.username for user in self.meeting_manager_user if user])

    def delete(self, session):
        """ Remove the object into the database. """
        self.clear_managers(session)
        session.delete(self)

    def copy(self, meeting=None):
        """ Return if a meeting is provided, the same meeting with
        updated information or else a new Meeting object containing the
        same information as the present one.
        If a Meeting object is provided, all the information *but* the
        date will be copied.

        :kwarg meeting: a Meeting object to update
        :return a Meeting object with the same information as the current
        object.
        """
        if meeting:
            meeting.meeting_name = self.meeting_name
            meeting.meeting_manager_user = self.meeting_manager_user
            #meeting.meeting_date = self.meeting_date
            meeting.meeting_time_start = self.meeting_time_start
            meeting.meeting_time_stop = self.meeting_time_stop
            meeting.meeting_timezone = self.meeting_timezone
            meeting.calendar_name = self.calendar_name
            meeting.calendar = self.calendar
            meeting.reminder_id = self.reminder_id
            meeting.meeting_location = self.meeting_location
            meeting.recursion_frequency = self.recursion_frequency
            meeting.recursion_ends = self.recursion_ends
            meeting.full_day = self.full_day
        else:
            meeting = Meeting(
                meeting_name=self.meeting_name,
                meeting_date=self.meeting_date,
                meeting_date_end=self.meeting_date_end,
                meeting_time_start=self.meeting_time_start,
                meeting_time_stop=self.meeting_time_stop,
                meeting_timezone=self.meeting_timezone,
                meeting_information=self.meeting_information,
                calendar_name=self.calendar_name,
                reminder_id=self.reminder_id,
                meeting_location=self.meeting_location,
                recursion_frequency=self.recursion_frequency,
                recursion_ends=self.recursion_ends,
                full_day=self.full_day
            )
        # Update object associated to the meeting
        meeting.reminder = self.reminder
        meeting.calendar = self.calendar
        meeting.reminder = self.reminder
        return meeting

    @classmethod
    def by_id(cls, session, identifier):
        """ Retrieve a Meeting object from the database based on its
        identifier.
        :return None if no calendar matched this identifier.
        """
        return session.query(cls).get(identifier)

    @classmethod
    def get_by_date(
            cls, session, calendar, start_date, stop_date,
            full_day=None, no_recursive=False):
        """ Retrieve the list of meetings between two date.
        We include the start date and exclude the stop date.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        query = session.query(
            cls
        ).filter(
            Meeting.calendar == calendar
        ).filter(
            or_(
                and_(
                    (Meeting.meeting_date >= start_date),
                    (Meeting.meeting_date <= stop_date),
                ),
                and_(
                    (Meeting.meeting_date_end >= start_date),
                    (Meeting.meeting_date_end <= stop_date),
                ),
                and_(
                    (Meeting.meeting_date <= start_date),
                    (Meeting.meeting_date_end >= stop_date),
                ),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name)

        if full_day is not None:
            query = query.filter(Meeting.full_day == full_day)
        if no_recursive:
            query = query.filter(Meeting.recursion_frequency == None)

        return query.all()

    # pylint: disable=R0913
    @classmethod
    def get_by_date_and_location(
            cls, session, calendar, start_date, stop_date, location):
        """ Retrieve the list of meetings in a location between two date.
        We include the start date and exclude the stop date.
        """
        return session.query(cls).filter(
            and_(
                (Meeting.calendar == calendar),
                (Meeting.meeting_date >= start_date),
                (Meeting.meeting_date < stop_date),
                (Meeting.meeting_location == location)
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        ).all()

    @classmethod
    def get_by_date_at_location(
            cls, session, location, start_date, stop_date, full_day=None,
            no_recursive=False):
        """ Retrieve the list of meetings between two date at a specific
        location.
        We include the start date and exclude the stop date.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        query = session.query(
            cls
        ).filter(
            Meeting.meeting_location == location
        ).filter(
            or_(
                and_(
                    (Meeting.meeting_date >= start_date),
                    (Meeting.meeting_date <= stop_date),
                ),
                and_(
                    (Meeting.meeting_date_end >= start_date),
                    (Meeting.meeting_date_end <= stop_date),
                ),
                and_(
                    (Meeting.meeting_date <= start_date),
                    (Meeting.meeting_date_end >= stop_date),
                ),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name)

        if full_day is not None:
            query = query.filter(Meeting.full_day == full_day)
        if no_recursive:
            query = query.filter(Meeting.recursion_frequency == None)

        return query.all()

    @classmethod
    def get_overlaping_meetings(
            cls, session, calendar, start_date, stop_date):
        """ Retrieve the list of meetings overlaping with the date
        provided.
        """
        # new meeting including others
        query1 = session.query(cls).filter(
            and_(
                (Meeting.calendar == calendar),
                (Meeting.meeting_date >= start_date),
                (Meeting.meeting_date_end <= stop_date),
            ))
        # new meeting included in another
        query2 = session.query(cls).filter(
            and_(
                (Meeting.calendar == calendar),
                (Meeting.meeting_date <= start_date),
                (Meeting.meeting_date_end >= stop_date),
            ))
        # new meeting end included in another
        query3 = session.query(cls).filter(
            and_(
                (Meeting.calendar == calendar),
                (Meeting.meeting_date >= stop_date),
                (Meeting.meeting_date_end <= stop_date),
            ))
        # new meeting start included in another
        query4 = session.query(cls).filter(
            and_(
                (Meeting.calendar == calendar),
                (Meeting.meeting_date >= start_date),
                (Meeting.meeting_date_end <= start_date),
            ))

        query = query1.union(query2).union(query3).union(query4).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )

        return list(set(query.all()))

    @classmethod
    def get_at_date(cls, session, calendar, meeting_date, full_day=None):
        """ Retrieve the list of meetings happening at a given date.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        query = session.query(cls).filter(
            and_(
                (Meeting.calendar == calendar),
                (Meeting.meeting_date == meeting_date),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )

        if full_day is not None:
            query = query.filter(Meeting.full_day == full_day)
        return query.all()

    @classmethod
    def get_active_regular_meeting(
            cls, session, calendar, start_date, end_date, full_day=None):
        """ Retrieve the list of recursive meetings occuring before the
        end_date in the specified calendar.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        meetings = session.query(cls).filter(
            and_(
                (Meeting.meeting_date <= end_date),
                (Meeting.recursion_ends >= start_date),
                (Meeting.calendar == calendar),
                (Meeting.recursion_frequency != None),
                (Meeting.recursion_ends != None),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )

        if full_day is not None:
            meetings = meetings.filter(Meeting.full_day == full_day)
        return meetings.all()

    @classmethod
    def get_active_regular_meeting_at_location(
            cls, session, location, start_date, end_date, full_day=None):
        """ Retrieve the list of recursive meetings occuring before the
        end_date at the specified location.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        meetings = session.query(cls).filter(
            and_(
                (Meeting.meeting_date <= end_date),
                (Meeting.recursion_ends >= start_date),
                (Meeting.meeting_location == location),
                (Meeting.recursion_frequency != None),
                (Meeting.recursion_ends != None),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )

        if full_day is not None:
            meetings = meetings.filter(Meeting.full_day == full_day)
        return meetings.all()

    @classmethod
    def get_regular_meeting_at_date(
            cls, session, calendar, end_date, full_day=None):
        """ Retrieve the list of recursive meetings happening at the
        specified end_date.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        meetings_tmp = cls.expand_regular_meetings(
            cls.get_active_regular_meeting(
                session, calendar, end_date, end_date, full_day),
            end_date)
        meetings = []
        for meeting in meetings_tmp:
            if meeting.meeting_date == end_date:
                meetings.append(meeting)
            meetings.sort(key=operator.attrgetter(
                'meeting_date', 'meeting_time_start', 'meeting_name'))
        return meetings

    @classmethod
    def get_active_regular_meeting_by_date(
            cls, session, calendar, start_date, full_day=None):
        """ Retrieve the list of recursive meetings occuring after the
        start_date in the specified calendar.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        meetings = session.query(cls).filter(
            and_(
                (Meeting.recursion_ends >= start_date),
                (Meeting.calendar == calendar),
                (Meeting.recursion_frequency != None),
                (Meeting.recursion_ends != None),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )
        # Apparently the API allows option that are not used
        if full_day is not None:  # pragma: no cover
            meetings = meetings.filter(Meeting.full_day == full_day)
        return meetings.all()

    @classmethod
    def get_active_regular_meeting_by_date_at_location(
            cls, session, location, start_date, full_day=None):
        """ Retrieve the list of recursive meetings occuring after the
        start_date in the specified location.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        meetings = session.query(cls).filter(
            and_(
                (Meeting.recursion_ends >= start_date),
                (Meeting.meeting_location == location),
                (Meeting.recursion_frequency != None),
                (Meeting.recursion_ends != None),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )
        # Apparently the API allows option that are not used
        if full_day is not None:  # pragma: no cover
            meetings = meetings.filter(Meeting.full_day == full_day)
        return meetings.all()

    @classmethod
    def get_regular_meeting_by_date(
            cls, session, calendar, start_date, end_date, full_day=None):
        """ Retrieve the list of recursive meetings happening in between
        the two specified dates.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        meetings = cls.expand_regular_meetings(
            cls.get_active_regular_meeting_by_date(
                session, calendar, start_date, full_day),
            end_date=end_date, start_date=start_date)
        meetings.sort(key=operator.attrgetter(
            'meeting_date', 'meeting_time_start', 'meeting_name'))
        return meetings

    @classmethod
    def get_regular_meeting_by_date_at_location(
            cls, session, location, start_date, end_date, full_day=None):
        """ Retrieve the list of recursive meetings happening in between
        the two specified dates at a specific location.

        :kwarg full_day: Can be True, False or None.  True will
            restrict to only meetings which take up the full day.  False will
            only select meetings which do not take the full day.  None will
            not restrict.  Default to None
        """
        meetings = cls.expand_regular_meetings(
            cls.get_active_regular_meeting_by_date_at_location(
                session, location, start_date, full_day),
            end_date=end_date, start_date=start_date)
        meetings.sort(key=operator.attrgetter(
            'meeting_date', 'meeting_time_start', 'meeting_name'))
        return meetings

    @classmethod
    def get_past_meeting_of_user(cls, session, username, start_date):
        """ Retrieve the list of meetings which specified username
        is among the managers and which date is older than the specified
        one.
        """
        query = session.query(
            cls
        ).filter(
            and_(
                (Meeting.meeting_date < start_date),
                (MeetingsUsers.meeting_id == Meeting.meeting_id),
                (MeetingsUsers.username == username)
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )

        return query.all()

    # pylint: disable=C0103
    @classmethod
    def get_future_single_meeting_of_user(
            cls, session, username, start_date=date.today()):
        """ Retrieve the list of meetings which specified username
        is among the managers and which date is newer or egual than the
        specified one (which defaults to today).
        """
        query = session.query(
            cls
        ).filter(
            and_(
                (Meeting.meeting_date >= start_date),
                (Meeting.recursion_frequency == None),
                (MeetingsUsers.meeting_id == Meeting.meeting_id),
                (MeetingsUsers.username == username),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )

        return query.all()

    # pylint: disable=C0103
    @classmethod
    def get_future_regular_meeting_of_user(
            cls, session, username, start_date=date.today()):
        """ Retrieve the list of meetings which specified username
        is among the managers and which end date is older or egual to
        specified one (which by default is today).
        """
        meetings = session.query(
            cls
        ).filter(
            and_(
                (Meeting.recursion_ends >= start_date),
                (Meeting.recursion_frequency != None),
                (MeetingsUsers.meeting_id == Meeting.meeting_id),
                (MeetingsUsers.username == username),
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        ).all()

        return meetings

    @classmethod
    def get_meeting_with_reminder(
            cls, session, start_date, start_time, stop_time, offset):
        """ Retrieve the list of meetings with a reminder set in
        <offset> hours for the given day and at the specified hour.
        """
        reminders = session.query(Reminder.reminder_id).filter(
            Reminder.reminder_offset == offset).all()
        reminders = [int(item.reminder_id) for item in reminders]
        if not reminders:
            return []
        meetings = session.query(cls).filter(
            and_(
                (Meeting.meeting_date == start_date),
                (Meeting.meeting_time_start >= start_time),
                (Meeting.meeting_time_start < stop_time),
                (Meeting.reminder_id.in_(reminders)))).all()

        # Add recursive meetings
        recursive_meetings = session.query(cls).filter(
            and_(
                (Meeting.meeting_time_start >= start_time),
                (Meeting.meeting_time_start < stop_time),
                (Meeting.recursion_frequency != None),
                (Meeting.recursion_ends >= start_date),
                (Meeting.reminder_id.in_(reminders)))).all()
        for meeting in recursive_meetings:
            meeting_date = meeting.meeting_date
            while meeting_date <= meeting.recursion_ends:
                if meeting_date == start_date:
                    if meeting not in meetings:
                        meetings.append(meeting)
                    break
                meeting_date = meeting_date + timedelta(
                    days=meeting.recursion_frequency)
        meetings.sort(key=operator.attrgetter(
            'meeting_date', 'meeting_time_start', 'meeting_name'))
        return meetings

    @staticmethod
    def expand_regular_meetings(
            meetings_in, start_date=None, end_date=None):
        """ For a given list of meetings, go through all of them and if
        the meeting is recursive, expand the recursion as if they were
        all different meetings.
        The end_date keyword argument allows to stop the process earlier
        allowing to have all recursive meeting up to a certain time
        point.
        The start_date keyword argument allows to only keep the meeting
        from a certain time point.
        """
        meetings = []
        for meeting in meetings_in:
            if not end_date:  # pragma: no cover
                end_date = meeting.recursion_ends
            if meeting.recursion_frequency and meeting.recursion_ends:
                meeting_date = meeting.meeting_date
                cnt = 0
                while meeting_date <= end_date and \
                        meeting_date <= meeting.recursion_ends:
                    recmeeting = meeting.copy()
                    recmeeting.meeting_id = meeting.meeting_id
                    recmeeting.meeting_manager_user = \
                        meeting.meeting_manager_user
                    recmeeting.calendar = meeting.calendar
                    if start_date \
                            and meeting_date >= start_date:
                        recmeeting.meeting_date = \
                            meeting.meeting_date + timedelta(
                                days=meeting.recursion_frequency * cnt)
                        recmeeting.meeting_date_end = \
                            meeting.meeting_date_end + timedelta(
                                days=meeting.recursion_frequency * cnt)
                        meetings.append(recmeeting)
                    elif not start_date:
                        recmeeting.meeting_date = \
                            meeting.meeting_date + timedelta(
                                days=meeting.recursion_frequency * cnt)
                        recmeeting.meeting_date_end = \
                            meeting.meeting_date_end + timedelta(
                                days=meeting.recursion_frequency * cnt)
                        meetings.append(recmeeting)

                    cnt = cnt + 1
                    meeting_date = meeting.meeting_date + timedelta(
                        days=meeting.recursion_frequency * cnt)
            else:
                meetings.append(meeting)
        meetings.sort(key=operator.attrgetter(
            'meeting_date', 'meeting_time_start', 'meeting_name'))
        return meetings

    @classmethod
    def search(cls, session, keyword):
        """ Searches the meetings table to return all the meetings having
        the provided keyword in their name or description.
        """
        query = session.query(
            cls
        ).filter(
            or_(
                cls.meeting_name.ilike(keyword),
                cls.meeting_information.ilike(keyword)
            )
        ).order_by(
            Meeting.meeting_date,
            Meeting.meeting_time_start,
            Meeting.meeting_name
        )

        return query.all()

    @classmethod
    def search_locations(cls, session, keyword):
        """ Searches the meetings table to return all the location having
        the provided keyword in their location.
        """
        query = session.query(
            distinct(cls.meeting_location)
        ).filter(
            cls.meeting_location.ilike(keyword)
        ).order_by(
            cls.meeting_location
        )

        return [el[0] for el in query.all()]

    @classmethod
    def get_locations(cls, session):
        """ Return the list of all the locations where meetings happen.
        """

        query = session.query(
            distinct(cls.meeting_location)
        ).filter(
            cls.meeting_location != None
        ).filter(
            cls.meeting_location != 'None'
        ).filter(
            cls.meeting_location != ''
        ).order_by(
            cls.meeting_location
        )

        return [el[0] for el in query.all()]

    @classmethod
    def clear_from_calendar(cls, session, calendar):
        """ Remove all the meetings associated with the calendar provided.
        """
        query = session.query(
            cls
        ).filter(
            cls.calendar == calendar
        )

        return query.delete()


class Reminder(BASE):
    """ Reminders table.

    Store the information about the reminders that should be sent
    when asked in a meeting.
    """

    __tablename__ = 'reminders'
    reminder_id = Column(Integer, primary_key=True)
    reminder_offset = Column(Enum(
        'H-12', 'H-24', 'H-48', 'H-168', name='reminder_offset'),
        nullable=False)
    reminder_to = Column(String(500), nullable=False)
    reminder_text = Column(Text)

    def __init__(self, reminder_offset, reminder_to, reminder_text):
        """ Constructor instanciating the defaults values. """
        self.reminder_offset = reminder_offset
        self.reminder_to = reminder_to
        self.reminder_text = reminder_text

    def __repr__(self):
        """ Representation of the Reminder object when printed.
        """
        return "<Reminder('%s', '%s')>" % (
            self.reminder_to, self.reminder_offset)

    def save(self, session):
        """ Save the object into the database. """
        session.add(self)

    @classmethod
    def by_id(cls, session, identifier):
        """ Retrieve a Reminder object from the database based on its
        identifier.
        :return None if no calendar matched this identifier.
        """
        return session.query(cls).get(identifier)


if __name__ == '__main__':  # pragma: no cover
    import os
    import ConfigParser
    CONFIG = ConfigParser.ConfigParser()
    if os.path.exists('/etc/fedocal.cfg'):
        CONFIG.readfp(open('/etc/fedocal.cfg'))
    else:
        CONFIG.readfp(open(os.path.join(os.path.dirname(
            os.path.abspath(__file__)),
            '..', 'fedocal.cfg')))
    create_tables(CONFIG.get('fedocal', 'db_url'), True)
