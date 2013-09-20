#!/usr/bin/python
#-*- coding: utf-8 -*-

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

This script is meant to be run as a cron job to send the reminders for
each meeting that asked for it.
"""


## These two lines are needed to run on EL6
__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources


import ConfigParser
import smtplib
import os

from email.mime.text import MIMEText

import fedocal
import fedocal.fedocallib as fedocallib


def fedmsg_init():
    try:
        import fedmsg
        import fedmsg.config
    except ImportError:
        warnings.warn("fedmsg ImportError")
        return

    config = fedmsg.config.load_config()
    config['active'] = True
    fedmsg.init(**config)


def fedmsg_publish(meeting):
    try:
        import fedmsg
    except ImportError:
        return

    fedmsg.publish(
        modname="fedocal",
        topic="meeting.reminder",
        msg=dict(
            calendar=meeting.calendar.to_json()
            meeting=meeting.to_json(),
        ),
    )


def send_reminder_meeting(meeting):
    """ This function sends the actual reminder of a given meeting.
    :arg meeting: a Meeting object from fedocallib.model
    """
    if not meeting.reminder_id:
        return
    string = """Dear all,

You are kindly invited to the meeting : 
   %s on %s from %s to %s

The meeting will be about:
%s
""" % (meeting.meeting_name, meeting.meeting_date,
        meeting.meeting_time_start, meeting.meeting_time_stop,
        meeting.meeting_information)
    if meeting.reminder.reminder_text:
        string = string + """
Please note:
%s""" % meeting.reminder.reminder_text
    msg = MIMEText(string)
    msg['Subject'] = '[Fedocal] Reminder meeting : %s' % meeting.meeting_name
    from_email = meeting.meeting_manager.split(',')[0]
    from_email = '%s@fedoraproject.org' % from_email
    msg['From'] = from_email
    msg['To'] = meeting.reminder.reminder_to

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    s = smtplib.SMTP(fedocal.APP.config['SMTP_SERVER'])
    s.sendmail(from_email,
                meeting.reminder.reminder_to,
                msg.as_string())
    s.quit()


def send_reminder():
    """ Retrieve all the meeting for which we should send a reminder and
    do it.
    """
    db_url = fedocal.APP.config['DB_URL']
    session = fedocallib.create_session(db_url)
    meetings = fedocallib.retrieve_meeting_to_remind(session,
        offset=int(fedocal.APP.config['CRON_FREQUENCY']))
    for meeting in meetings:
        send_reminder_meeting(meeting)
        fedmsg_publish(meeting)


if __name__ == '__main__':
    fedmsg_init()
    send_reminder()
