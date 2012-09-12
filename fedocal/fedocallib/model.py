# -*- coding: utf-8 -*-

"""
model - an object mapper to a SQL database representation of the data
        stored in this project.

Copyright (C) 2012 Pierre-Yves Chibon
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

from datetime import datetime
from datetime import date

from sqlalchemy import (
    create_engine,
    Column,
    Date,
    distinct,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    Time,
    UniqueConstraint,
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import relation as relationship
from sqlalchemy.orm.exc import NoResultFound
from sqlalchemy.sql import and_

BASE = declarative_base()


def create_tables(db_url, debug=False):
    """ Create the tables in the database using the information from the
    url obtained.

    :arg db_url, URL used to connect to the database. The URL contains
    information with regards to the database engine, the host to connect
    to, the user and password and the database name.
      ie: <engine>://<user>:<password>@<host>/<dbname>
    :arg debug, a boolean specifying wether we should have the verbose
    output of sqlalchemy or not.
    :return a session that can be used to query the database.
    """
    engine = create_engine(db_url, echo=debug)
    BASE.metadata.create_all(engine)
    sessionmak = sessionmaker(bind=engine)
    return sessionmak()


class Calendar(BASE):
    """ Calendara table.

    Define the calendar available in this application.
    """

    __tablename__ = 'calendars'
    calendar_name = Column(String(80), primary_key=True)
    calendar_description = Column(String(500))
    calendar_manager_group = Column(String(100))  # 3 groups (3*32)

    def __init__(self, calendar_name, calendar_description,
        calendar_manager_group):
        """ Constructor instanciating the defaults values. """
        self.calendar_name = calendar_name
        self.calendar_description = calendar_description
        self.calendar_manager_group = calendar_manager_group

    def __repr__(self):
        """ Representation of the Calendar object when printed.
        """
        return "<Calendar('%s')>" % (self.calendar_name)

    def save(self, session):
        """ Save the object into the database. """
        session.add(self)

    @classmethod
    def by_id(cls, session, identifier):
        """ Retrieve a Calendar object from the database based on its
        identifier.
        :return None if no calendar matched this identifier.
        """
        try:
            return session.query(cls).get(identifier)
        except NoResultFound:
            return None

    @classmethod
    def get_manager_groups(cls, session, identifier):
        """ Return the list of managers for a given meeting.
        """
        calendar = Calendar.by_id(session, identifier)
        if not calendar or not calendar.calendar_manager_group:
            groups = []
        else:
            groups = [item.strip()
                for item in calendar.calendar_manager_group.split(',')]
        return groups

    @classmethod
    def get_all(cls, session):
        """ Retrieve all the Calendar available."""
        try:
            return session.query(cls).all()
        except NoResultFound:
            return None


class Meeting(BASE):
    """ Meetings table.

    Store the information about the meetings set in the application.
    """

    __tablename__ = 'meetings'
    meeting_id = Column(Integer, primary_key=True)
    meeting_name = Column(String(200), nullable=False)
    calendar_name = Column(String(80), ForeignKey('calendars.calendar_name'),
        nullable=False)
    calendar = relationship("Calendar")
    meeting_manager = Column(String(160))  #  5 person max (32 * 5)
    meeting_date = Column(Date, default=datetime.utcnow().date())
    meeting_time_start = Column(Time, default=datetime.utcnow().time())
    meeting_time_stop = Column(Time, default=datetime.utcnow().time())
    reminder_id = Column(Integer, ForeignKey('reminders.reminder_id'),
        nullable=True)
    reminder = relationship("Reminder")
    recursion_id = Column(Integer, ForeignKey('recursivity.recursion_id'),
        nullable=True)
    recursion = relationship("Recursive")

    __table_args__ = (
            UniqueConstraint('calendar_name', 'meeting_date',
                'meeting_time_start'),
            )

    def __init__(self, meeting_name, meeting_manager,
        meeting_date, meeting_time_start, meeting_time_stop,
        calendar_name, reminder_id, recursion_id):
        """ Constructor instanciating the defaults values. """
        self.meeting_name = meeting_name
        self.meeting_manager = meeting_manager
        self.meeting_date = meeting_date
        self.meeting_time_start = meeting_time_start
        self.meeting_time_stop = meeting_time_stop
        self.calendar_name = calendar_name
        self.reminder_id = reminder_id
        self.recursion_id = recursion_id

    def __repr__(self):
        """ Representation of the Reminder object when printed.
        """
        return "<Meeting('%s', '%s')>" % (self.calendar,
            self.meeting_name)

    def save(self, session):
        """ Save the object into the database. """
        session.add(self)

    def delete(self, session):
        """ Remove the object into the database. """
        session.delete(self)

    def copy(self):
        """ Return a new Meeting object containing the same information
        as the present one.
        """
        return Meeting(self.meeting_name, self.meeting_manager,
            self.meeting_date, self.meeting_time_start,
            self.meeting_time_stop, self.calendar_name, self.reminder_id,
            self.recursion_id)

    @classmethod
    def by_id(cls, session, identifier):
        """ Retrieve a Meeting object from the database based on its
        identifier.
        :return None if no calendar matched this identifier.
        """
        try:
            return session.query(cls).get(identifier)
        except NoResultFound:
            return None

    @classmethod
    def get_future_meetings_of_recursion(cls, session, meeting):
        """ Return the list of meetings which are in the future and
        associated with a specific recursivity.
        """
        try:
            return session.query(cls).filter(and_
                (Meeting.calendar == meeting.calendar),
                (Meeting.meeting_date >= meeting.meeting_date),
                (Meeting.recursion == meeting.recursion)).all()
        except NoResultFound:
            return None

    @classmethod
    def get_managers(cls, session, identifier):
        """ Return the list of managers for a given meeting.
        """
        meeting = Meeting.by_id(session, identifier)
        if not meeting or not meeting.meeting_manager:
            managers = []
        else:
            if ',' in meeting.meeting_manager:
                managers = [item.strip()
                    for item in meeting.meeting_manager.split(',')]
            else:
                managers = [meeting.meeting_manager]
        return managers

    @classmethod
    def get_by_date(cls, session, calendar, start_date, stop_date):
        """ Retrieve the list of meetings between two date.
        We include the start date and exclude the stop date.
        """
        try:
            return session.query(cls).filter(and_
                (Meeting.calendar == calendar),
                (Meeting.meeting_date >= start_date),
                (Meeting.meeting_date < stop_date)).all()
        except NoResultFound:
            return None

    @classmethod
    def get_by_time(cls, session, calendar, date, start_time, stop_time):
        """ Retrieve the list of meetings for a given date and between
        two times.
        """
        try:
            return session.query(cls).filter(and_
                (Meeting.calendar == calendar),
                (Meeting.meeting_date == date),
                (Meeting.meeting_time_start >= start_time),
                (Meeting.meeting_time_stop <= stop_time)).all()
        except NoResultFound:
            return None

    @classmethod
    def get_past_meeting_of_user(cls, session, username, start_date):
        """ Retrieve the list of meetings which specified username
        is among the managers and which date is older than the specified
        one.
        """
        try:
            return session.query(cls).filter(and_
                (Meeting.meeting_date < start_date),
                (Meeting.meeting_manager.like('%%%s%%' % username))).all()
        except NoResultFound:
            return None

    @classmethod
    def get_future_single_meeting_of_user(cls, session, username,
        start_date):
        """ Retrieve the list of meetings which specified username
        is among the managers and which date is newer or egual than the
        specified one.
        """
        try:
            return session.query(cls).filter(and_
                (Meeting.meeting_date >= start_date),
                (Meeting.recursion == None),
                (Meeting.meeting_manager.like('%%%s%%' % username))).all()
        except NoResultFound:
            return None

    @classmethod
    def get_future_regular_meeting_of_user(cls, session, username,
        start_date):
        """ Retrieve the list of meetings which specified username
        is among the managers and which date is newer or egual than the
        specified one.
        """
        try:
            recursive_meetings = session.query(distinct(cls.recursion_id)
                ).filter(and_
                    (Meeting.meeting_date >= start_date),
                    (Meeting.recursion != None),
                    (Meeting.meeting_manager.like('%%%s%%' % username))
                ).all()
            meetings = []
            for recursive_meeting in recursive_meetings:
                meetings.append(session.query(cls).filter(and_
                    (Meeting.meeting_date >= start_date),
                    (Meeting.recursion_id == recursive_meeting[0])
                    ).order_by(Meeting.meeting_date).limit(1).one())
            return meetings
        except NoResultFound:
            return None


class Recursive(BASE):
    """ recursivity table.

    Store the information about the recursivity that can be set to a
    meeting.
    """

    __tablename__ = 'recursivity'
    recursion_id = Column(Integer, primary_key=True)
    recursion_frequency = Column(Enum('7', '14'), nullable=False)
    recursion_start = Column(Date, nullable=False,
        default=datetime.utcnow().date())
    recursion_ends = Column(Date,
        default=date(2121, 12, 31), nullable=False)

    def __init__(self, recursion_frequency, recursion_ends):
        """ Constructor instanciating the defaults values. """
        self.recursion_frequency = recursion_frequency
        self.recursion_ends = recursion_ends

    def __repr__(self):
        """ Representation of the Reminder object when printed.
        """
        return "<Recursion(From '%s' to '%s' every '%s')>" % (
            self.recursion_start, self.recursion_ends,
            self.recursion_frequency)

    def save(self, session):
        """ Save the object into the database. """
        session.add(self)

    @classmethod
    def by_id(cls, session, identifier):
        """ Retrieve a Reminder object from the database based on its
        identifier.
        :return None if no calendar matched this identifier.
        """
        try:
            return session.query(cls).get(identifier)
        except NoResultFound:
            return None


class Reminder(BASE):
    """ Reminders table.

    Store the information about the reminders that should be sent
    when asked in a meeting.
    """

    __tablename__ = 'reminders'
    reminder_id = Column(Integer, primary_key=True)
    reminder_offset = Column(Enum('H-12', 'H-24', 'H-48', 'H-168'),
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
        return "<Reminder('%s', '%s')>" % (self.reminder_to,
            self.reminder_offset)

    def save(self, session):
        """ Save the object into the database. """
        session.add(self)

    @classmethod
    def by_id(cls, session, identifier):
        """ Retrieve a Reminder object from the database based on its
        identifier.
        :return None if no calendar matched this identifier.
        """
        try:
            return session.query(cls).get(identifier)
        except NoResultFound:
            return None


if __name__ == '__main__':
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
