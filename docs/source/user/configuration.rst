Configuration
=============

pyramid_blacksmith is configuring the clients using the ``settings``
of the pyramid `configurator`_, usually loaded via a ``paste.ini`` file format.

The configuration here will use this format for clarity.

.. _`configurator`: https://docs.pylonsproject.org/projects/pyramid/en/latest/api/config.html#pyramid.config.Configurator


Include pyramid_blacksmith as a pyramid plugin
----------------------------------------------

If you read the Pyramid documentation, there are many way to initialize its Configurator,
lets go straigth to the point, by loging the plugin using the pyramid depencency injection.


.. code-block:: python

   def includeme(config):
      # Load the blacksmith binding
      config.include('pyramid_blacksmith')


The line above will read the configuration bellow from the `config.registry.settings`.


Loading resources
-----------------

The first setting is used to fillout the blacksmith registry.

.. code-block:: ini

   blacksmith.scan =
      my.resources
      maybe.another.resources


.. note::

   The resources is a list of `packages`_.

.. _`packages`: https://docs.python.org/3/tutorial/modules.html#packages


Service Discovery
-----------------

A service discovery method has to be configured, and blacksmith discover
can be choosen following the example bellow.


Example using a static
~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: sd/static.ini
   :language: ini


Example using a consul
~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: sd/consul.ini
   :language: ini


Example using the router
~~~~~~~~~~~~~~~~~~~~~~~~

.. literalinclude:: sd/router.ini
   :language: ini


.. note::

   This strategy is perfect for testing too.
   You can use the following section in your test.ini file.

   .. literalinclude:: sd/router-in-test.ini
      :language: ini


Timeout
-------

.. code-block:: ini

   blacksmith.client.read_timeout = 5
   blacksmith.client.connect_timeout = 2


Proxies
-------

.. code-block:: ini

   blacksmith.client.proxies =
      http://   https://letmeout.example.net:8443/
      https://  https://letmeout.example.net:8443/




Disable Certificate Verification
--------------------------------

.. code-block:: ini

   blacksmith.client.verify_certificate = false


.. important::

   | This let your application vulnerable to man-in-the-middle.
   | Great power came with great responsabilities.


Updating the collection parser
------------------------------

While consuming API that does not do bared collection, a collection parser
has to be set in blacksmith to change the ``collection_get`` method that
deserialize and build back the pyrantic model.

.. code-block:: ini

   blacksmith.client.collection_parser = path.to.module:MyCollectionParser


Updating the error parser
------------------------------

While consuming API, the unboxed error is by default a HTTPError, to add
a generic parser for a whole client factory, the path to the error_parser
can be provided as a setting.

.. code-block:: ini

   blacksmith.client.error_parser = path.to.module:MyErrorParser


Middlewares
-----------

The blacksmith middlewares can also be configured using the configurator,
this is going to be documented in the next chapters.

In blacksmith, there are global middlewares per ``ClientFactory``, and
there are middlewares per ``Client``. Global :ref:`middlewares` are usefull for
metrics, tracing, caching, but they are not usesull for authentication in
a multi user application. :ref:`Middleware Factories` are usefull for that
purpose.
