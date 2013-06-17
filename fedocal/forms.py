#-*- coding: UTF-8 -*-

"""
 (c) 2012 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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

import flask
from flask.ext import wtf
from datetime import time
from datetime import datetime

from wtforms import ValidationError

import fedocallib


def validate_time(form, field):
    """ Validate if the data set in the given field is a valid time. """
    import re
    if not re.match(r'\d?\d:\d\d?', field.data):
        raise ValidationError('Time must be of type "HH:MM"')
    time_data = field.data.split(':')
    try:
        field.data = time(int(time_data[0]), int(time_data[1]))
    except ValueError:
        raise ValidationError('Time must be of type "HH:MM"')


class AddCalendarForm(wtf.Form):
    """ Form used to create a new calendar. """
    calendar_name = wtf.TextField(
        'Calendar',
        [wtf.validators.Required()])
    calendar_contact = wtf.TextField(
        'Contact email',
        [wtf.validators.Required()])
    calendar_description = wtf.TextField('Description')
    calendar_manager_groups = wtf.TextField('Manager groups')
    calendar_admin_groups = wtf.TextField('Admin groups')
    calendar_multiple_meetings = wtf.BooleanField(
        'Agenda can have multiple meetings on the same day?')
    calendar_regional_meetings = wtf.BooleanField(
        'Meetings can be regional?')

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        if a calendar is set using the calendar keyword, then fill the
        value of the form with the value from the Calendar object.
        """
        super(AddCalendarForm, self).__init__(*args, **kwargs)
        if 'calendar' in kwargs:
            calendar = kwargs['calendar']

            self.calendar_name.data = calendar.calendar_name
            self.calendar_contact.data = calendar.calendar_contact
            self.calendar_description.data = calendar.calendar_description
            self.calendar_manager_groups.data = \
                calendar.calendar_manager_group
            self.calendar_admin_groups.data = \
                calendar.calendar_admin_group
            self.calendar_multiple_meetings.data = bool(
                calendar.calendar_multiple_meetings)
            self.calendar_regional_meetings.data = bool(
                calendar.calendar_regional_meetings)


class AddMeetingForm(wtf.Form):
    """ Form used to create a new meeting. """
    meeting_name = wtf.TextField(
        'Meeting name',
        [wtf.validators.Required()])

    meeting_date = wtf.DateField('Date', [wtf.validators.Required()])
    meeting_date_end = wtf.DateField(
        'End date',
        [wtf.validators.optional()])

    meeting_time_start = wtf.TextField(
        'Start time',
        [wtf.validators.Required(), validate_time])

    meeting_time_stop = wtf.TextField(
        'Stop time',
        [wtf.validators.Required(), validate_time])

    comanager = wtf.TextField('Co-manager')

    information = wtf.TextAreaField('Information')

    meeting_region = wtf.SelectField(
        'Region',
        [wtf.validators.optional()],
        choices=[('APAC', 'APAC'),
                 ('EMEA', 'EMEA'),
                 ('LATAM', 'LATAM'),
                 ('NA', 'NA')]
    )

    # Recursion
    frequency = wtf.SelectField(
        'Repeat every',
        [wtf.validators.optional()],
        choices=[('', ''),
                 ('7', '7 days'),
                 ('14', '14 days')]
    )
    end_repeats = wtf.DateField('End date', [wtf.validators.optional()])

    # Recursive edit
    recursive_edit = wtf.BooleanField('Yes I want to edit all the meetings')

    # Reminder
    remind_when = wtf.SelectField(
        'Send reminder',
        [wtf.validators.optional()],
        choices=[('', ''),
                 ('H-12', '12 hours before'),
                 ('H-24', '1 day before'),
                 ('H-48', '2 days before'),
                 ('H-168', '7 days before'),
                 ]
    )
    remind_who = wtf.TextField(
        'Send reminder to',
        [wtf.validators.Email(), wtf.validators.optional()])

    # Full day
    full_day = wtf.BooleanField('Full day meeting')

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        if a meeting is set using the meeting keyword, then fill the
        value of the form with the value from the Meeting object.
        """
        super(AddMeetingForm, self).__init__(*args, **kwargs)
        if 'meeting' in kwargs:
            meeting = kwargs['meeting']
            tzone = 'UTC'
            if 'tzone' in kwargs:
                tzone = kwargs['tzone']

            # Convert time to user's timezone
            startdt = datetime(
                meeting.meeting_date.year,
                meeting.meeting_date.month,
                meeting.meeting_date.day,
                meeting.meeting_time_start.hour,
                meeting.meeting_time_start.minute, 0)
            stopdt = datetime(
                meeting.meeting_date.year,
                meeting.meeting_date.month,
                meeting.meeting_date.day,
                meeting.meeting_time_stop.hour,
                meeting.meeting_time_stop.minute, 0)

            startdt = fedocallib.convert_time(startdt, 'UTC', tzone)
            stopdt = fedocallib.convert_time(stopdt, 'UTC', tzone)

            self.meeting_name.data = meeting.meeting_name
            self.meeting_date.data = startdt.date()
            self.meeting_date_end.data = meeting.meeting_date_end
            self.meeting_time_start.data = startdt.time().strftime('%H:%M')
            self.meeting_time_stop.data = stopdt.time().strftime('%H:%M')
            self.information.data = meeting.meeting_information
            # You are not allowed to remove yourself from the managers.
            meeting_manager = meeting.meeting_manager.replace(
                '%s,' % flask.g.fas_user.username, '')
            self.comanager.data = meeting_manager
            self.meeting_region.data = meeting.meeting_region
            self.frequency.data = meeting.recursion_frequency
            self.end_repeats.data = meeting.recursion_ends
            self.full_day.data = meeting.full_day
            if meeting.reminder_id:
                self.remind_when.data = meeting.reminder.reminder_offset
                self.remind_who.data = meeting.reminder.reminder_to


class DeleteMeetingForm(wtf.Form):
    """ Form used to delete a meeting. """
    confirm_delete = wtf.BooleanField('Yes I want to delete this meeting')
    confirm_futher_delete = wtf.BooleanField(
        'Yes, I want to delete all futher meetings.')


class DeleteCalendarForm(wtf.Form):
    """ Form used to delete a calendar. """
    confirm_delete = wtf.BooleanField('Yes I want to delete this calendar')


class LoginForm(wtf.Form):
    """ Form to log in the application. """
    username = wtf.TextField('Username', [wtf.validators.Required()])
    password = wtf.PasswordField('Password', [wtf.validators.Required()])
