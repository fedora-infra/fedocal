# -*- coding: utf-8 -*-

"""
exceptions - Different Exceptions classes used in the project.

Copyright (C) 2012 Pierre-Yves Chibon
Author: Pierre-Yves Chibon <pingou@pingoured.fr>

This program is free software; you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation; either version 3 of the License, or (at
your option) any later version.
See http://www.gnu.org/copyleft/gpl.html  for the full text of the
license.
"""
from __future__ import unicode_literals, absolute_import, print_function


# pylint: disable=R0903
class FedocalException(Exception):
    """ Exception thrown when a user is not allowed to perform a specific
    action.
    """
    pass


# pylint: disable=R0903
class UserNotAllowed(FedocalException):
    """ Exception thrown when a user is not allowed to perform a specific
    action.
    """
    pass


# pylint: disable=R0903
class InvalidMeeting(FedocalException):
    """ Exception thrown when a user is not allowed to perform a specific
    action.
    """
    pass
