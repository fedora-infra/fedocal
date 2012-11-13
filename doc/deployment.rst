Deployment
==========

From sources
------------

Clone the source::

 git clone https://github.com/pypingou/fedocal.git


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

Copy this file into ``/etc/`` with the name ``fedocal.cfg``::

  cp /path/to/fedocal.cfg.sample /etc/fedocal.cfg

Find the file used to create the database::

  rpm -ql fedocal |grep model.py

Create the database scheme::

   python path/to/fedocal/fedocallib/model.py

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

 
 import fedocal
 application = fedocal.APP

.. note:: If you run form the sources, you might have to add at the
         top of the file ::

            import sys
            sys.path.insert(0, '/srv/fedocal/')

         Adapt the path to your configuration
 

Then restart apache and you should be able to access the website on
http://localhost/fedocal


.. note:: `Flask <http://flask.pocoo.org/>`_ provides also  some documentation
          on how to `deploy Flask application with WSGI and apache
          <http://flask.pocoo.org/docs/deploying/mod_wsgi/>`_.


For testing
-----------

See :doc:`development` if you want to run fedocal just to test it.

