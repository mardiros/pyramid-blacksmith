Middlewares Factories
=====================

The middleware factory differ from the middleware in their need and usage.
A middleware is global, and, sometimes, middleware data may differ per 
incoming requests.

The middleware factory, build a middleware and inject in in the blacksmith
client on instanciation.

The main use case is for forwardin header

Forward http headers
--------------------

The list of middleware are defined under the 
setting key ``blacksmith.client.middlewares_factories``, as in the example above.

.. code-block:: ini

   blacksmith.client.middlewares_factories =
      forward_header

   blacksmith.client.middlewares_factory.forward_header =
      Authorization

Then each middleware should be configured under the key
``blacksmith.client.middleware.<name>`` such as
``blacksmith.client.middleware.forward_header`` in the example below.

In this example, the ``forward_header`` middleware factory
will forward the ``Authorization`` header if present in the Pyramid request,
to every blacksmith instanciated clients without writing a line of code.


Custom Middleware Factory
-------------------------

To load a custom middleware, a class can be passed on the same line

.. code-block:: ini

   blacksmith.client.middlewares_factories =
      mybuilder  my.own.module:MyMiddlewareBuilder


In the example above, the class ``MyMiddlewareBuilder`` overrides the class
:class:`pyramid_blacksmith.AbstractMiddlewareFactoryBuilder`.
