# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Johan Cwiklinski <johan@x-tnd.be>
 (c) 2014 - Copyright Patrick Uiterwijk <puiterwijk@redhat.com>
 (c) 2014 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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
from babel import support

try:
    from flask.ext.babel import (
        Babel, lazy_gettext, gettext, ngettext, format_datetime, get_locale)
except ImportError:

    def gettext(string, **variables):
        """Wrapper for gettext functions, if flask-babel is missing"""
        return string

    def ngettext(singular, plural, n, **variables):
        """Wrapper for ngettext functions, if flask-babel is missing"""
        if n == 1:
            return singular % n
        else:
            return plural % n

    def lazy_gettext(string, **variables):
        """Wrapper for lazy_gettext function, if flask-babel is missing"""
        return string

    def format_datetime(datetime=None, format=None, rebase=True):
        """Wrapper for format_datetime function, if flask-babel is missing"""
        return datetime

    def get_locale():
        """Wrapper for get_locale, if flask-babel is missing"""
        return 'en'

    class Babel(object):
        """Wrapper for Babel class, if flask-babel is missing"""

        def __init__(self, app):
            app.jinja_env.add_extension('jinja2.ext.i18n')
            app.jinja_env.install_gettext_callables(
                gettext,
                ngettext,
                newstyle=True
            )

        def localeselector(self, f):
            return f
