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
from __future__ import unicode_literals, absolute_import

import smtplib
import warnings
import logging

from email.mime.text import MIMEText

import fedocal
import fedocal.fedocallib as fedocallib
import fedocal.fedocallib.fedmsgshim as fedmsg

_log = logging.getLogger(__name__)

def fedmsg_publish(meeting, meeting_id):
    """ Publish the meeting.reminder messages on fedora-messaging.
    :arg meeting: a Meeting object from fedocallib.model
    :arg meeting_id: an int representing the meeting identifier in the
        database
    """
    _log.debug('Publishing a message for meeting: %s', meeting_id)

    meeting_dict = meeting.to_json()
    meeting_dict['meeting_id'] = meeting_id

    message = dict(
        meeting=meeting_dict,
        calendar=meeting.calendar.to_json()
    )
    fedmsg.publish(topic='reminder', msg=message)


def send_reminder_meeting(meeting, meeting_id):
    """ This function sends the actual reminder of a given meeting.
    :arg meeting: a Meeting object from fedocallib.model
    :arg meeting_id: an int representing the meeting identifier in the
        database
    """
    if not meeting.reminder_id:
        return
    location = ''
    if meeting.meeting_location:
        location = 'At %s' % meeting.meeting_location

    string = u"""Dear all,

You are kindly invited to the meeting:
   %(name)s on %(date)s from %(time_start)s to %(time_stop)s %(timezone)s
   %(location)s

The meeting will be about:
%(description)s


Source: %(host)s/meeting/%(id)s/

""" % ({
        'name': u'%s' % meeting.meeting_name,
        'date': meeting.meeting_date,
        'time_start': meeting.meeting_time_start,
        'time_stop': meeting.meeting_time_stop,
        'timezone': meeting.meeting_timezone,
        'location': u'%s' % location,
        'description': u'%s' % meeting.meeting_information,
        'id': meeting_id,
        'host': fedocal.APP.config['SITE_URL'],
    })

    if meeting.reminder.reminder_text:
        string = string + u"""
Please note:
%s""" % meeting.reminder.reminder_text
    msg = MIMEText(string.encode('utf-8'), 'plain', 'utf-8')
    msg['Subject'] = '[Fedocal] Reminder meeting : %s' % meeting.meeting_name
    from_email = meeting.meeting_manager[0]
    from_email = '%s@fedoraproject.org' % from_email
    msg['From'] = meeting.reminder.reminder_from or from_email
    msg['To'] = meeting.reminder.reminder_to.replace(',', ', ')

    # Send the message via our own SMTP server, but don't include the
    # envelope header.
    smtp = smtplib.SMTP(fedocal.APP.config['SMTP_SERVER'])
    smtp.sendmail(
        from_email,
        meeting.reminder.reminder_to.split(','),
        msg.as_string())
    smtp.quit()
    return msg


def send_reminder():
    """ Retrieve all the meeting for which we should send a reminder and
    do it.
    """
    db_url = fedocal.APP.config['DB_URL']
    session = fedocallib.create_session(db_url)
    meetings = fedocallib.retrieve_meeting_to_remind(
        session, offset=int(fedocal.APP.config['CRON_FREQUENCY']))

    msgs = []
    for meeting in meetings:
        meeting_id = meeting.meeting_id
        meeting = fedocallib.update_date_rec_meeting(meeting, action='next')
        msgs.append(send_reminder_meeting(meeting, meeting_id))
        fedmsg_publish(meeting, meeting_id)

    return msgs


if __name__ == '__main__':
    send_reminder()
