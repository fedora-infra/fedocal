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
import flask


class FedocalCalendar(HTMLCalendar):
    """ Improve Python's HTMLCalendar object adding
    html validation and some features 'locally required'
    """

    def __init__(self, year, month, calendar_name=None):
        """ Constructor.
        Stores the year and the month asked.
        """
        super(FedocalCalendar, self).__init__()
        self.year = year
        self.month = month
        self.calendar_name = calendar_name

    def formatday(self, day, weekday):
        """
        Return a day as a table cell.
        """
        cur_date = date.today()
        if day == 0:
            return '<td class="noday">&nbsp;</td>'  # day outside month
        else:
            link_day = day
            if self.calendar_name:
                link_day= '<a href="%s">%d</a>' % (flask.url_for(
                        'calendar_fullday',
                        calendar_name=self.calendar_name, year=self.year,
                        month=self.month, day=day), day)
            if day == cur_date.day \
                and self.month == cur_date.month \
                and self.year == cur_date.year:
                return '<td class="%s today">%s</td>' % (
                    self.cssclasses[weekday], link_day)
            else:
                return '<td class="%s">%s</td>' % (
                    self.cssclasses[weekday], link_day)

    def formatmonth(self, withyear=True):
        """
        Return a formatted month as a html valid table.
        """
        v = []
        a = v.append
        a('<table class="month">')
        a('\n')
        a(self.formatmonthname(self.year, self.month, withyear=withyear))
        a('\n')
        #a(self.formatweekheader())
        #a('\n')
        for week in self.monthdays2calendar(self.year, self.month):
            a(self.formatweek(week))
            a('\n')
        a('</table>')
        a('\n')
        return ''.join(v)
