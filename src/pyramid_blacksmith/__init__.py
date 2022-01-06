import pkg_resources

try:
    __version__ = pkg_resources.get_distribution("pyramid_blacksmith").version
except pkg_resources.DistributionNotFound:
    # read the doc does not support poetry
    pass
