from pyramid.config import Configurator
from pyramid.interfaces import IRequestExtensions
import pytest
from pyramid import testing
from pyramid.testing import DummyRequest
from pyramid_blacksmith import includeme


@pytest.fixture
def config():
    config = testing.setUp()
    config.include(includeme)
    yield config
    testing.tearDown()


@pytest.fixture
def dummy_request(config: Configurator, params=None):
    params = params or {}
    req = DummyRequest(config=config, **params.get('request', {}))
    ext = config.registry.queryUtility(IRequestExtensions)
    for key, val in ext.descriptors.items():
        setattr(req.__class__, key, val)
    yield req
    testing.tearDown()

