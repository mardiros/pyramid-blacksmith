from typing import cast
import pytest
from blacksmith import __version__ as blacksmith_version
from blacksmith.middleware._sync.circuit_breaker import PrometheusHook
from purgatory import SyncInMemoryUnitOfWork

from pyramid_blacksmith.middleware import (
    CircuitBreakerBuilder,
    PrometheusMetricsBuilder,
)
from tests.unittests.fixtures import DummyPurgatoryUow


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "key": """
                """
            },
            "expected_buckets": [0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6],
        },
        {
            "settings": {
                "key": """
                    buckets     .5 1 5 10
                """
            },
            "expected_buckets": [0.5, 1.0, 5.0, 10.0],
        },
    ],
)
def test_prometheus_metrics_builder(registry, params):
    promb = PrometheusMetricsBuilder(params["settings"], "key", {})
    prom = promb.build()
    val = registry.get_sample_value(
        "blacksmith_info", labels={"version": blacksmith_version}
    )
    assert val == 1.0
    assert (
        prom.blacksmith_request_latency_seconds._kwargs["buckets"]
        == params["expected_buckets"]
    )


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
def test_circuit_breaker(registry, params):
    circuitb = CircuitBreakerBuilder(params["settings"], "key", {})
    circuit = circuitb.build()
    assert circuit.circuit_breaker.default_threshold == params["expected_threshold"]
    assert circuit.circuit_breaker.default_ttl == params["expected_ttl"]
    assert len(circuit.circuit_breaker.listeners) == 0
    assert isinstance(circuit.circuit_breaker.uow, params["expected_uow"])
    if "expected_uow_url" in params:
        assert (
            cast(DummyPurgatoryUow, circuit.circuit_breaker.uow).url
            == params["expected_uow_url"]
        )


@pytest.mark.parametrize("params", [{}])
def test_circuit_breaker_with_prometheus(registry):
    prometheus = PrometheusMetricsBuilder({}, "k", {}).build()
    circuitb = CircuitBreakerBuilder({}, "key", {"prometheus": prometheus})
    circuit = circuitb.build()
    assert len(circuit.circuit_breaker.listeners) == 1
    assert isinstance(list(circuit.circuit_breaker.listeners.keys())[0], PrometheusHook)
