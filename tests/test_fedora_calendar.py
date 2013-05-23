#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
 (c) 2012 - Copyright Pierre-Yves Chibon
 Author: Pierre-Yves Chibon <pingou@pingoured.fr>

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

 fedocal.model test script
"""

__requires__ = ['SQLAlchemy >= 0.7', 'jinja2 >= 2.4']
import pkg_resources

import unittest
import sys
import os

from datetime import date

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from fedocallib.fedora_calendar import FedocalCalendar
from tests import Modeltests, TODAY


class FedocalCalendartests(Modeltests):
    """ fedora_calendar application tests. """

    def test_formatday(self):
        """ Test the formatday function. """
        today = date.today()
        cal = FedocalCalendar(today.year, today.month, today.day)
        self.assertEqual(cal.formatday(6, 1),
            '<td class="tue">6</td>')
        self.assertEqual(cal.formatday(7, 3),
            '<td class="thu">7</td>')
        self.assertEqual(cal.formatday(today.day, today.isoweekday() - 1),
            '<td class="%s today">%s</td>' % (
                today.strftime('%a').lower(), today.day)
                )

    def test_formatweek(self):
        """ Test the formatweek function. """
        today = TODAY
        cal = FedocalCalendar(today.year, today.month, today.day)
        output = cal.formatweek([(1, 1), (2, 2)]).replace(' today', '')
        self.assertEqual(
            output,
            '<tr><td class="tue">1</td><td class="wed">2</td></tr>')
        self.assertEqual(
            cal.formatweek([(0, 1), (1, 2)]),
            '<tr><td class="noday">&nbsp;</td><td class="wed">1</td></tr>')
        output = cal.formatweek([(1, 1), (2, 2)], True).replace(' today', '')
        self.assertEqual(
            output,
            '<tr class="current_week"><td class="tue">1</td><td '\
            'class="wed">2</td></tr>')

    def test_formatmonthname(self):
        """ Test the formatmonthname function. """
        today = date.today()
        cal = FedocalCalendar(today.year, today.month, today.day)
        self.assertEqual(cal.formatmonthname(2012, 4),
            '<tr><th colspan="7" class="month"> April 2012 </th></tr>')
        self.assertEqual(cal.formatmonthname(2012, 4, False),
            '<tr><th colspan="7" class="month"> April </th></tr>')

    def test_formatmonth(self):
        """ Test the formatmonth function. """
        cal = FedocalCalendar(2012, 1, 10)
        self.assertEqual(cal.formatmonth(),
            '<table class="month">\n<tr><th colspan="7" class="month"> '\
            'January 2012 </th></tr>\n<tr><td '\
            'class="noday">&nbsp;</td><td class="noday">&nbsp;'\
            '</td><td class="noday">&nbsp;</td><td class="noday">'\
            '&nbsp;</td><td class="noday">&nbsp;</td><td class="noday">'\
            '&nbsp;</td><td class="sun">1</td></tr>\n<tr><td '\
            'class="mon">2</td><td class="tue">3</td><td class="wed">'\
            '4</td><td class="thu">5</td><td class="fri">6</td><td '\
            'class="sat">7</td><td class="sun">8</td></tr>\n<tr '\
            'class="current_week"><td class="mon">9</td><td '\
            'class="tue">10</td><td class="wed">11</td><td '\
            'class="thu">12</td><td class="fri">13</td><td '\
            'class="sat">14</td><td class="sun">15</td></tr>\n<tr><td'\
            ' class="mon">16</td><td class="tue">17</td><td '\
            'class="wed">18</td><td class="thu">19</td><td '\
            'class="fri">20</td><td class="sat">21</td><td '\
            'class="sun">22</td></tr>\n<tr><td class="mon">23</td>'\
            '<td class="tue">24</td><td class="wed">25</td><td '\
            'class="thu">26</td><td class="fri">27</td><td '\
            'class="sat">28</td><td class="sun">29</td></tr>\n<tr>'\
            '<td class="mon">30</td><td class="tue">31</td><td '\
            'class="noday">&nbsp;</td><td class="noday">&nbsp;</td>'\
            '<td class="noday">&nbsp;</td><td class="noday">&nbsp;</td>'\
            '<td class="noday">&nbsp;</td></tr>\n</table>\n')

        self.assertEqual(cal.formatmonth(False),
            '<table class="month">\n<tr><th colspan="7" class="month">'\
            ' January </th></tr>\n<tr><td '\
            'class="noday">&nbsp;</td><td class="noday">&nbsp;'\
            '</td><td class="noday">&nbsp;</td><td class="noday">'\
            '&nbsp;</td><td class="noday">&nbsp;</td><td class="noday">'\
            '&nbsp;</td><td class="sun">1</td></tr>\n<tr><td '\
            'class="mon">2</td><td class="tue">3</td><td class="wed">'\
            '4</td><td class="thu">5</td><td class="fri">6</td><td '\
            'class="sat">7</td><td class="sun">8</td></tr>\n<tr '\
            'class="current_week"><td class="mon">9</td><td '\
            'class="tue">10</td><td class="wed">11</td><td '\
            'class="thu">12</td><td class="fri">13</td><td '\
            'class="sat">14</td><td class="sun">15</td></tr>\n<tr><td'\
            ' class="mon">16</td><td class="tue">17</td><td '\
            'class="wed">18</td><td class="thu">19</td><td '\
            'class="fri">20</td><td class="sat">21</td><td '\
            'class="sun">22</td></tr>\n<tr><td class="mon">23</td>'\
            '<td class="tue">24</td><td class="wed">25</td><td '\
            'class="thu">26</td><td class="fri">27</td><td '\
            'class="sat">28</td><td class="sun">29</td></tr>\n<tr>'\
            '<td class="mon">30</td><td class="tue">31</td><td '\
            'class="noday">&nbsp;</td><td class="noday">&nbsp;</td>'\
            '<td class="noday">&nbsp;</td><td class="noday">&nbsp;</td>'\
            '<td class="noday">&nbsp;</td></tr>\n</table>\n')


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(FedocalCalendartests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
