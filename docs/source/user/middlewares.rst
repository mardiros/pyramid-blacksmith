.. _`Middlewares`:

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

   # Optional configuration for the buckets
   blacksmith.prometheus_buckets =
       buckets            0.05  0.1  0.2  0.4  1.6  3.2  6.4  12.8  25.6
       hit_cache_buckets 0.005 0.01 0.02 0.04 0.16 0.32 0.64 0.128 0.256

   blacksmith.client.middlewares =
      prometheus

.. note::

   The ``hit_cache_buckets`` setting is used by the :ref:`HTTP Cache Middleware`.

   The prometheus middleware alone is only used to track metrics HTTP queries.


Circuit Breaker Middleware
--------------------------

.. code-block:: ini

   blacksmith.client.middlewares =
      circuitbreaker

   # Optional configurations
   blacksmith.client.middleware.circuitbreaker =
      threshold   7
      ttl         42

The ``threshold`` is the maximum number of consecutive failure to attempt
before opening the circuit. The ``ttl`` is the number of second the circuit
stay open.

.. note::

   | Blacksmith circuit breaker is based on `purgatory`.
   | Read the `purgatory`_ documentation for more information.

.. _`purgatory`: https://mardiros.github.io/purgatory/


Collect Circuit Breaker in prometheus
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

To properly works together, middleware must be added in this order:

.. code-block:: ini

   blacksmith.client.middlewares =
      prometheus
      circuitbreaker


Using redis as a storage backend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: ini

   blacksmith.client.middlewares =
      circuitbreaker

   blacksmith.client.middleware.circuitbreaker =
      uow   purgatory:SyncRedisUnitOfWork

   blacksmith.client.middleware.circuitbreaker.uow =
      url   redis://host.example.net/42


.. _`HTTP Cache Middleware`:

HTTP Cache Middleware
---------------------

.. code-block:: ini

   blacksmith.client.middlewares =
      http_cache

   blacksmith.client.middleware.http_cache =
      redis       redis://foo.localhost/0


To override the policy, or the serializal some additional configuration
keys are avaiable:


.. code-block:: ini

    blacksmith.client.middleware.http_cache =
         redis       redis://foo.localhost/0
         policy      path.to.module:SpecificCachePolicy
         serializer  path.to.module:SpecificSerializer

   blacksmith.client.middleware.http_cache.policy =
      key val
      key2 val2


In that case, the class ``SpecificCachePolicy`` has been created
in the ``path.to.module`` and implement the ``AbscractCachePolicy``
of blacksmith. The contructor accept parameter ``key`` and ``key2``.
Note that, to keep the configuration readable, those parameters must be
of type ``str``.

By default, the ``serializer`` is using ``json``. The key ``serializer``
``path.to.module:SpecificSerializer``. The ``AbstractSerializer`` of blacksmith
must be implemented.
