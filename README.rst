bluesnow
========

BlueSnow is a basic tool powered by pip that packages your Python applications into a
single script.

Note that, at the moment, custom package data is not supported.

Installation
************

::

  $ pip install bluesnow

Usage via setup.py plugin
*************************

Put this in your ``setup.py``:

.. code-block:: python

  try:
      import bluesnow
      cmdclass = bluesnow.setuptools_cmdclass
  except ImportError:
      cmdclass = {}

  setup(
      # Normal stuff here...
      cmdclass=cmdclass,
  )

Now just run ``python setup.py bluesnow`` to compile your entry points. The results will
be placed in the ``bluesnow-out`` directory.

Usage from command line
***********************

You can also use BlueSnow from the command line, e.g.::

  $ bluesnow 'my_entry_point = my_module:my_function'

The entry points follow the `standard entry point specification
<http://setuptools.readthedocs.io/en/latest/pkg_resources.html#creating-and-parsing>`_. Use
``bluesnow -h`` for more options.
