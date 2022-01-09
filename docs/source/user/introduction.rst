Introduction
============

``pyramid_blacksmith`` is available on PyPI, it can be installed
using pip.

::

   pip install pyramid_blacksmith


Or adding to a project using poetry by using

::

   poetry add pyramid_blacksmith


After wath, the library has to be configured throw the pyramid 
configurator using the command

::

   with Configurator(settings=settings) as config:
      config.include('pyramid_blacksmith')


in the code or using the `.ini` file configuration


::

   pyramid.includes =
      pyramid_blacksmith



To finalize the client factory, the configuration is required and will be
documented in the next chapter.