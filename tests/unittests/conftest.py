from prometheus_client import CollectorRegistry
import pytest
from pyramid import testing
from pyramid.config import Configurator
from pyramid.interfaces import IRequestExtensions
from pyramid.request import apply_request_extensions
from pyramid.testing import DummyRequest

from pyramid_blacksmith import includeme


@pytest.fixture
def config(params):
    config = testing.setUp(settings=params.get("settings", {}))
    config.include(includeme)
    yield config
    testing.tearDown()


@pytest.fixture
def dummy_request(config: Configurator):
    req = DummyRequest(config=config)
    exts = config.registry.queryUtility(IRequestExtensions)
    apply_request_extensions(req, exts)
    yield req
    testing.tearDown()


@pytest.fixture
def registry(params):
    import prometheus_client

    yield prometheus_client.REGISTRY
    prometheus_client.REGISTRY = CollectorRegistry()
