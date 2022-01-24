from typing import Any, Dict, Generator

import pytest
from blacksmith import PrometheusMetrics
from prometheus_client import CollectorRegistry
from pyramid import testing
from pyramid.config import Configurator
from pyramid.interfaces import IRequestExtensions
from pyramid.request import apply_request_extensions
from pyramid.testing import DummyRequest

from pyramid_blacksmith import includeme


@pytest.fixture
def config(params: Dict[str, Any]):
    config = testing.setUp(settings=params.get("settings", {}))
    config.include(includeme)
    yield config
    testing.tearDown()


@pytest.fixture
def dummy_request(config: Configurator) -> Generator[DummyRequest, None, None]:
    req = DummyRequest(config=config)
    exts: IRequestExtensions = config.registry.queryUtility(IRequestExtensions)
    apply_request_extensions(req, exts)
    yield req
    testing.tearDown()


@pytest.fixture
def registry() -> Generator[CollectorRegistry, None, None]:
    import prometheus_client  # type: ignore

    yield prometheus_client.REGISTRY
    prometheus_client.REGISTRY = CollectorRegistry()


@pytest.fixture
def metrics(
    registry: CollectorRegistry, params: Dict[str, Any]
) -> Generator[PrometheusMetrics, None, None]:
    yield PrometheusMetrics(
        buckets=params.get("metrics", {}).get("buckets"),
        hit_cache_buckets=params.get("metrics", {}).get("hit_cache_buckets"),
        registry=registry,
    )
