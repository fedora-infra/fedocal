fedocal
=======

:Author: Pierre-Yves Chibon <pingou@pingoured.fr>


fedocal is a web based calendar application.


Get this project:
-----------------
Source:  https://pagure.io/fedocal.git/
Mirror on github: https://github.com/fedora-infra/fedocal
(Please use Pagure as the main repository and make sure
you run your patch against it)

Documentation: http://fedocal.rtfd.org


Dependencies:
-------------
.. _python: http://www.python.org
.. _Flask: http://flask.pocoo.org/
.. _python-flask: http://flask.pocoo.org/
.. _python-flask-wtf: http://packages.python.org/Flask-WTF/
.. _python-wtforms: http://wtforms.simplecodes.com/docs/1.0.1/
.. _SQLAlchemy: http://www.sqlalchemy.org/
.. _python-sqlalchemy: http://www.sqlalchemy.org/
.. _python-vobject: http://vobject.skyhouseconsulting.com/
.. _iCal: http://en.wikipedia.org/wiki/ICalendar
.. _alembic: https://bitbucket.org/zzzeek/alembic
.. _python-alembic: http://pypi.python.org/pypi/alembic
.. _pytz: http://pytz.sourceforge.net/
.. _dateutil: http://labix.org/python-dateutil
.. _python-dateutil: http://pypi.python.org/pypi/python-dateutil

This project is a `Flask`_ application. The calendars and meetings are
stored into a relational database using `SQLAlchemy`_ as Object Relational
Mapper (ORM) and `alembic`_ to handle database scheme changes.
fedocal provides an `iCal`_ feed for each calendar and relies on
`python-vobject`_ for this. Finally, `pytz`_ is used to handle the timezone
changes and `dateutil`_ to allow date manipulation over months/years.


The dependency list is therefore:

- `python`_ (2.5 minimum)
- `python-flask`_
- `python-flask-wtf`_
- `python-wtforms`_
- `python-sqlalchemy`_
- `python-vobject`_
- `python-kitchen`_
- `python-alembic`_
- `pytz`_
- `python-dateutil`_
- `python-fedora-messaging`_
- `python-flask-multistatic`_
- `python-flask-oidc`_


Running a development instance:
-------------------------------

Clone the source::

 git clone https://github.com/fedora-infra/fedocal.git


Copy the configuration files::

 cp fedocal.cfg.sample fedocal.cfg
 cp alembic.ini.sample alembic.ini

Adjust the configuration file (secret key, database URL, admin group...)


Create the database scheme::

 FEDOCAL_CONFIG=fedocal.cfg sh createdb


Register the application to iddev for development::

  oidc-register https://iddev.fedorainfracloud.org/ http://localhost:5000/oidc_callback


Add the following two lines in your configuration file `fedocal.cfg`::

  OIDC_ID_TOKEN_COOKIE_SECURE = False
  OIDC_REQUIRE_VERIFIED_EMAIL = False


Run the server::

 python runserver.py --config fedocal.cfg

You should be able to access the server at http://localhost:5000 (do not use
``127.0.0.1`` as it will no work)


/!\ If login in does not work and gives you an ``invalid return_uri`` check
  the ``redirect_uris`` in the ``client_secrets.json`` file and make sure it
  matches **exactly** (check http vs https, trailing slash vs no trailing slash...).
  You may have to re-register as editing directly the ``client_secrets.json``
  file will not work.



Testing:
--------

This project contains unit-tests allowing you to check if your server
has all the dependencies correctly set.

To run them simply call::

 tox

.. note:: To stop the test at the first error or failure you can try:

   ::

    tox -- -x

.. note:: To run a single file you can try:

   ::

    tox -- tests/test_flask.py -x


Reporting issues:
-----------------

For any issue you may encounter please file a ticket and submit it to:

Fedocal Pagure: https://pagure.io/fedocal/issues

Contributors can use the same tracker to find existing bugs to work on.
You need to login with your FAS account to submit or modify a ticket.



License:
--------

This project is licensed GPLv3+.
