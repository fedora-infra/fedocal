#-*- coding: utf-8 -*-

"""
 (c) 2014 - Copyright Johan Cwiklinski <johan@x-tnd.be>

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
from fedocal.fedocal_babel import get_locale
from babel import support
import os


def translations_path():
    """Retrieve trnaslations path"""
    module_path = os.path.abspath(__file__)
    dirname = os.path.join(os.path.dirname(module_path), 'translations')
    return dirname


def _get_translations():
    """Get translations"""
    try:
        ctx = _request_ctx_stack.top
        translations = getattr(ctx, 'wtforms_translations', None)
        if translations is None:
            translations = support.Translations.load(
                translations_path(), [get_locale()], domain='messages'
            )
        ctx.wtforms_translations = translations
        return translations
    except:
        return None


class Translations(object):
    """Translations object (see 
    http://wtforms.readthedocs.org/en/1.0.5/i18n.html#writing-your-own-translations-provider
    """
    def gettext(self, string):
        """Gettext for forms"""
        trans = _get_translations()
        if trans is None:
            return string
        return trans.ugettext(string)

    def ngettext(self, singular, plural, num):
        """Ngettext for forms"""
        trans = _get_translations()
        if trans is None:
            if num == 1:
                return singular
            return plural
        return trans.ungettext(singular, plural, num)


TRANSLATIONS = Translations()


class Form(wtf.Form):
    """I18n form"""
    def _get_translations(self):
        """I18n form translation"""
        return TRANSLATIONS
