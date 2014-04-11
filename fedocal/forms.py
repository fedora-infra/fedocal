#-*- coding: utf-8 -*-

"""
 (c) 2012-2014 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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
    if isinstance(field.data, time):  # pragma: no cover
        return
    import re
    if not re.match(r'\d?\d:\d\d?', field.data):
        raise wtforms.ValidationError('Time must be of type "HH:MM"')
    time_data = field.data.split(':')
    try:
        field.data = time(int(time_data[0]), int(time_data[1]))
    except ValueError:
        raise wtforms.ValidationError('Time must be of type "HH:MM"')

def validate_meeting_location(form,field):
    """ Validate if location doesn't contain #irc-chan format
        More info: https://fedorahosted.org/fedocal/ticket/118
    """
    if field.data.count('#') > 0:
        raise wtforms.ValidationError('Please use channel@server format!')

class AddCalendarForm(wtf.Form):
    """ Form used to create a new calendar. """
    calendar_name = wtforms.TextField(
        'Calendar <span class="error">*</span>',
        [wtforms.validators.Required()])
    calendar_contact = wtforms.TextField(
        'Contact email <span class="error">*</span>',
        [wtforms.validators.Required()])
    calendar_description = wtforms.TextField('Description')
    calendar_editor_groups = wtforms.TextField('Editor groups')
    calendar_admin_groups = wtforms.TextField('Admin groups')
    calendar_status = wtforms.SelectField(
        'Status <span class="error">*</span>',
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
        'Calendar <span class="error">*</span>',
        [wtforms.validators.Required()],
        choices=[])

    meeting_name = wtforms.TextField(
        'Meeting name <span class="error">*</span>',
        [wtforms.validators.Required()])

    meeting_date = wtforms.DateField(
        'Date <span class="error">*</span>',
        [wtforms.validators.Required()])

    meeting_date_end = wtforms.DateField(
        'End date',
        [wtforms.validators.optional()])

    meeting_time_start = wtforms.TextField(
        'Start time <span class="error">*</span>',
        [wtforms.validators.Required(), validate_time])

    meeting_time_stop = wtforms.TextField(
        'Stop time <span class="error">*</span>',
        [wtforms.validators.Required(), validate_time])

    meeting_timezone = wtforms.SelectField(
        'Time zone <span class="error">*</span>',
        [wtforms.validators.Required()],
        choices=[(tzone, tzone) for tzone in common_timezones])

    wiki_link = wtforms.TextField('More information URL')

    comanager = wtforms.TextField('Co-manager')

    information = wtforms.TextAreaField('Information')

    meeting_location = wtforms.TextField(
        'Location',
        [wtforms.validators.optional(), validate_meeting_location]
    )

    # Recursion
    frequency = wtforms.SelectField(
        'Repeat every',
        [wtforms.validators.optional()],
        choices=[
            ('', ''),
            ('7', '7 days'),
            ('14', '14 days'),
            ('21', '3 weeks'),
            ('28', '4 weeks'),
        ]
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

            self.calendar_name.data = meeting.calendar_name
            self.meeting_name.data = meeting.meeting_name
            self.meeting_date.data = meeting.meeting_date
            self.meeting_date_end.data = meeting.meeting_date_end
            self.meeting_time_start.data = meeting.meeting_time_start.strftime(
                '%H:%M')
            self.meeting_time_stop.data = meeting.meeting_time_stop.strftime(
                '%H:%M')
            self.meeting_timezone.data = meeting.meeting_timezone
            self.information.data = meeting.meeting_information
            meeting_manager = ','.join(meeting.meeting_manager)
            self.comanager.data = meeting_manager
            self.meeting_location.data = meeting.meeting_location
            self.frequency.data = str(meeting.recursion_frequency)
            self.end_repeats.data = meeting.recursion_ends
            self.full_day.data = meeting.full_day
            if meeting.reminder_id:  # pragma: no cover
                self.remind_when.data = meeting.reminder.reminder_offset
                self.remind_who.data = meeting.reminder.reminder_to


class DeleteMeetingForm(wtf.Form):
    """ Form used to delete a meeting. """
    confirm_delete = wtforms.BooleanField(
        'Yes I want to delete this meeting')
    confirm_futher_delete = wtforms.BooleanField(
        'Yes, I want to delete all futher meetings.')
    from_date = wtforms.DateField(
        'Date from which to remove the meeting')


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
    ics_file = wtforms.FileField(
        'ics file <span class="error">*</span>',
        [wtforms.validators.Required()])
