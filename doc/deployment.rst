Deployment
==========

From sources
------------

Clone the source::

 git clone http://git.fedorahosted.org/git/fedocal.git


Copy the configuration files::

  cp fedocal.cfg.sample fedocal.cfg
  cp alembic.ini.sample alembic.ini

Adjust the configuration files (secret key, database URL, admin group...).
See :doc:`configuration` for detailed information about the configuration.


Create the database scheme::

   sh createdb

or::

   FEDOCAL_CONFIG=/path/to/fedocal.cfg python createdb.py

Set up the WSGI as described below.


From system-wide packages
-------------------------

Start by install fedocal::

  yum install fedocal

Adjust the configuration files: ``/etc/fedocal/fedocaf.cfg`` and
``/etc/fedocal/alembic.ini``.
See :doc:`configuration` for detailed information about the configuration.

Find the file used to create the database::

  rpm -ql fedocal |grep createdb.py

Create the database scheme::

   FEDOCAL_CONFIG=/etc/fedocal/fedocal.cfg python path/to/createdb.py

Set up the WSGI as described below.


Set-up WSGI
-----------

Start by installing ``mod_wsgi``::

  yum install mod_wsgi


Then configure apache::

 sudo vim /etc/httd/conf.d/fedocal.conf

uncomment the content of the file and adjust as desired.


Then edit the file ``/usr/share/fedocal/fedocal.wsgi`` and
adjust as needed.


Then restart apache and you should be able to access the website on
http://localhost/fedocal


.. note:: `Flask <http://flask.pocoo.org/>`_ provides also  some documentation
          on how to `deploy Flask application with WSGI and apache
          <http://flask.pocoo.org/docs/deploying/mod_wsgi/>`_.


Set-up the cron job
-------------------

Reminders are sent by a cron job which is provided with the source under
the name ``fedocal_cron.py``.

You will need to specified the ``FEDOCAL_CONFIG`` environment variable
when running the cron job as the specified configuration file contains
information required by the cron job (ie: SMTP_SERVER or CRON_FREQUENCY,
see :doc:`configuration`).

The only tricky part is that the configuration file will need to be
adjusted according to how the cron job is set-up. See :doc:`configuration`
on how to set-up the configuration file.

Example of the cron job:

::

 */30 * * * *  FEDOCAL_CONFIG=/etc/fedocal/fedocal.cfg /usr/bin/fedocal_cron.py



For testing
-----------

See :doc:`development` if you want to run fedocal just to test it.

