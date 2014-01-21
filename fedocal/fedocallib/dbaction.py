# -*- coding: utf-8 -*-

"""
dbaction - Simple file containing all the methods to add/edit and remove
            object from the database.

Copyright (C) 2012-2013 Pierre-Yves Chibon
Author: Pierre-Yves Chibon <pingou@pingoured.fr>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.
See http://www.gnu.org/copyleft/gpl.html  for the full text of the
license.
"""

from datetime import date
import model


def add_reminder(session, remind_when, remind_who, reminder_text=None):
    """ Logic to add a reminder to the database.
    """
    reminder = model.Reminder(reminder_offset=remind_when,
                              reminder_to=remind_who,
                              reminder_text=reminder_text)
    reminder.save(session)
    session.flush()
    return reminder


# pylint: disable=R0913,R0914
def add_meeting(
        session,
        meeting_name,
        meeting_manager,
        meeting_date,
        meeting_date_end,
        meeting_time_start,
        meeting_time_stop,
        meeting_information,
        calendarobj,
        meeting_timezone='UTC',
        reminder_id=None,
        meeting_location=None,
        recursion_frequency=None,
        recursion_ends=None,
        full_day=False):
    """ Logic to add a meeting to the database.
    """

    if not recursion_frequency:
        recursion_frequency = None
    if not recursion_ends and recursion_frequency:
        recursion_ends = date(2025, 12, 31)

    # Unless we test directly dbaction we will never hit this as
    # fedocallib.add_meeting already covers it
    if not meeting_date_end:  # pragma: no cover
        meeting_date_end = meeting_date

    meeting = model.Meeting(
        meeting_name=meeting_name,
        meeting_date=meeting_date,
        meeting_date_end=meeting_date_end,
        meeting_time_start=meeting_time_start.time(),
        meeting_time_stop=meeting_time_stop.time(),
        meeting_timezone=meeting_timezone,
        meeting_information=meeting_information,
        calendar_name=calendarobj.calendar_name,
        reminder_id=reminder_id,
        meeting_location=meeting_location,
        recursion_frequency=recursion_frequency,
        recursion_ends=recursion_ends,
        full_day=full_day)
    meeting.add_manager(session, meeting_manager)
    meeting.save(session)
    session.flush()
    return meeting
