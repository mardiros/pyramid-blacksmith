Multiple Clients
================

Sometime, projects requires multiple api that require different configuration,
such as different middleware for authentication or discovery mechanism.

The pyramid-blacksmith plugin enabled that by name your client factory.

the default name is ``client``, but it can be override using the
``blacksmith.clients`` setting.

This settings is a list such as

.. code-block:: ini

   blacksmith.clients =
      client_foo
      client_bar

In that case, the ``request.blacksmith`` property will contains to functions,
name ``client_foo`` and ``client_bar`` but there is no ``client``.

Example
-------

ini file
~~~~~~~~
.. literalinclude:: ../../../examples/multi_clients/notif/development.ini
   :language: ini


pyramid views
~~~~~~~~~~~~~

.. literalinclude:: ../../../examples/multi_clients/notif/src/notif/__init__.py
   :language: python
