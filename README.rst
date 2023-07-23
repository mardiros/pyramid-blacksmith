pyramid-blacksmith
==================

.. image:: https://github.com/mardiros/pyramid-blacksmith/actions/workflows/gh-pages.yml/badge.svg
   :target: https://mardiros.github.io/pyramid-blacksmith/
   :alt: Documentation

.. image:: https://github.com/mardiros/pyramid-blacksmith/actions/workflows/main.yml/badge.svg
   :target: https://github.com/mardiros/pyramid-blacksmith/actions/workflows/main.yml
   :alt: Continuous Integration

.. image:: https://codecov.io/gh/mardiros/pyramid-blacksmith/branch/main/graph/badge.svg?token=9IRABRO2LN
   :target: https://codecov.io/gh/mardiros/pyramid-blacksmith
   :alt: Coverage

Pyramid bindings for `Blacksmith`_ rest api client.


Introduction
------------

This plugin create a request proterty named ``blacksmith`` that bind
clients to do API Call using `Blacksmith`_.


Clients are configured via the pyramid configurator and its settings.

Then you can access the client factory behind a blacksmith property of
the request.


::

   def my_view(request):
      api_dummy = request.blacksmith.client("api_dummy")
      dummy = api_dummy.dummies.get({"name": "alice"})


In the example above, a dummy resource has been fetch using the service api_dummy.
The client method is a configured `Blacksmith Factory`_.

The configuration of the factory is simply made throw the pyramid configurator.

Go ahead and `get familiar with the documentation`_.


.. _`Blacksmith`: https://mardiros.github.io/blacksmith/index.html
.. _`Blacksmith Factory`: https://mardiros.github.io/blacksmith/user/instanciating_clients.html
.. _`get familiar with the documentation`: https://mardiros.github.io/blacksmith/index.html

