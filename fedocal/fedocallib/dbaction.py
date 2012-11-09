# -*- coding: utf-8 -*-

"""
dbaction - Simple file containing all the methods to add/edit and remove
            object from the database.

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
import model


def add_reminder(session, remind_when, remind_who, reminder_text=None):
    """ Logic to add a reminder to the database.
    """
    reminder = model.Reminder(
                        reminder_offset=remind_when,
                        reminder_to=remind_who,
                        reminder_text=None)
    reminder.save(session)
    session.flush()
    return reminder


# pylint: disable=R0913,R0914
def add_meeting(session, meeting_name, meeting_manager,
        meeting_date, meeting_date_end,
        meeting_time_start, meeting_time_stop,
        meeting_information, calendarobj, reminder_id=None,
        meeting_region=None,
        recursion_frequency=None, recursion_ends=None):
    """ Logic to add a meeting to the database.
    """

    if not recursion_frequency:
        recursion_frequency = None
    if not recursion_ends and recursion_frequency:
        recursion_ends = date(2025, 12, 31)

    if not calendarobj.calendar_regional_meetings or not meeting_region:
        meeting_region = None

    if not meeting_date_end:
        meeting_date_end = meeting_date

    meeting = model.Meeting(
        meeting_name=meeting_name,
        meeting_manager=meeting_manager,
        meeting_date=meeting_date,
        meeting_date_end=meeting_date_end,
        meeting_time_start=meeting_time_start.time(),
        meeting_time_stop=meeting_time_stop.time(),
        meeting_information=meeting_information,
        calendar_name=calendarobj.calendar_name,
        reminder_id=reminder_id,
        meeting_region=meeting_region,
        recursion_frequency=recursion_frequency,
        recursion_ends=recursion_ends)
    meeting.save(session)
    session.flush()
