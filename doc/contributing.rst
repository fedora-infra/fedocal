Contributing
============

If you're submitting patches to fedocal, please observe the following:

- Check that your python code is `PEP8-compliant
  <http://www.python.org/dev/peps/pep-0008/>`_.  There is a `pep8 tool
  <http://pypi.python.org/pypi/pep8>`_ that can automatically check
  your source.

- Check your code quality usint `pylint <http://pypi.python.org/pypi/pylint>`_.
  The ``run_pylint.sh`` allows you to run pylint for the whole project which
  solves some problem that you might find if you run pylint on your file alone.

- Check that your code doesn't break the test suite.  The test suite can be
  run using the ``run_tests.sh`` shell script at the top of the sources.
  See :doc:`development` for more information about the test suite.

- If you are adding new code, please write tests for them in ``fedocal/tests/``,
  the ``run_tests.sh`` script will help you to see the coverage of your code
  in unit-tests.

- If your change warrants a modification to the docs in ``doc/`` or any
  docstrings in ``fedocal/`` please make that modification.

.. note:: You have a doubt, you don't know how to do something, you have an
   idea but don't know how to implement it, you just have something bugging
   you?

   Come to see us on IRC: ``#fedora-apps`` on irc.freenode.net or via the
   `trac of the project <http://fedorahosted.org/fedocal/>`_.
