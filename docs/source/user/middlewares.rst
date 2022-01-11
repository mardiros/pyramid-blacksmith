Middlewares
===========

Blacksmith middleware can be configured using the configurator.


Loading middlewares
-------------------

The list of middleware are defined under the 
setting key ``blacksmith.client.middlewares``, as in the example above.

.. code-block:: ini

   blacksmith.client.middlewares =
      prometheus

Then each middleware should be configured under the key
``blacksmith.client.middleware.<name>`` such as
``blacksmith.client.middleware.prometheus`` in the previous example.

To load a custom middleware, a class can be passed on the same line

.. code-block:: ini

   blacksmith.client.middlewares =
      mybuilder  my.own.module:MyMiddlewareBuilder


In the example above, the class ``MyMiddlewareBuilder`` overrides the class
:class:`pyramid_blacksmith.AbstractMiddleware`.


Prometheus Middleware
---------------------

.. code-block:: ini

   blacksmith.client.middlewares =
      prometheus

   # Optional configuration for the buckets
   blacksmith.client.middleware.prometheus =
       buckets 0.05 0.1 0.2 0.4 1.6 3.2 6.4 12.8 25.6
