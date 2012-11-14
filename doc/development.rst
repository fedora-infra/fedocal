Development
===========

Get the sources
---------------

Anonymous:

::

  git clone http://git.fedorahosted.org/git/fedocal.git

Contributors:

::

  git clone ssh://<FAS user>@git.fedorahosted.org/git/fedocal.git


Run fedocal for development
---------------------------
Copy the configuration file::

 cp fedocal.cfg.sample fedocal.cfg

Adjust the configuration file (secret key, database URL, admin group...)
See :doc:`configuration` for more detailed information about the configuration.


Create the database scheme::

  python fedocal/fedocallib/model.py

Run the server::

  python fedocal/__init__.py

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
We provide a shell script ``run_pylint.sh`` at the top of the sources to allow
easy inspection of the code with pylint.

.. note:: both pep8 and pylint are available in Fedora via yum:

          ::

            yum install python-pep8 pylint


Send patch
----------

The easiest way to work on fedocal is to make your own branch in git, make your
changes to this branch, commit whenever you want, rebase on master, whenever
you need and when you are done, send the patch either by email or via the trac.


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
          <https://lists.fedorahosted.org/mailman/listinfo/fedocal>`_

Unit-tests
----------

Fedocal has a number of unit-tests providing at the moment a full coverage of
the backend library (fedocallib).


We aim at having a full (100%) coverage of the whole code (including the Flask
application) and of course a smart coverage as in we want to check that the
functions work the way we want but also that they fail when we expect it and
the way we expect it.


Tests checking that function are failing when/how we want are as important
as tests checking they work the way they are intended to.

``run_tests.sh``, located at the top of the sources, helps to run the
unit-tests of the project with coverage information using `python-nose
<https://nose.readthedocs.org/>`_.


Each unit-tests files (located under ``fedocal/tests/``) can be called
by alone, allowing easier debugging of the tests. For example:

::

  python fedocal/tests/test_week.py


Database changes
----------------

We try to make the database schema as stable as possible, however once in a
while we need to change it to add new features or information.


When database changes are made, they should have the corresponding change
handled via `alembic <http://pypi.python.org/pypi/alembic>`_.


See the `alembic tutorial
<http://alembic.readthedocs.org/en/latest/tutorial.html>`_ for more information
on how to make a revision to the database schema.
