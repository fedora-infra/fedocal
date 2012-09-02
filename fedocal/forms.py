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


class LoginForm(wtf.Form):
    username = wtf.TextField('Username', [wtf.validators.Required()])
    password = wtf.PasswordField('Password', [wtf.validators.Required()])

