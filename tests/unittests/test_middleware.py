import pytest
from blacksmith import __version__ as blacksmith_version
from prometheus_client import CollectorRegistry

from pyramid_blacksmith.middleware import PrometheusMetricsBuilder


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {},
            "expected_buckets": [0.05, 0.1, 0.2, 0.4, 0.8, 1.6, 3.2, 6.4, 12.8, 25.6],
        },
        {
            "settings": {
                "key.buckets": """
                    .5 1 5 10
                """
            },
            "expected_buckets": [0.5, 1.0, 5.0, 10.0],
        },
    ],
)
def test_prometheus_metrics_builder(params):
    registry = CollectorRegistry()
    promb = PrometheusMetricsBuilder(params["settings"], "key")
    prom = promb.build(registry)
    val = registry.get_sample_value(
        "blacksmith_info", labels={"version": blacksmith_version}
    )
    assert val == 1.0
    assert (
        prom.blacksmith_request_latency_seconds._kwargs["buckets"]
        == params["expected_buckets"]
    )
