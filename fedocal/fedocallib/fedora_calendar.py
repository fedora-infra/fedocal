# -*- coding: utf-8 -*-

"""
fedora_calendar - HTML Calendar

Copyright (C) 2012-2014 Johan Cwiklinski
Author: Johan Cwiklinski <johan@x-tnd.be>
        Pierre-Yves Chibon <pingou@pingoured.fr>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.
See http://www.gnu.org/copyleft/gpl.html  for the full text of the
license.
"""

from datetime import date
from calendar import LocaleHTMLCalendar
from calendar import TimeEncoding
from calendar import month_name
import fedocal
import flask


class FedocalCalendar(LocaleHTMLCalendar):
    """ Improve Python's HTMLCalendar object adding
    html validation and some features 'locally required'
    """

    def __init__(self, year, month, day,
                 calendar_name=None, loc_name=None, busy_days=None):
        """ Constructor.
        Stores the year and the month asked.
        """
        babel_locale = fedocal.get_locale()
        if babel_locale == 'fr':
            cal_locale = 'fr_FR'
        else:
            cal_locale = 'en_US'

        LocaleHTMLCalendar.__init__(self, locale=cal_locale)
        self.year = year
        self.month = month
        self.day = day
        self.busy_days = busy_days or []
        self.calendar_name = calendar_name
        self.loc_name = loc_name

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
                link_day = '<a href="%s">%d</a>' % (
                    flask.url_for(
                        'calendar',
                        calendar_name=self.calendar_name, year=self.year,
                        month=self.month, day=day),
                    day)
            elif self.loc_name:
                link_day = '<a href="%s">%d</a>' % (
                    flask.url_for(
                        'location',
                        loc_name=self.loc_name, year=self.year,
                        month=self.month, day=day),
                    day)

            if day in self.busy_days:
                link_day = '<div class="busy_day">%s</div>' % link_day

            if day == cur_date.day \
                    and self.month == cur_date.month \
                    and self.year == cur_date.year:
                output = '<td class="%s today">%s</td>' % (
                    self.cssclasses[weekday], link_day)
            else:
                output = '<td class="%s">%s</td>' % (
                    self.cssclasses[weekday], link_day)

            return output

    # pylint: disable=W0221
    def formatweek(self, theweek, current=False):
        """ Return a complete week as a table row.

        :kwarg current: a boolean stating wether this is the current
            week or not (the current week will have the css class:
            current_week)
        """
        string = ''.join(self.formatday(d, wd) for (d, wd) in theweek)
        if current:
            return '<tr class="current_week">%s</tr>' % string
        else:
            return '<tr>%s</tr>' % string

    def formatmonthname(self, theyear, themonth, withyear=True):
        """
        Return a month name as a table row.
        """

        with TimeEncoding(self.locale) as encoding:
            smonth = month_name[themonth]
            if encoding is not None:
                smonth = smonth.decode(encoding)

            if withyear:
                string = '%s %s' % (smonth, theyear)
            else:
                string = '%s' % smonth

        prev_month = self.month - 1
        prev_year = self.year
        if prev_month == 0:
            prev_month = 12
            prev_year = prev_year - 1

        prev_month_lnk = ''
        if self.calendar_name:
            prev_month_lnk = '<a class="button" href="%s">&lt;</a>' % (
                flask.url_for(
                    'calendar',
                    calendar_name=self.calendar_name,
                    year=int(prev_year),
                    month=int(prev_month),
                    day=1))
        elif self.loc_name:
            prev_month_lnk = '<a class="button" href="%s">&lt;</a>' % (
                flask.url_for(
                    'location',
                    loc_name=self.loc_name,
                    year=int(prev_year),
                    month=int(prev_month),
                    day=1))

        next_month = self.month
        next_year = self.year + next_month / 12
        next_month = next_month % 12 + 1

        next_month_lnk = ''
        if self.calendar_name:
            next_month_lnk = '<a class="button" href="%s">&gt;</a>' % (
                flask.url_for(
                    'calendar',
                    calendar_name=self.calendar_name,
                    year=int(next_year),
                    month=int(next_month),
                    day=1))
        elif self.loc_name:
            next_month_lnk = '<a class="button" href="%s">&gt;</a>' % (
                flask.url_for(
                    'location',
                    loc_name=self.loc_name,
                    year=int(next_year),
                    month=int(next_month),
                    day=1))

        return '<tr><th colspan="7" class="month">%s %s %s</th></tr>' % (
            prev_month_lnk, string, next_month_lnk)

    # pylint: disable=W0221
    def formatmonth(self, withyear=True):
        """
        Return a formatted month as a html valid table.
        """
        values = []
        item = values.append
        item('<table class="month">')
        item('\n')
        item(self.formatmonthname(self.year, self.month, withyear=withyear))
        item('\n')
        #item(self.formatweekheader())
        #item('\n')
        for week in self.monthdays2calendar(self.year, self.month):
            days = [day[0] for day in week]
            if self.day in days:
                item(self.formatweek(week, current=True))
            else:
                item(self.formatweek(week))
            item('\n')
        item('</table>')
        item('\n')
        return ''.join(values)
