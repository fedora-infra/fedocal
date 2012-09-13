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

from fedocallib import HOURS


class AddCalendarForm(wtf.Form):
    calendar_name = wtf.TextField('Calendar',
        [wtf.validators.Required()])
    calendar_description = wtf.TextField('Description')
    calendar_manager_groups = wtf.TextField('Manager groups')


class AddMeetingForm(wtf.Form):
    meeting_name = wtf.TextField('Meeting name',
        [wtf.validators.Required()])

    meeting_date = wtf.DateField('Date', [wtf.validators.Required()])

    meeting_time_start = wtf.SelectField('Start time',
        [wtf.validators.Required()],
        choices = [(hour, hour) for hour in HOURS]
        )

    meeting_time_stop = wtf.SelectField('Stop time',
        [wtf.validators.Required()],
        choices = [(hour, hour) for hour in HOURS]
        )
    comanager = wtf.TextField('Co-manager')

    information = wtf.TextAreaField('Information')

    # Recursion
    frequency = wtf.SelectField('Repeat every',
        [wtf.validators.optional()],
        choices = [ ('', ''),
                    ('7', '7 days'),
                    ('14', '14 days')]
        )
    end_repeats = wtf.DateField('End date', [wtf.validators.optional()])

    # Reminder
    remind_when = wtf.SelectField('Send reminder',
        [wtf.validators.optional()],
        choices = [ ('', ''),
                    ('H-12', '12 hours before'),
                    ('H-24', '1 day before'),
                    ('H-48', '2 days before'),
                    ('H-168', '7 days before'),
                    ]
        )
    remind_who = wtf.TextField('Send reminder to',
        [wtf.validators.Email(), wtf.validators.optional()])

    def __init__(self, *args, **kwargs):
        """ Calls the default constructor with the normal argument but
        if a meeting is set using the meeting keyword, then fill the
        value of the form with the value from the Meeting object.
        """
        super(AddMeetingForm, self).__init__(*args, **kwargs)
        if 'meeting' in kwargs:
            meeting = kwargs['meeting']
            if meeting.meeting_time_start.hour < 10:
                start_hour = "0%s" % str(meeting.meeting_time_start.hour)
            else:
                start_hour = str(meeting.meeting_time_start.hour)
            if meeting.meeting_time_stop.hour < 10:
                stop_hour = "0%s" % str(meeting.meeting_time_stop.hour)
            else:
                stop_hour = str(meeting.meeting_time_stop.hour)
        
            self.meeting_name.data = meeting.meeting_name
            self.meeting_date.data = meeting.meeting_date
            self.meeting_time_start.data = start_hour
            self.meeting_time_stop.data = stop_hour
            # You are not allowed to remove yourself from the managers.
            meeting_manager = meeting.meeting_manager.replace(
                        '%s,' % flask.g.fas_user.username, '')
            self.comanager.data = meeting_manager
            if meeting.recursion_id:
                self.frequency.data = meeting.recursion.recursion_frequency
                self.end_repeats.data = meeting.recursion.recursion_ends
            if meeting.reminder_id:
                self.remind_when.data = meeting.reminder.reminder_offset
                self.remind_who.data = meeting.reminder.reminder_to


class DeleteMeetingForm(wtf.Form):
    confirm_delete = wtf.BooleanField('Yes I want to delete this meeting')
    confirm_futher_delete = wtf.BooleanField('Yes, I want to delete all futher meetings.')


class LoginForm(wtf.Form):
    username = wtf.TextField('Username', [wtf.validators.Required()])
    password = wtf.PasswordField('Password', [wtf.validators.Required()])

