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

from datetime import date
from datetime import timedelta
from model import Meeting


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
        self.stop_date = start_date + timedelta(days=7)
        self.meetings = []
        self.get_meetings()

    def get_meetings(self):
        """ Retrieves the list of this week meeting from the database.
        """
        self.meetings = Meeting.get_by_date(self.session, self.calendar,
            self.start_date, self.stop_date)

        for meeting in Meeting.get_active_regular_meeting(self.session,
            self.start_date, self.stop_date):
            for delta in range(0, 7):
                day = self.start_date + timedelta(days=delta)
                if ((meeting.meeting_date - day).days %
                        meeting.recursion_frequency) == 0:
                    if meeting not in self.meetings:
                        self.meetings.append(meeting)

    def __repr__(self):
        """ Representation of the Week object when printed.
        """
        return "<Week('%s' from '%s' to '%s')>" % (
            self.calendar.calendar_name,
            self.start_date, self.stop_date)
