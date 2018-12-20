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
from __future__ import unicode_literals, absolute_import

import os

from datetime import timedelta

# Set the time after which the session expires
PERMANENT_SESSION_LIFETIME = timedelta(hours=1)

# url to the database server:
DB_URL = 'sqlite:////var/tmp/fedocal_dev.sqlite'


# The FAS group in which the admin of fedocal are
ADMIN_GROUP = 'fedocal_admin'


# The address of the SMTP server used to send the reminders emails
# via the cron job.
SMTP_SERVER = 'localhost'


# The cron job can be set with any frequency but fedocal_cron
CRON_FREQUENCY = 30

# Path to the alembic configuration file
PATH_ALEMBIC_INI = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    '..', 'alembic.ini')

# Name of the folder containing the desired theme inside the traditional
# template folder. Defaults to 'default'.
THEME_FOLDER = 'default'

ALLOWED_EXTENSIONS = ['ics', 'ical', 'ifb', 'icalendar']
ALLOWED_MIMETYPES = [
    'text/calendar',
]

# The email address to which the flask.log will send the errors (tracebacks)
EMAIL_ERROR = 'pingou@pingoured.fr'

# The URL at which the project is available.
SITE_ROOT = 'https://apps.fedoraproject.org'
SITE_URL = '%s/calendar' % SITE_ROOT

LANGUAGES = {
    'en': 'English',
    'fr': 'Français'
}

# Options for iCal remind before dropdown
ICAL_REMINDER_OPTIONS = (
    ('5', '5 minutes'),
    ('60', '1 hour'),
    ('1440', '1 day')
)
