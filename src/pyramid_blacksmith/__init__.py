import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("pyramid-blacksmith").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass

from .binding import includeme, PyramidBlacksmith

__all__ = ["PyramidBlacksmith", "includeme"]
