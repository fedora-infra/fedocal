#-*- coding: utf-8 -*-

"""
 (c) 2012-2013 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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

from pytz import common_timezones

import wtforms

import fedocal.fedocallib as fedocallib


def validate_time(form, field):
    """ Validate if the data set in the given field is a valid time. """
    if isinstance(field.data, time):
        return
    import re
    if not re.match(r'\d?\d:\d\d?', field.data):
        raise wtforms.ValidationError('Time must be of type "HH:MM"')
    time_data = field.data.split(':')
    try:
        field.data = time(int(time_data[0]), int(time_data[1]))
    except ValueError:
        raise wtforms.ValidationError('Time must be of type "HH:MM"')


class AddCalendarForm(wtf.Form):
    """ Form used to create a new calendar. """
    calendar_name = wtforms.TextField(
        'Calendar',
        [wtforms.validators.Required()])
    calendar_contact = wtforms.TextField(
        'Contact email',
        [wtforms.validators.Required()])
    calendar_description = wtforms.TextField('Description')
    calendar_editor_groups = wtforms.TextField('Editor groups')
    calendar_admin_groups = wtforms.TextField('Admin groups')
    calendar_status = wtforms.SelectField(
        'Status',
        [wtforms.validators.Required()],
        choices=[]
    )

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        if a calendar is set using the calendar keyword, then fill the
        value of the form with the value from the Calendar object.
        """
        super(AddCalendarForm, self).__init__(*args, **kwargs)
        if 'status' in kwargs:
            self.calendar_status.choices = [
                (status.status, status.status)
                for status in kwargs['status']
            ]

        if 'calendar' in kwargs:
            calendar = kwargs['calendar']

            self.calendar_name.data = calendar.calendar_name
            self.calendar_contact.data = calendar.calendar_contact
            self.calendar_description.data = calendar.calendar_description
            self.calendar_editor_groups.data = \
                calendar.calendar_editor_group
            self.calendar_admin_groups.data = \
                calendar.calendar_admin_group
            self.calendar_status.data = calendar.calendar_status


class AddMeetingForm(wtf.Form):
    """ Form used to create a new meeting. """
    calendar_name = wtforms.SelectField(
        'Calendar',
        [wtforms.validators.Required()],
        choices=[])

    meeting_name = wtforms.TextField(
        'Meeting name',
        [wtforms.validators.Required()])

    meeting_date = wtforms.DateField(
        'Date',
        [wtforms.validators.Required()])

    meeting_date_end = wtforms.DateField(
        'End date',
        [wtforms.validators.optional()])

    meeting_time_start = wtforms.TextField(
        'Start time',
        [wtforms.validators.Required(), validate_time])

    meeting_time_stop = wtforms.TextField(
        'Stop time',
        [wtforms.validators.Required(), validate_time])

    meeting_timezone = wtforms.SelectField(
        'Time zone',
        [wtforms.validators.Required()],
        choices=[(tzone, tzone) for tzone in common_timezones])

    comanager = wtforms.TextField('Co-manager')

    information = wtforms.TextAreaField('Information')

    meeting_location = wtforms.TextField(
        'Location',
        [wtforms.validators.optional()]
    )

    # Recursion
    frequency = wtforms.SelectField(
        'Repeat every',
        [wtforms.validators.optional()],
        choices=[('', ''),
                 ('7', '7 days'),
                 ('14', '14 days')]
    )
    end_repeats = wtforms.DateField(
        'End date',
        [wtforms.validators.optional()])

    # Reminder
    remind_when = wtforms.SelectField(
        'Send reminder',
        [wtforms.validators.optional()],
        choices=[('', ''),
                 ('H-12', '12 hours before'),
                 ('H-24', '1 day before'),
                 ('H-48', '2 days before'),
                 ('H-168', '7 days before'),
                 ]
    )
    remind_who = wtforms.TextField(
        'Send reminder to',
        [wtforms.validators.Email(), wtforms.validators.optional()])

    # Full day
    full_day = wtforms.BooleanField('Full day meeting')

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        if a meeting is set using the meeting keyword, then fill the
        value of the form with the value from the Meeting object.
        """
        super(AddMeetingForm, self).__init__(*args, **kwargs)
        if 'timezone' in kwargs:
            self.meeting_timezone.data = kwargs['timezone']

        if 'calendars' in kwargs:
            calendars = kwargs['calendars']
            self.calendar_name.choices = [
                (calendar.calendar_name, calendar.calendar_name)
                for calendar in calendars
            ]

        if 'meeting' in kwargs:
            meeting = kwargs['meeting']
            tzone = 'UTC'
            if 'timezone' in kwargs:
                tzone = kwargs['timezone']

            # Convert time to user's timezone
            startdt = datetime(
                meeting.meeting_date.year,
                meeting.meeting_date.month,
                meeting.meeting_date.day,
                meeting.meeting_time_start.hour,
                meeting.meeting_time_start.minute, 0)
            stopdt = datetime(
                meeting.meeting_date_end.year,
                meeting.meeting_date_end.month,
                meeting.meeting_date_end.day,
                meeting.meeting_time_stop.hour,
                meeting.meeting_time_stop.minute, 0)

            startdt = fedocallib.convert_time(startdt, 'UTC', tzone)
            stopdt = fedocallib.convert_time(stopdt, 'UTC', tzone)

            self.calendar_name.data = meeting.calendar_name
            self.meeting_name.data = meeting.meeting_name
            self.meeting_date.data = startdt.date()
            self.meeting_date_end.data = meeting.meeting_date_end
            self.meeting_time_start.data = startdt.time().strftime('%H:%M')
            self.meeting_time_stop.data = stopdt.time().strftime('%H:%M')
            self.meeting_timezone.data = meeting.meeting_timezone
            self.information.data = meeting.meeting_information
            # You are not allowed to remove yourself from the managers.
            meeting_manager = meeting.meeting_manager.replace(
                '%s,' % flask.g.fas_user.username, '')
            self.comanager.data = meeting_manager
            self.meeting_location.data = meeting.meeting_location
            self.frequency.data = str(meeting.recursion_frequency)
            self.end_repeats.data = meeting.recursion_ends
            self.full_day.data = meeting.full_day
            if meeting.reminder_id:
                self.remind_when.data = meeting.reminder.reminder_offset
                self.remind_who.data = meeting.reminder.reminder_to


class DeleteMeetingForm(wtf.Form):
    """ Form used to delete a meeting. """
    confirm_delete = wtforms.BooleanField(
        'Yes I want to delete this meeting')
    confirm_futher_delete = wtforms.BooleanField(
        'Yes, I want to delete all futher meetings.')


class DeleteCalendarForm(wtf.Form):
    """ Form used to delete a calendar. """
    confirm_delete = wtforms.BooleanField(
        'Yes I want to delete this calendar')


class ClearCalendarForm(wtf.Form):
    """ Form used to delete a calendar. """
    confirm_delete = wtforms.BooleanField(
        'Yes I want to clear this calendar')


class UploadIcsForm(wtf.Form):
    ''' Form to upload an ics file into a calendar. '''
    ics_file = wtf.FileField(
        'ics file <span class="error">*</span>',
        [wtf.validators.Required()])
