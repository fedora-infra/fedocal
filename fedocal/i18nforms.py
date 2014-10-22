# -*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Johan Cwiklinski <johan@x-tnd.be>
 (c) 2014 - Copyright Patrick Uiterwijk <puiterwijk@redhat.com>

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
from flask import _request_ctx_stack
from fedocal.fedocal_babel import get_locale, gettext, ngettext
from babel import support
import os


class Translations(object):
    """Translations object (see
    http://wtforms.readthedocs.org/en/1.0.5/i18n.html#writing-your-own-translations-provider
    """
    def __init__(self):
        """ Constructor instanciates the gettext and ngettext methods used
        by the forms to translate.
        """
        self.gettext = gettext
        self.ngettext = ngettext


class Form(wtf.Form):
    """I18n form"""
    def _get_translations(self):
        """I18n form translation"""
        return Translations()
