Development
===========

Get the sources
---------------

Anonymous:

::

  git clone https://pagure.io/fedocal.git

Contributors:

::

  git clone ssh://<FAS user>@git.pagure.io/fedocal.git


Dependencies
------------

The dependencies of fedocal are listed in the file ``requirements.txt``
at the top level of the sources.


.. note:: if you work in a `virtualenv <http://www.virtualenv.org/en/latest/>`_
          the installation of python-fedora might fail the first time you
          try, just try to run the command twice, the second time it should
          work.


Run fedocal for development
---------------------------
Copy the configuration file::

 cp fedocal.cfg.sample fedocal.cfg

Adjust the configuration file (secret key, database URL, admin group...)
See :doc:`configuration` for more detailed information about the
configuration.

::

 cp alembic.ini.sample alembic.ini

Adjust the database url to be the same as in ``fedocal.cfg``.

.. note:: You can use the follow entry in ``fedocal.cfg`` when working on a
          development version of fedocal::

            import os
            PATH_ALEMBIC_INI=os.path.join(
                os.path.dirname(__file__), 'alembic.ini')

Create the database scheme::

  ./createdb

Run the server::

  ./runserver

You should be able to access the server at http://localhost:5000


Every time you save a file, the project will be automatically restarted
so you can see your change immediatly.


Coding standards
----------------

We are trying to make the code `PEP8-compliant
<http://www.python.org/dev/peps/pep-0008/>`_.  There is a `pep8 tool
<http://pypi.python.org/pypi/pep8>`_ that can automatically check
your source.


We are also inspecting the code using `pylint
<http://pypi.python.org/pypi/pylint>`_ and aim of course for a 10/10 code
(but it is an assymptotic goal).
We provide a shell script ``run_pylint.sh`` at the top of the sources to
allow easy inspection of the code with pylint.

.. note:: both pep8 and pylint are available in Fedora via yum:

          ::

            yum install python-pep8 pylint


Send patch
----------

The easiest way to work on fedocal is to make your own branch in git, make
your changes to this branch, commit whenever you want, rebase on master,
whenever you need and when you are done, send the patch either by email or
via the trac.


The workflow would therefore be something like:

::

   git branch <my_shiny_feature>
   git checkout <my_shiny_feature>
   <work>
   git commit file1 file2
   <more work>
   git commit file3 file4
   git checkout master
   git pull
   git checkout <my_shiny_feature>
   git rebase master
   git format-patch -2

This will create two patch files that you can send by email to submit in the
trac.

.. note:: You can send your patch by email to the `fedocal mailing-list
          <https://lists.fedoraproject.org/archives/list/fedocal@lists.fedorahosted.org/>`_


Unit-tests
----------

Fedocal has a number of unit-tests providing at the moment a full coverage of
the backend library (fedocallib).


We aim at having a full (100%) coverage of the whole code (including the
Flask application) and of course a smart coverage as in we want to check
that the functions work the way we want but also that they fail when we
expect it and the way we expect it.


Tests checking that function are failing when/how we want are as important
as tests checking they work the way they are intended to.

``run_tests.sh``, located at the top of the sources, helps to run the
unit-tests of the project with coverage information using `python-nose
<https://nose.readthedocs.org/>`_.


.. note:: You can specify additional arguments to the nose command used
          in this script by just passing arguments to the script.

          For example you can specify the ``-x`` / ``--stop`` argument:
          `Stop running tests after the first error or failure` by just doing

          ::

            ./run_tests.sh --stop


Each unit-tests files (located under ``fedocal/tests/``) can be called
by alone, allowing easier debugging of the tests. For example:

::

  python fedocal/tests/test_week.py

Similarly as for nose you can also ask that the unit-test stop at the first
error or failure. For example, the command could be:

::

  FEDOCAL_CONFIG=tests/fedocal_test.cfg python -m unittest -f -v fedocal.tests.test_week


.. note:: In order to have coverage information you might have to install
          ``python-coverage``

          ::

            yum install python-coverage


Database changes
----------------

We try to make the database schema as stable as possible, however once in a
while we need to change it to add new features or information.


When database changes are made, they should have the corresponding change
handled via `alembic <http://pypi.python.org/pypi/alembic>`_.


See the `alembic tutorial
<http://alembic.readthedocs.org/en/latest/tutorial.html>`_ for complete
information on how to make a revision to the database schema.


The basic idea is to create a revision using (in the top folder):

::

  alembic revision -m "<description of the change>"

Then edit the file generated in alembic/versions/ to add the correct command
for upgrade and downgrade (for example: ``op.add_column``, ``op.drop_column``,
``op.create_table``, ``op.drop_table``).


Translations
------------

Strings are translated using gettext and the Flask-Babel extension. All UI
strings have to be translatable.

In order to get Fedocal happy even if Flask-Babel is missing, we provide some
wrappers via `fedocal_babel` that must be used instead of requiring directly
Flask-Babel methods.

In core Python code, you'll have to import the wrapper, and use the `gettext` function::

   from fedocal.fedocal_babel import gettext
   [...]
   str = gettext("Translate this!")

   from fedocal.fedocal_babel import gettext
   [...]
   str = gettext("%(count)s translations found!", count=256)

In Jinja templates, just use the `_()` function::

   <p>{{ _('Fedocal is awesome!') }}</a>
   <p>{{ _('%(users)s in the world use it.', users=2000000) }}</p>

Once you've added new strings, you'lla have to extract them::

   pybabel extract -F babel.cfg -o messages.pot fedocal

And finally, update the `po` file::

   pybabel update -i messages.pot -d fedocal/translations


Troubleshooting
---------------

+ Login fails in development mode

  The Flask FAS extension requires a secure cookie which ensures that it is
  always encrypted during client/server exchanges.
  This makes the authentication cookie less likely to be exposed to cookie
  theft by eavesdropping.

  You can disable the secure cookie for testing purposes by setting the
  configuration key ``FAS_HTTPS_REQUIRED`` to False.

  .. WARNING::
     Do not use this option in production as it causes major security issues

