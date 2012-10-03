#!/usr/bin/python
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

This script is meant to be run as a cron job to send the reminders for
each meeting that asked for it.
"""

import ConfigParser
import smtplib
import os

from email.mime.text import MIMEText

import sys
sys.path.insert(0, 'fedocal')

from fedocal import fedocallib

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
    s = smtplib.SMTP('localhost')
    s.sendmail(from_email,
                meeting.reminder.reminder_to,
                msg.as_string())
    s.quit()


def send_reminder(db_url):
    """ Retrieve all the meeting for which we should send a reminder and
    do it.
    """
    session = fedocallib.create_session(db_url)
    meetings = fedocallib.retrieve_meeting_to_remind(session)
    for meeting in meetings:
        send_reminder_meeting(meeting)


if __name__ == '__main__':
    sys.argv.append('fedocal/fedocal.cfg')
    config = ConfigParser.ConfigParser()
    if len(sys.argv) == 1:
        if os.path.exists('/etc/fedocal.cfg'):
            config.readfp(open('/etc/fedocal.cfg'))
        else:
            print 'No config file found in /etc or specified to the cron.'
    elif len(sys.argv) == 2:
        if os.path.exists(sys.argv[1]):
            config.readfp(open(sys.argv[1]))
        else:
            print 'Config file specified to the cron could not be found.'
    send_reminder(config.get('fedocal', 'db_url'))
