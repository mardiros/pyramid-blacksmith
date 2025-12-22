import json
from typing import Any, cast

import pytest
from blacksmith import SyncPrometheusMiddleware
from blacksmith.domain.model.middleware.circuit_breaker import PrometheusHook
from blacksmith.domain.model.middleware.http_cache import CacheControlPolicy
from blacksmith.domain.model.middleware.prometheus import PrometheusMetrics
from blacksmith.middleware._sync.zipkin import SyncZipkinMiddleware
from purgatory import SyncInMemoryUnitOfWork
from pyramid.config import ConfigurationError
from redis import Redis

from pyramid_blacksmith.middleware import (
    CircuitBreakerBuilder,
    HTTPCacheBuilder,
    HTTPStaticHeadersBuilder,
    PrometheusMetricsBuilder,
    ZipkinBuilder,
)
from tests.unittests.fixtures import (
    DummyCachePolicy,
    DummyPurgatoryUow,
    DummySerializer,
)


@pytest.mark.parametrize(
    "params",
    [{}],
)
def test_prometheus_metrics_builder(
    metrics: PrometheusMetrics,
):
    builder = PrometheusMetricsBuilder({}, "key", metrics)
    prom = builder.build()
    assert isinstance(prom, SyncPrometheusMiddleware)


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "key": """
                """
            },
            "expected_threshold": 5,
            "expected_ttl": 30,
            "expected_uow": SyncInMemoryUnitOfWork,
        },
        {
            "settings": {
                "key": """
                    threshold 10
                    ttl       42
                    uow       tests.unittests.fixtures:DummyPurgatoryUow
                """,
                "key.uow": """
                    url redis://desir/0
                """,
            },
            "expected_threshold": 10,
            "expected_ttl": 42,
            "expected_uow": DummyPurgatoryUow,
            "expected_uow_url": "redis://desir/0",
        },
    ],
)
def test_circuit_breaker(params: dict[str, Any], metrics: PrometheusMetrics):
    builder = CircuitBreakerBuilder(params["settings"], "key", metrics)
    circuit = builder.build()
    assert circuit.circuit_breaker.default_threshold == params["expected_threshold"]
    assert circuit.circuit_breaker.default_ttl == params["expected_ttl"]
    assert len(circuit.circuit_breaker.listeners) == 1  # type: ignore
    assert isinstance(
        next(iter(circuit.circuit_breaker.listeners.keys())),  # type: ignore
        PrometheusHook,
    )
    assert isinstance(circuit.circuit_breaker.uow, params["expected_uow"])
    if "expected_uow_url" in params:
        assert (
            cast(DummyPurgatoryUow, circuit.circuit_breaker.uow).url
            == params["expected_uow_url"]
        )


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "key": """
                    redis   redis://foo.localhost/0
                """
            },
            "expected_redis": {"db": 0, "host": "foo.localhost"},
            "expected_policy": CacheControlPolicy,
            "expected_policy_param": ("sep", "$"),
            "expected_serializer": json,
        },
        {
            "settings": {
                "key": """
                    redis   redis://foo.localhost/0
                """,
                "key.policy": """
                    sep   |
                """,
            },
            "expected_redis": {"db": 0, "host": "foo.localhost"},
            "expected_policy": CacheControlPolicy,
            "expected_policy_param": ("sep", "|"),
            "expected_serializer": json,
        },
        {
            "settings": {
                "key": """
                    redis       redis://foo.localhost/0
                    policy      tests.unittests.fixtures:DummyCachePolicy
                    serializer  tests.unittests.fixtures:DummySerializer
                """,
                "key.policy": """
                    foo   bar
                """,
            },
            "expected_redis": {"db": 0, "host": "foo.localhost"},
            "expected_policy": DummyCachePolicy,
            "expected_policy_param": ("foo", "bar"),
            "expected_serializer": DummySerializer,
        },
    ],
)
def test_http_caching_builder(params: dict[str, Any], metrics: PrometheusMetrics):
    cachingb = HTTPCacheBuilder(params["settings"], "key", metrics)
    caching = cachingb.build()
    assert (
        cast(Redis, caching._cache).connection_pool.connection_kwargs
        == params["expected_redis"]
    )
    assert isinstance(caching._policy, params["expected_policy"])
    assert caching._serializer is params["expected_serializer"]
    assert (
        getattr(caching._policy, params["expected_policy_param"][0])  # type: ignore
        == params["expected_policy_param"][1]
    )


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "key": """
                """
            },
        },
        {
            "settings": {},
        },
    ],
)
def test_http_caching_builder_error(params: dict[str, Any], metrics: PrometheusMetrics):
    cachingb = HTTPCacheBuilder(params["settings"], "key", metrics)
    with pytest.raises(ConfigurationError) as ctx:
        cachingb.build()
    assert str(ctx.value) == "Missing sub-key redis in setting key"


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "key": """
                    Authorization: Bearer abcdef
                    User-Agent: blacksmith
                """,
            },
            "headers": {"Authorization": "Bearer abcdef", "User-Agent": "blacksmith"},
        },
    ],
)
def test_http_add_headers(params: dict[str, Any], metrics: PrometheusMetrics):
    headersb = HTTPStaticHeadersBuilder(params["settings"], "key", metrics)
    headers = headersb.build()
    assert headers.headers == params["headers"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {},
            "headers": {"Authorization": "Bearer abcdef", "User-Agent": "blacksmith"},
        },
    ],
)
def test_zipkin_middleware(params: dict[str, Any], metrics: PrometheusMetrics):
    zkb = ZipkinBuilder(params["settings"], "key", metrics)
    zkm = zkb.build()
    assert isinstance(zkm, SyncZipkinMiddleware)
