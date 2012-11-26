Deployment
==========

From sources
------------

Clone the source::

 git clone http://git.fedorahosted.org/git/fedocal.git


Copy the configuration file::

  cp fedocal.cfg.sample fedocal.cfg

Adjust the configuration file (secret key, database URL, admin group...).
See :doc:`configuration` for detailed information about the configuration.


Create the database scheme::

   python fedocal/fedocallib/model.py

Set up the WSGI as described below.


From system-wide packages
-------------------------

Start by install fedocal::

  yum install fedocal

Find the sample configuration file::

  rpm -ql fedocal |grep fedocal.cfg.sample

Copy this file into (for example) ``/etc/`` with the name ``fedocal.cfg``::

  cp /path/to/fedocal.cfg.sample /etc/fedocal.cfg

Find the file used to create the database::

  rpm -ql fedocal |grep createdb.py

Create the database scheme::

   FEDOCAL_CONFIG=/etc/fedocal/cfg python path/to/createdb.py

Set up the WSGI as described below.


Set-up WSGI
-----------

Start by installing ``mod_wsgi``::

  yum install mod_wsgi


Then configure apache::

 sudo vim /etc/httd/conf.d/wsgi.conf

and put in this file::

  WSGIScriptAlias /fedocal /var/www/wsgi/fedocal.wsgi
  <Directory /var/www/wsgi/>
      Order deny,allow
      Allow from all
  </Directory>


Then create the file /var/www/wsgi/fedocal.wsgi with::

 import os
 os.environ['FEDOCAL_CONFIG'] = '/etc/fedocal.cfg'
 
 import fedocal
 application = fedocal.APP

.. note:: If you run form the sources, you might have to add at the
         top of the file ::

            import sys
            sys.path.insert(0, '/srv/fedocal/')

         Adapt the path to your configuration


.. seealso:: Within the sources of fedocal is a ``fedocal.wsgi`` which
             can be used as a template for your own wsgi.
 

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

 */30 * * * *  FEDOCAL_CONFIG=/etc/fedocal.cfg python /path/to/fedocal_cron.py




For testing
-----------

See :doc:`development` if you want to run fedocal just to test it.

