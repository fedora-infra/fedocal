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

__requires__ = ['SQLAlchemy >= 0.7']
import pkg_resources

import unittest
import sys
import os

from datetime import date
from datetime import time
from datetime import timedelta

from sqlalchemy.exc import IntegrityError

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from fedocallib import model
from tests import Modeltests


class Remindertests(Modeltests):
    """ Reminder tests. """

    def test_init_reminder(self):
        """ Test the Reminder init function. """
        obj = model.Reminder('H-12',
            'fi-apprentice@lists.fedoraproject.org,'\
            'ambassadors@lists.fedoraproject.org',
            'This is your friendly reminder')
        obj.save(self.session)
        self.session.commit()
        self.assertNotEqual(obj, None)

    def test_init_reminder_failed(self):
        """ Test the Reminder init function. """
        obj = model.Reminder('H-36',
            'fi-apprentice@lists.fedoraproject.org,'\
            'ambassadors@lists.fedoraproject.org',
            'This is your friendly reminder')
        obj.save(self.session)
        try:
            self.session.flush()
        except IntegrityError:
            obj = None
        self.assertEqual(obj, None)

    def test_repr_reminder(self):
        """ Test the Reminder string representation function. """
        self.test_init_reminder()
        obj = model.Reminder.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertEqual(str(obj), '<Reminder(\'' \
            'fi-apprentice@lists.fedoraproject.org,'\
            'ambassadors@lists.fedoraproject.org\', \'H-12\')>')

    def test_get_reminder(self):
        """ Test the query of a reminder by its identifier. """
        self.test_init_reminder()
        obj = model.Reminder.by_id(self.session, 1)
        self.assertNotEqual(obj, None)
        self.assertEqual(obj.reminder_offset, 'H-12')
        self.assertEqual(obj.reminder_to,
            'fi-apprentice@lists.fedoraproject.org,'\
            'ambassadors@lists.fedoraproject.org')
        self.assertEqual(obj.reminder_text, 'This is your friendly reminder')

if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Remindertests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
