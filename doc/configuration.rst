Configuration
=============

There are three main configuration options to set to have fedocal running

The secret key
---------------

Set in the configuration file under the key ``SECRET_KEY``, this is a unique,
random string which is used by `Flask <http://flask.pocoo.org>`_ to generate
the `CSRF <http://en.wikipedia.org/CSRF>`_ key unique for each user.


You can easily generate one using `pwgen <http://sf.net/projects/pwgen>`_
for example to generate a 50 characters long random key
::

  pwgen 50


The database URL
-----------------

Fedocal uses `SQLAlchemy <http://sqlalchemy.org>`_ has Object Relationship
Mapper and thus to connect to the database. You need to provide under the
key ``DB_URL`` in the configuration file the required information to connect
to the database.


Examples URLs are::

  DB_URL=mysql://user:pass@host/db_name
  DB_URL=postgres://user:pass@host/db_name
  DB_URL=sqlite:////full/path/to/database.sqlite


The admin group
----------------

Fedocal relies on a group of administrator to create calendar which are then
managed by people from this group. The ``ADMIN_GROUP`` field in the
configuration file refers to the
`FAS <https://admin.fedoraproject.org/accounts>`_ group that manages this
fedocal instance.

See :doc:`usage` for details explanations on the different administration layer
of fedocal.

