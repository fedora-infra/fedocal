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

from datetime import timedelta
import operator
from model import Meeting


# pylint: disable=R0903
class Week(object):
    """ This class represents a week for in a specific calendar with
    all its meetings.
    """

    def __init__(self, session, calendar, start_date=None):
        """ Constructor, instanciate a week object for a given calendar.
        :arg calendar, the name of the calendar to use.
        :kwarg start_date, the starting date of the week.
        """
        self.session = session
        self.calendar = calendar
        self.start_date = start_date
        self.stop_date = start_date + timedelta(days=6)
        self.meetings = []
        self.full_day_meetings = []
        self.get_meetings()
        self.get_full_day_meetings()

    def get_meetings(self):
        """ Retrieves the list of this week's meeting from the database.
        """
        self.meetings = Meeting.get_by_date(
            self.session, self.calendar, self.start_date, self.stop_date)

        for meeting in Meeting.get_active_regular_meeting(
                self.session, self.calendar,
                self.start_date, self.stop_date):
            for delta in range(0, 7):
                day = self.start_date + timedelta(days=delta)
                if ((meeting.meeting_date - day).days %
                        meeting.recursion_frequency) == 0:
                    if meeting not in self.meetings:
                        self.meetings.append(meeting)
        # Expand the regular meetings so that they appear as meeting
        self.meetings = Meeting.expand_regular_meetings(
            self.meetings, end_date=self.stop_date,
            start_date=self.start_date)
        # Sort the meetings by date, time_start and name
        self.meetings.sort(key=operator.attrgetter(
            'meeting_date', 'meeting_time_start', 'meeting_name'))

    def get_full_day_meetings(self):
        """ Retrieve all the full day meetings for this week. """
        self.full_day_meetings = Meeting.get_by_date(
            self.session, self.calendar, self.start_date,
            self.stop_date, full_day=True)

        for meeting in Meeting.get_active_regular_meeting(
                self.session, self.calendar,
                self.start_date, self.stop_date,
                full_day=True):
            for delta in range(0, 7):
                day = self.start_date + timedelta(days=delta)
                if ((meeting.meeting_date - day).days %
                        meeting.recursion_frequency) == 0:
                    if meeting not in self.full_day_meetings:
                        self.full_day_meetings.append(meeting)
        # Expand the regular meetings so that they appear as meeting
        self.full_day_meetings = Meeting.expand_regular_meetings(
            self.full_day_meetings, end_date=self.stop_date,
            start_date=self.start_date)
        # Sort the meetings by date, time_start and name
        self.full_day_meetings.sort(key=operator.attrgetter(
            'meeting_date', 'meeting_time_start', 'meeting_name'))

    def __repr__(self):
        """ Representation of the Week object when printed.
        """
        return "<Week('%s' from '%s' to '%s')>" % (
            self.calendar.calendar_name,
            self.start_date, self.stop_date)
