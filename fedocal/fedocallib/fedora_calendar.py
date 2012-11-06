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

from datetime import date
from calendar import HTMLCalendar


class FedocalCalendar(HTMLCalendar):
    """ Improve Python's HTMLCalendar object adding
    html validation and some features 'locally required'
    """

    def formatday(self, day, weekday):
        """
        Return a day as a table cell.
        """
        cur_date = date.today()
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # day outside month
        else:
            if day == cur_date.day:
                return '<td class="%s, today">%d</td>' % (
                    self.cssclasses[weekday], day)
            else:
                return '<td class="%s">%d</td>' % (
                    self.cssclasses[weekday], day)

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
        #a(self.formatweekheader())
        #a('\n')
        for week in self.monthdays2calendar(theyear, themonth):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)
