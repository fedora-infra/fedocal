#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
 (c) 2014 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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


'''
Utility script to convert a fedocal-0.3.x database to the fedocal-0.4.0
data model.

Note: It will need the SQLAlchemy database url filled at the top of this
file.

'''
from __future__ import print_function

## These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources


import sys
import os

import sqlalchemy as sa
import sqlalchemy.orm as orm
import sqlalchemy.exc


sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

import fedocal.fedocallib
from fedocal.fedocallib import model


DB_URL_FEDOCAL03 = ''
DB_URL_FEDOCAL04 = ''


class F03Calendars(object):
    pass


class F03Meetings(object):
    pass


class F03Reminders(object):
    pass


def create_session(db_url, debug=False):
    ''' Return a SQLAlchemy session connecting to the provided database.
    This is assuming the db_url provided has the right information.

    '''
    engine = sa.create_engine(db_url, echo=debug)

    metadata = sa.MetaData(engine)

    table = sa.Table('calendars', metadata, autoload=True)
    sa.orm.mapper(F03Calendars, table)

    table = sa.Table('meetings', metadata, autoload=True)
    sa.orm.mapper(F03Meetings, table)

    table = sa.Table('reminders', metadata, autoload=True)
    sa.orm.mapper(F03Reminders, table)

    scopedsession = orm.scoped_session(orm.sessionmaker(bind=engine))
    return scopedsession


def convert_calendars(fed03_sess, fed04_sess):
    ''' Convert the Calendars from fedocal-0.3.x to fedocal-0.4.0.
    '''
    cnt = 0
    for calendar in fed03_sess.query(F03Calendars).all():
        calendarobj = model.Calendar(
            calendar_name=calendar.calendar_name,
            calendar_contact=calendar.calendar_contact,
            calendar_description=calendar.calendar_description,
            calendar_editor_group=calendar.calendar_editor_group,
            calendar_admin_group=calendar.calendar_admin_group,
            calendar_status=calendar.calendar_status
        )
        fed04_sess.add(calendarobj)
        cnt += 1
    fed04_sess.commit()
    print('%s calendars added' % cnt)


def convert_reminders(fed03_sess, fed04_sess):
    ''' Convert the Reminders from fedocal-0.3.x to fedocal-0.4.0.
    '''
    cnt = 0
    for reminder in fed03_sess.query(F03Reminders).all():
        reminderobj = model.Reminder(
            reminder_offset=reminder.reminder_offset,
            reminder_to=reminder.reminder_to,
            reminder_text=reminder.reminder_text,
            )
        reminderobj.reminder_id = reminder.reminder_id
        fed04_sess.add(reminderobj)
        cnt += 1
    fed04_sess.commit()
    print('%s reminders added' % cnt)


def convert_meetings(fed03_sess, fed04_sess):
    ''' Convert the Meetings from fedocal-0.3.x to fedocal-0.4.0.
    '''
    cnt = 0
    for meeting in fed03_sess.query(F03Meetings).all():
        calendarobj = model.Calendar.by_id(
            fed04_sess, meeting.calendar_name)

        if meeting.reminder_id:
            reminderobj = model.Reminder.by_id(
                fed04_sess, meeting.reminder_id)

        # Create the meeting
        meetingobj = model.Meeting(
            meeting_name=meeting.meeting_name,
            meeting_date=meeting.meeting_date,
            meeting_date_end=meeting.meeting_date_end,
            meeting_time_start=meeting.meeting_time_start,
            meeting_time_stop=meeting.meeting_time_stop,
            meeting_information=meeting.meeting_information,
            calendar_name=meeting.calendar_name,
            meeting_timezone=meeting.meeting_timezone,
            reminder_id=meeting.reminder_id,
            meeting_location=meeting.meeting_location,
            recursion_frequency=meeting.recursion_frequency,
            recursion_ends=meeting.recursion_ends,
            full_day=meeting.full_day)
        fed04_sess.add(meetingobj)
        # Add the managers
        meetingobj.add_manager(fed04_sess, meeting.meeting_manager)
        fed04_sess.add(meetingobj)
        fed04_sess.flush()
        cnt += 1
    fed04_sess.commit()
    print('%s meetings added' % cnt)


def main(db_url_fed03, db_url_fed04):
    ''' The methods connect to the two pkgdb database and converts the data
    from one database model to the other.
    '''
    fed03_sess = create_session(db_url_fed03)
    fed04_sess = fedocal.fedocallib.create_session(db_url_fed04)

    convert_calendars(fed03_sess, fed04_sess)
    convert_reminders(fed03_sess, fed04_sess)
    convert_meetings(fed03_sess, fed04_sess)
    fed03_sess.close()
    fed04_sess.close()


if __name__ == '__main__':
    if not DB_URL_FEDOCAL03 or not DB_URL_FEDOCAL04:
        print('You need to set the database(s) URL(s) at the top of this ' \
              'file')
        sys.exit(1)

    main(DB_URL_FEDOCAL03, DB_URL_FEDOCAL04)
