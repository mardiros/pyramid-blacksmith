from importlib import metadata

from .binding import PyramidBlacksmith, includeme
from .middleware import AbstractMiddlewareBuilder
from .middleware_factory import AbstractMiddlewareFactoryBuilder

__version__ = metadata.version("blacksmith")

__all__ = [
    "PyramidBlacksmith",
    "includeme",
    "AbstractMiddlewareBuilder",
    "AbstractMiddlewareFactoryBuilder",
]
