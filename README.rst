fedocal
=======

:Author: Pierre-Yves Chibon <pingou@pingoured.fr>


fedocal is a web based calendar application.


Get this project:
-----------------
Source:  http://git.fedorahosted.org/cgit/fedocal.git/
Mirror on github: https://github.com/fedora-infra/fedocal
(Please use fedorahosted as the main repository and make sure
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
.. _python-kitchen: http://packages.python.org/kitchen/
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


Running a development instance:
-------------------------------

Clone the source::

 git clone https://github.com/fedora-infra/fedocal.git


Copy the configuration file::

 cp fedocal.cfg.sample fedocal.cfg

Adjust the configuration file (secret key, database URL, admin group...)


Create the database scheme::

 sh createdb


Run the server::

 sh runserver

You should be able to access the server at http://localhost:5000



Testing:
--------

This project contains unit-tests allowing you to check if your server
has all the dependencies correctly set.

To run them::

 ./run_tests.sh

.. note:: To stop the test at the first error or failure you can try:

   ::

    ./run_tests.sh -x


License:
--------

This project is licensed GPLv3+.
