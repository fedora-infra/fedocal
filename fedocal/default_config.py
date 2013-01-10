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

import os


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
PATH_ALEMBIC_INI=os.path.join(os.path.dirname(os.path.abspath(__file__)),
    '..','alembic.ini')
