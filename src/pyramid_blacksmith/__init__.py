from importlib import metadata

from .binding import PyramidBlacksmith, includeme
from .middleware import AbstractMiddlewareBuilder
from .middleware_factory import AbstractMiddlewareFactoryBuilder

__version__ = metadata.version("pyramid_blacksmith")

__all__ = [
    "AbstractMiddlewareBuilder",
    "AbstractMiddlewareFactoryBuilder",
    "PyramidBlacksmith",
    "includeme",
]
