# -*- coding: utf-8 -*-

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

import re
from datetime import time
from fedocal.fedocal_babel import lazy_gettext as _
from fedocal import i18nforms

import email_validator
from pytz import common_timezones

import wtforms


def validate_time(form, field):
    """ Validate if the data set in the given field is a valid time. """
    if isinstance(field.data, time):  # pragma: no cover
        return
    if not re.match(r'\d?\d:\d\d?', field.data):
        raise wtforms.ValidationError(
            _('Time must be of type "HH:MM"')
        )
    time_data = field.data.split(':')
    try:
        field.data = time(int(time_data[0]), int(time_data[1]))
    except ValueError:
        raise wtforms.ValidationError(
            _('Time must be of type "HH:MM"')
        )


def validate_meeting_location(form, field):
    """ Validate if location doesn't contain #irc-chan format
        More info: https://fedorahosted.org/fedocal/ticket/118
    """
    if '#' in field.data.strip():
        raise wtforms.ValidationError(
            _('Please use channel@server format!')
        )


def validate_multi_email(form, field):
    """ Raises an exception if the content of the field does not contain one or
        more email.
    """
    data = field.data.replace(' ', ',')
    for entry in data.split(','):
        entry = entry.strip()
        if not entry:
            continue
        try:
            email_validator.validate_email(entry)
        except email_validator.EmailNotValidError as e:
            # email is not valid, exception message is human-readable
            raise wtforms.ValidationError(str(e))


class AddCalendarForm(i18nforms.Form):
    """ Form used to create a new calendar. """
    calendar_name = wtforms.TextField(
        _('Calendar'),
        [wtforms.validators.DataRequired()])
    calendar_contact = wtforms.TextField(
        _('Contact email'),
        [wtforms.validators.DataRequired()])
    calendar_description = wtforms.TextField(_('Description'))
    calendar_editor_groups = wtforms.TextField(_('Editor groups'))
    calendar_admin_groups = wtforms.TextField(_('Admin groups'))
    calendar_status = wtforms.SelectField(
        _('Status'),
        [wtforms.validators.DataRequired()],
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


class AddMeetingForm(i18nforms.Form):
    """ Form used to create a new meeting. """
    calendar_name = wtforms.SelectField(
        _('Calendar'),
        [wtforms.validators.DataRequired()],
        choices=[])

    meeting_name = wtforms.TextField(
        _('Meeting name'),
        [wtforms.validators.DataRequired()])

    meeting_date = wtforms.DateField(
        _('Date'),
        [wtforms.validators.DataRequired()])

    meeting_date_end = wtforms.DateField(
        _('End date'),
        [wtforms.validators.optional()])

    meeting_time_start = wtforms.TextField(
        _('Start time'),
        [wtforms.validators.DataRequired(), validate_time])

    meeting_time_stop = wtforms.TextField(
        _('Stop time'),
        [wtforms.validators.DataRequired(), validate_time])

    meeting_timezone = wtforms.SelectField(
        _('Time zone'),
        [wtforms.validators.DataRequired()],
        choices=[(tzone, tzone) for tzone in sorted(common_timezones)])

    wiki_link = wtforms.TextField(_('More information URL'))

    comanager = wtforms.TextField(_('Co-manager'))

    information = wtforms.TextAreaField(_('Information'))

    meeting_location = wtforms.TextField(
        _('Location'),
        [wtforms.validators.optional(), validate_meeting_location]
    )

    # Recursion
    frequency = wtforms.SelectField(
        _('Repeat every'),
        [wtforms.validators.optional()],
        choices=[
            ('', ''),
            ('7', _('%(days)s days', days='7')),
            ('14', _('%(days)s days', days='14')),
            ('21', _('%(weeks)s weeks', weeks='3')),
            ('28', _('%(weeks)s weeks', weeks='4')),
        ]
    )
    end_repeats = wtforms.DateField(
        _('End date'),
        [wtforms.validators.optional()])

    # Reminder
    remind_when = wtforms.SelectField(
        _('Send reminder'),
        [wtforms.validators.optional()],
        choices=[
            ('', ''),
            ('H-12', _('%(hours)s hours before', hours='12')),
            ('H-24', _('%(days)s day before', days='1')),
            ('H-48', _('%(days)s days before', days='2')),
            ('H-168', _('%(days)s days before', days='7')),
        ]
    )
    remind_who = wtforms.TextField(
        _('Send reminder to'),
        [validate_multi_email, wtforms.validators.optional()])
    reminder_from = wtforms.TextField(
        _('Send reminder from'),
        [wtforms.validators.Email(), wtforms.validators.optional()])

    # Full day
    full_day = wtforms.BooleanField(_('Full day meeting'))

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
                self.reminder_from.data = meeting.reminder.reminder_from
                self.remind_who.data = meeting.reminder.reminder_to


class DeleteMeetingForm(i18nforms.Form):
    """ Form used to delete a meeting. """
    confirm_delete = wtforms.BooleanField(
        _('Yes I want to delete this meeting')
    )
    confirm_futher_delete = wtforms.BooleanField(
        _('Yes, I want to delete all futher meetings.')
    )
    from_date = wtforms.DateField(
        _('Date from which to remove the meeting')
    )


class DeleteCalendarForm(i18nforms.Form):
    """ Form used to delete a calendar. """
    confirm_delete = wtforms.BooleanField(
        _('Yes I want to delete this calendar')
    )


class ClearCalendarForm(i18nforms.Form):
    """ Form used to delete a calendar. """
    confirm_delete = wtforms.BooleanField(
        _('Yes I want to clear this calendar')
    )


class UploadIcsForm(i18nforms.Form):
    ''' Form to upload an ics file into a calendar. '''
    ics_file = wtforms.FileField(
        _('ics file'),
        [wtforms.validators.DataRequired()])
