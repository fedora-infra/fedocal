fedocal
=======

:Author: Pierre-Yves Chibon <pingou@pingoured.fr>


fedocal is a web based calendar application.


Get this project:
-----------------
Source:  https://github.com/pypingou/fedocal



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

This project is a `Flask`_ application. The calendars and meetings are
stored into a relational database using `SQLAlchemy`_ as Object Relational
Mapper (ORM) and `alembic`_ to handle database scheme changes.
fedocal provides an `iCal`_ feed for each calendar and relies on
`python-vobject`_ for this. Finally, `pytz`_ is used to handle the timezone
changes.


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


Running a development instance:
-------------------------------

Clone the source::

 git clone https://github.com/pypingou/fedocal.git


Copy the configuration file::

 cp fedocal.cfg.sample fedocal.cfg

Adjust the configuration file (secret key, database URL, admin group...)


Create the database scheme::

 python fedocal/fedocallib/model.py


Run the server::
 sh runserver

You should be able to access the server at http://localhost:5000


Deploying this project:
-----------------------

.. _Flask deployment documentation: http://flask.pocoo.org/docs/deploying/

Instruction to deploy this application is available on the
`Flask deployment documentation`_ page.

 **My approach.**

Below is the approach I took to deploy the instance on a local (test) machine.


Retrieve the sources::

 cd /srv/
 git clone <repo>
 cd fedocal


Copy the configuration file::

 cp fedocal.cfg.sample fedocal.cfg

Adjust the configuration file (secret key, database URL, admin group...)

Create the database scheme::

 python fedocal/fedocallib/model.py


Then configure apache::

 sudo vim /etc/httd/conf.d/wsgi.conf

and put in this file::

 WSGIScriptAlias /fedocal /var/www/wsgi/fedocal.wsgi
 <Directory /var/www/wsgi/>
    Order deny,allow
    Allow from all
 </Directory>

Then create the file /var/www/wsgi/fedocal.wsgi with::

 import sys
 sys.path.insert(0, '/srv/fedocal/')
 
 import fedocal
 application = fedocal.APP


Then restart apache and you should be able to access the website on
http://localhost/fedocal


Testing:
--------

This project contains unit-tests allowing you to check if your server
has all the dependencies correctly set.

To run them::

 ./run_tests.sh


Database changes:
-----------------
.. _alembic tutorial: http://alembic.readthedocs.org/en/latest/tutorial.html

The database changes are handled via `alembic`.


If you are deploying fedocal for the first time, you will not need this,
however, if you already have a running fedocal but the database scheme
is not up to date, then you will have to run::


 alembic upgrade head

.. note:: If this is the first time you are running ``alembic``, you will
   need to copy file ``alembic.ini.sample`` to ``alembic.ini`` and setup
   the ``sqlalchemy.url`` variable in the latest


If you are a developer, you probably want to have a look at the `alembic tutorial`_


License:
--------

This project is licensed GPLv3+.
