#!/usr/bin/python
#-*- coding: utf-8 -*-

"""
 (c) 2012-2013 - Copyright Pierre-Yves Chibon
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
from datetime import timedelta
from functools import wraps

from contextlib import contextmanager
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.orm import scoped_session

sys.path.insert(0, os.path.join(os.path.dirname(
    os.path.abspath(__file__)), '..'))

from fedocal.fedocallib import model, get_start_week


DB_PATH = 'sqlite:///:memory:'
FAITOUT_URL = 'http://209.132.184.152/faitout/'
try:
    import requests
    req = requests.get('%s/new' % FAITOUT_URL)
    if req.status_code == 200:
        DB_PATH = req.text
        print 'Using faitout at: %s' % DB_PATH
except:
    pass


TODAY = get_start_week(date.today().year, date.today().month,
                       date.today().day) + timedelta(days=2)

ICS_FILE = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'ical.ics')
ICS_FILE_NOTOK = os.path.join(os.path.dirname(
    os.path.abspath(__file__)), 'ical_wrong')


def flask10_only(function):
    """ Decorator to skip tests if the flask version is lower than 0.10 """
    @wraps(function)
    def decorated_function(*args, **kwargs):
        """ Decorated function, actually does the work. """
        import flask
        ver = flask.__version__.split('.')
        if int(ver[0]) >= 0 and int(ver[1]) >= 10:
            return function(*args, **kwargs)
        return 'Skipped'
    return decorated_function


@contextmanager
def user_set(APP, user):
    """ Set the provided user as fas_user in the provided application."""

    # Hack used to remove the before_request function set by
    # flask.ext.fas_openid.FAS which otherwise kills our effort to set a
    # flask.g.fas_user.
    from flask import appcontext_pushed, g
    APP.before_request_funcs[None] = []

    def handler(sender, **kwargs):
        g.fas_user = user

    with appcontext_pushed.connected_to(handler, APP):
        yield


class Modeltests(unittest.TestCase):
    """ Model tests. """

    def __init__(self, method_name='runTest'):
        """ Constructor. """
        unittest.TestCase.__init__(self, method_name)
        self.session = None

    # pylint: disable=C0103
    def setUp(self):
        """ Set up the environnment, ran before every tests. """
        self.session = model.create_tables(DB_PATH)

    # pylint: disable=C0103
    def tearDown(self):
        """ Remove the test.db database if there is one. """
        self.session.close()
        if os.path.exists(DB_PATH):
            os.unlink(DB_PATH)
        if DB_PATH.startswith('postgres'):
            if 'localhost' in DB_PATH:
                model.drop_tables(DB_PATH, self.session.bind)
            else:
                db_name = DB_PATH.rsplit('/', 1)[1]
                requests.get('%s/clean/%s' % (FAITOUT_URL, db_name))


class FakeGroup(object):
    """ Fake object used to make the FakeUser object closer to the
    expectations.
    """

    def __init__(self, name):
        """ Constructor.
        :arg name: the name given to the name attribute of this object.
        """
        self.name = name
        self.group_type = 'cla'


# pylint: disable=R0903
class FakeUser(object):
    """ Fake user used to test the fedocallib library. """

    def __init__(self, groups=[], username='username', cla_done=True):
        """ Constructor.
        :arg groups: list of the groups in which this fake user is
            supposed to be.
        """
        if isinstance(groups, basestring):
            groups = [groups]
        self.groups = groups
        self.username = username
        self.name = username
        self.approved_memberships = [
            FakeGroup('packager'),
            FakeGroup('design-team')]
        self.dic = {}
        self.dic['timezone'] = 'Europe/Paris'
        self.cla_done = cla_done

    def __getitem__(self, key):
        return self.dic[key]


if __name__ == '__main__':
    SUITE = unittest.TestLoader().loadTestsFromTestCase(Modeltests)
    unittest.TextTestRunner(verbosity=2).run(SUITE)
