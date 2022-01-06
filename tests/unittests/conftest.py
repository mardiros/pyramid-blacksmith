import pytest
from pyramid import testing
from pyramid.config import Configurator
from pyramid.interfaces import IRequestExtensions
from pyramid.request import apply_request_extensions
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
    req = DummyRequest(config=config, **params.get("request", {}))
    exts = config.registry.queryUtility(IRequestExtensions)
    apply_request_extensions(req, exts)
    yield req
    testing.tearDown()
