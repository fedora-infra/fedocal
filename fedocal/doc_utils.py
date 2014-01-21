#-*- coding: utf-8 -*-

"""
 (c) 2013-2014 - Copyright Pierre-Yves Chibon <pingou@pingoured.fr>

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

import docutils
import docutils.examples
import markupsafe


def modify_rst(rst):
    """ Downgrade some of our rst directives if docutils is too old. """

    try:
        # The rst features we need were introduced in this version
        minimum = [0, 9]
        version = [int(el) for el in docutils.__version__.split('.')]

        # If we're at or later than that version, no need to downgrade
        if version >= minimum:
            return rst
    except Exception:  # pragma: no cover
        # If there was some error parsing or comparing versions, run the
        # substitutions just to be safe.
        pass

    # On Fedora this will never work as the docutils version is to recent
    # Otherwise, make code-blocks into just literal blocks.
    substitutions = {  # pragma: no cover
        '.. code-block:: javascript': '::',
    }
    for old, new in substitutions.items():  # pragma: no cover
        rst = rst.replace(old, new)

    return rst  # pragma: no cover


def modify_html(html):
    """ Perform style substitutions where docutils doesn't do what we want.
    """

    substitutions = {
        '<tt class="docutils literal">': '<code>',
        '</tt>': '</code>',
    }
    for old, new in substitutions.items():
        html = html.replace(old, new)

    return html


def load_doc(endpoint):
    """ Utility to load an RST file and turn it into fancy HTML. """

    rst = unicode(endpoint.__doc__)

    rst = modify_rst(rst)

    api_docs = docutils.examples.html_body(rst)

    api_docs = modify_html(api_docs)

    api_docs = markupsafe.Markup(api_docs)
    return api_docs
