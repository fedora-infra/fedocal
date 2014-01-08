Configuration
=============

There are the main configuration options to set to have fedocal running.
These options are all present and described in the fedocal.cfg file.

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


.. note:: The key ``sqlalchemy.url`` of the ``alembic.ini`` file should
          have the same value as the ``DB_URL`` described here.


The admin group
----------------

Fedocal relies on a group of administrator to create calendar which are then
managed by people from this group. The ``ADMIN_GROUP`` field in the
configuration file refers to the
`FAS <https://admin.fedoraproject.org/accounts>`_ group that manages this
fedocal instance.

See :doc:`usage` for details explanations on the different administration layer
of fedocal.


The SMTP server address
-----------------------

Fedocal sends reminder emails for the meeting for which it has been asked.
This tasks is performed by a cron job.
The ``SMTP_SERVER`` field in the configuration file refers to the address
of the `SMTP <http://en.wikipedia.org/wiki/Simple_Mail_Transfer_Protocol>`_
server to use to send these reminders.


This field defaults to ``SMTP_SERVER='localhost'``.


The cron job frequency
----------------------

Fedocal sends reminder emails for the meeting for which it has been asked.
This tasks is performed by a cron job.
The ``CRON_FREQUENCY`` field in the configuration file refers to the
time (in minute) spent between two consecutive run of the cron job. This
information is essentiel to accurately retrieve the meetings to remind
and avoid sending multiple reminder for one meeting.


This field defaults to ``CRON_FREQUENCY=30``.


Dedicated theme
---------------

Fedocal supports having multiple theme. To make your own theme, copy the
theme `default` and adjust it as desired.

Remember:
* All the templates from the default theme should exists in your own theme
* Copy the templates and the static files

You can then change from one theme to another simply by using the configuration
key ``THEME_FOLDER`` in the configuration file.

.. note:: the template and static file of the theme should be located under
        the default ``template`` and ``static`` folder, where are currently
        located to folder named ``default`` representing the default theme.
