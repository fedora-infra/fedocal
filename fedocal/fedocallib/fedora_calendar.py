# -*- coding: utf-8 -*-

"""
fedora_calendar - HTML Calendar

Copyright (C) 2012 Johan Cwiklinski
Author: Johan Cwiklinski <johan@x-tnd.be>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.
See http://www.gnu.org/copyleft/gpl.html  for the full text of the
license.
"""

from calendar import HTMLCalendar
from datetime import date

class FedocalCalendar(HTMLCalendar):

    def formatmonth(self, theyear, themonth, withyear=True):
        """
        Return a formatted month as a html valid table.
        """
        v = []
        a = v.append
        a('<table class="month">')
        a('\n')
        a(self.formatmonthname(theyear, themonth, withyear=withyear))
        a('\n')
        a(self.formatweekheader())
        a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)
