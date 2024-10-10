import sys
from pathlib import Path
from typing import Any, Dict

from blacksmith.sd._sync.adapters.nomad import SyncNomadDiscovery
import pytest
from blacksmith import HTTPTimeout, PrometheusMetrics
from blacksmith.domain.error import default_error_parser
from blacksmith.domain.model.params import CollectionParser
from blacksmith.domain.registry import registry as blacksmith_registry
from blacksmith.middleware._sync.auth import SyncHTTPBearerMiddleware
from blacksmith.middleware._sync.base import SyncHTTPAddHeadersMiddleware
from blacksmith.middleware._sync.circuit_breaker import SyncCircuitBreakerMiddleware
from blacksmith.middleware._sync.prometheus import SyncPrometheusMiddleware
from blacksmith.middleware._sync.zipkin import SyncZipkinMiddleware
from blacksmith.sd._sync.adapters.consul import SyncConsulDiscovery
from blacksmith.sd._sync.adapters.router import SyncRouterDiscovery
from blacksmith.sd._sync.adapters.static import SyncStaticDiscovery
from blacksmith.service._sync.adapters.httpx import SyncHttpxTransport
from blacksmith.service._sync.client import SyncClientFactory
from prometheus_client import CollectorRegistry  # type: ignore
from pyramid.exceptions import ConfigurationError  # type: ignore
from pyramid.interfaces import IRequestExtensions  # type: ignore

from pyramid_blacksmith.binding import (
    BlacksmithClientSettingsBuilder,
    BlacksmithMiddlewareFactoryBuilder,
    BlacksmithPrometheusMetricsBuilder,
    PyramidBlacksmith,
)
from pyramid_blacksmith.middleware_factory import ForwardHeaderFactoryBuilder

here = Path(__file__).parent.parent.parent
sys.path.insert(0, str(here))
from tests.unittests.fixtures import (  # noqa
    DummyCollectionParser,
    DummyErrorParser,
    DummyMiddleware,
    DummyTransport,
)


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.service_discovery": "consul",
                "blacksmith.client.consul_sd_config": "",
                "blacksmith.scan": "tests.unittests.resources",
            },
        }
    ],
)
def test_includeme(config: Dict[str, Any], registry: CollectorRegistry):
    ext: Any = config.registry.queryUtility(IRequestExtensions)  # type: ignore
    assert "blacksmith" in ext.descriptors

    # check that the scan is loading resources
    assert blacksmith_registry.clients == {
        "api": {"dummy": blacksmith_registry.clients["api"]["dummy"]},
    }
    assert blacksmith_registry.clients["api"]["dummy"].collection is None
    assert (
        blacksmith_registry.clients["api"]["dummy"].resource.path  # type: ignore
        == "/dummies/{name}"
    )


@pytest.mark.parametrize(
    "params",
    [  # type: ignore
        {
            "settings": {
                "blacksmith.client.service_discovery": "router",
                "blacksmith.client.middlewares": ["prometheus", "circuitbreaker"],
                "blacksmith.client.middleware_factories": ["forward_header"],
                "blacksmith.client.middleware_factorie.forward_header": ["foo"],
                "blacksmith.scan": "tests.unittests.resources",
            },
            "expected": {
                "sd": SyncRouterDiscovery,
                "timeout": HTTPTimeout(30, 15),
                "proxies": None,
                "verify": True,
                "transport": SyncHttpxTransport,
                "collection_parser": CollectionParser,
                "middlewares": [
                    SyncCircuitBreakerMiddleware,
                    SyncPrometheusMiddleware,
                ],
                "middleware_factories": [
                    SyncHTTPAddHeadersMiddleware,
                    SyncCircuitBreakerMiddleware,
                    SyncPrometheusMiddleware,
                ],
            },
        },
        {
            "settings": {
                "blacksmith.client.service_discovery": "router",
                "blacksmith.client.router_sd_config": "",
                "blacksmith.client.read_timeout": "5",
                "blacksmith.client.connect_timeout": "2",
                "blacksmith.client.proxies": ["http://  http//p/"],
                "blacksmith.client.verify_certificate": False,
                "blacksmith.client.collection_parser": DummyCollectionParser,
                "blacksmith.scan": "tests.unittests.resources",
            },
            "expected": {
                "sd": SyncRouterDiscovery,
                "timeout": HTTPTimeout(5, 2),
                "proxies": {"http://": "http//p/"},
                "verify": False,
                "transport": SyncHttpxTransport,
                "collection_parser": DummyCollectionParser,
                "middlewares": [],
                "middleware_factories": [],
            },
        },
        {
            "settings": {
                "blacksmith.client.service_discovery": "router",
                "blacksmith.client.router_sd_config": "",
                "blacksmith.client.transport": DummyTransport(),
                "blacksmith.scan": "tests.unittests.resources",
            },
            "expected": {
                "sd": SyncRouterDiscovery,
                "timeout": HTTPTimeout(30, 15),
                "proxies": None,
                "verify": True,
                "transport": DummyTransport,
                "collection_parser": CollectionParser,
                "middlewares": [],
                "middleware_factories": [],
            },
        },
    ],
)
def test_req_attr(
    params: Dict[str, Any], dummy_request: Any, registry: CollectorRegistry
):
    assert isinstance(dummy_request.blacksmith, PyramidBlacksmith)
    assert isinstance(dummy_request.blacksmith.clients["client"], SyncClientFactory)
    assert isinstance(
        dummy_request.blacksmith.clients["client"].sd, params["expected"]["sd"]
    )
    assert (
        dummy_request.blacksmith.clients["client"].timeout
        == params["expected"]["timeout"]
    )
    assert (
        dummy_request.blacksmith.clients["client"].transport.proxies
        == params["expected"]["proxies"]
    )
    assert (
        dummy_request.blacksmith.clients["client"].transport.verify_certificate
        == params["expected"]["verify"]
    )
    assert isinstance(
        dummy_request.blacksmith.clients["client"].transport,
        params["expected"]["transport"],
    )
    assert (
        dummy_request.blacksmith.clients["client"].collection_parser
        is params["expected"]["collection_parser"]
    )
    assert [
        type(m) for m in dummy_request.blacksmith.clients["client"].middlewares
    ] == params["expected"]["middlewares"]

    assert [
        type(m) for m in dummy_request.blacksmith.client("api").middlewares
    ] == params["expected"]["middleware_factories"]

    # Ensure there is not two middleware here
    assert [
        type(m) for m in dummy_request.blacksmith.client("api").middlewares
    ] == params["expected"]["middleware_factories"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.clients": """
                    client1
                    client2
                """,
                "blacksmith.client1.service_discovery": "consul",
                "blacksmith.client1.consul_sd_config": "",
                "blacksmith.client2.service_discovery": "static",
                "blacksmith.client2.static_sd_config": [],
                "blacksmith.scan": "tests.unittests.resources",
            },
            "expected": {
                "client1": SyncConsulDiscovery,
                "client2": SyncStaticDiscovery,
            },
        }
    ],
)
def test_multi_client(
    params: Dict[str, Any], dummy_request: Any, registry: CollectorRegistry
):
    assert isinstance(
        dummy_request.blacksmith.clients["client1"].sd, params["expected"]["client1"]
    )
    assert isinstance(
        dummy_request.blacksmith.clients["client2"].sd, params["expected"]["client2"]
    )
    with pytest.raises(AttributeError) as ctx:
        dummy_request.blacksmith.client3("api")
    assert str(ctx.value) == "Client 'client3' is not registered"


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.service_discovery": "static",
                "blacksmith.client.static_sd_config": [],
            },
            "expected": SyncStaticDiscovery,
        },
        {
            "settings": {
                "blacksmith.client.service_discovery": "consul",
                "blacksmith.client.consul_sd_config": [],
            },
            "expected": SyncConsulDiscovery,
        },
        {
            "settings": {
                "blacksmith.client.service_discovery": "router",
                "blacksmith.client.router_sd_config": [],
            },
            "expected": SyncRouterDiscovery,
        },
        {
            "settings": {
                "blacksmith.client.service_discovery": "nomad",
                "blacksmith.client.nomad_sd_config": [],
            },
            "expected": SyncNomadDiscovery,
        },
    ],
)
def test_get_sd_strategy(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)
    assert isinstance(builder.build_sd_strategy(), params["expected"])


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {},
            "expected": "Missing setting blacksmith.client.service_discovery",
        },
        {
            "settings": {"blacksmith.client.service_discovery": "Static"},
            "expected": (
                "Invalid value Static for blacksmith.client.service_discovery: "
                "not in static, consul, nomad, router"
            ),
        },
    ],
)
def test_get_sd_strategy_error(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)
    with pytest.raises(ConfigurationError) as ctx:
        builder.build_sd_strategy()
    assert str(ctx.value) == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.static_sd_config": """
                    api/v1 http://api.v1
                    smtp   smtp://host/
                """
            },
            "expected": {
                ("api", "v1"): "http://api.v1",
                ("smtp", None): "smtp://host/",
            },
        },
    ],
)
def test_build_sd_static(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    sd = builder.build_sd_static()
    assert isinstance(sd, SyncStaticDiscovery)
    assert sd.endpoints == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.service_discovery": "static",
                "blacksmith.client.static_sd_config": [
                    "api/v1 http://api.v1",
                    "smtp://host/",
                ],
            },
            "expected": (
                "Invalid value smtp://host/ in blacksmith.client.static_sd_config[1]"
            ),
        },
    ],
)
def test_build_sd_static_error(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)
    with pytest.raises(ConfigurationError) as ctx:
        builder.build_sd_strategy()
    assert str(ctx.value) == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.consul_sd_config": """
                    addr                           https://csl.v1/
                    service_name_fmt               {service}${version}
                    service_url_fmt                http://{address}:{port}/api/{version}
                    unversioned_service_name_fmt   {service}
                    unversioned_service_url_fmt    http://{address}:{port}/api
                    consul_token                   abc
                """
            },
            "expected": {
                "consul_endpoint": "https://csl.v1/",
                "service_name_fmt": "{service}${version}",
                "service_url_fmt": "http://{address}:{port}/api/{version}",
                "unversioned_service_name_fmt": "{service}",
                "unversioned_service_url_fmt": "http://{address}:{port}/api",
                "consul_token": "abc",
            },
        },
        {
            "settings": {
                "blacksmith.client.consul_sd_config": """
                """
            },
            "expected": {
                "consul_endpoint": "http://consul.v1/",
                "service_name_fmt": "{service}-{version}",
                "service_url_fmt": "http://{address}:{port}/{version}",
                "unversioned_service_name_fmt": "{service}",
                "unversioned_service_url_fmt": "http://{address}:{port}",
            },
        },
    ],
)
def test_build_sd_consul(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    sd = builder.build_sd_consul()
    assert isinstance(sd, SyncConsulDiscovery)
    if "consul_token" in params["expected"]:
        assert len(sd.blacksmith_cli.middlewares) == 1  # type: ignore
        assert isinstance(
            sd.blacksmith_cli.middlewares[0],
            SyncHTTPBearerMiddleware,
        )
        assert sd.blacksmith_cli.middlewares[0].headers == {
            "Authorization": "Bearer abc"
        }
    else:
        assert len(sd.blacksmith_cli.middlewares) == 0  # type: ignore

    assert sd.service_name_fmt == params["expected"]["service_name_fmt"]
    assert sd.service_url_fmt == params["expected"]["service_url_fmt"]
    assert (
        sd.unversioned_service_name_fmt
        == params["expected"]["unversioned_service_name_fmt"]
    )
    assert (
        sd.unversioned_service_url_fmt
        == params["expected"]["unversioned_service_url_fmt"]
    )


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.router_sd_config": """
                    service_url_fmt             https://r/{service}-{version}
                    unversioned_service_url_fmt https://r/{service}
                """
            },
            "expected": {
                "service_url_fmt": "https://r/{service}-{version}",
                "unversioned_service_url_fmt": "https://r/{service}",
            },
        },
        {
            "settings": {
                "blacksmith.client.router_sd_config": """
                """
            },
            "expected": {
                "service_url_fmt": "http://router/{service}-{version}/{version}",
                "unversioned_service_url_fmt": "http://router/{service}",
            },
        },
    ],
)
def test_build_sd_router(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    sd = builder.build_sd_router()
    assert isinstance(sd, SyncRouterDiscovery)
    assert sd.service_url_fmt == params["expected"]["service_url_fmt"]
    assert (
        sd.unversioned_service_url_fmt
        == params["expected"]["unversioned_service_url_fmt"]
    )


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.proxies": """
                    http://   http://proxy:8080/
                    https://  https://proxy:8443/
                """
            },
            "expected": {
                "http://": "http://proxy:8080/",
                "https://": "https://proxy:8443/",
            },
        },
        {
            "settings": {
                "blacksmith.client.proxies": """
                """
            },
            "expected": None,
        },
        {"settings": {}, "expected": None},
    ],
)
def test_get_proxies(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    proxies = builder.get_proxies()
    assert proxies == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {"settings": {}, "expected": True},
        {
            "settings": {"blacksmith.client.verify_certificate": "true"},
            "expected": True,
        },
        {"settings": {"blacksmith.client.verify_certificate": "1"}, "expected": True},
        {"settings": {"blacksmith.client.verify_certificate": True}, "expected": True},
        {"settings": {"blacksmith.client.verify_certificate": "0"}, "expected": False},
        {
            "settings": {"blacksmith.client.verify_certificate": "whatever"},
            "expected": False,
        },
    ],
)
def test_get_verify_certificate(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    verify = builder.get_verify_certificate()
    assert verify is params["expected"]


NoneType = type(None)


@pytest.mark.parametrize(
    "params",
    [
        {"settings": {}, "expected": NoneType},
        {"settings": {"blacksmith.client.transport": ""}, "expected": NoneType},
        {
            "settings": {"blacksmith.client.transport": DummyTransport()},
            "expected": DummyTransport,
        },
        {
            "settings": {
                "blacksmith.client.transport": "tests.unittests.fixtures:DummyTransport"
            },
            "expected": DummyTransport,
        },
    ],
)
def test_build_transport(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    transport = builder.build_transport()
    assert isinstance(transport, params["expected"])


@pytest.mark.parametrize(
    "params",
    [
        {"settings": {}, "expected": CollectionParser},
        {
            "settings": {"blacksmith.client.collection_parser": ""},
            "expected": CollectionParser,
        },
        {
            "settings": {"blacksmith.client.collection_parser": DummyCollectionParser},
            "expected": DummyCollectionParser,
        },
        {
            "settings": {
                "blacksmith.client.collection_parser": (
                    "tests.unittests.fixtures:DummyCollectionParser"
                )
            },
            "expected": DummyCollectionParser,
        },
    ],
)
def test_build_collection_parser(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    parser = builder.build_collection_parser()
    assert parser == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {"settings": {}, "expected": default_error_parser},
        {
            "settings": {"blacksmith.client.error_parser": ""},
            "expected": default_error_parser,
        },
        {
            "settings": {"blacksmith.client.error_parser": default_error_parser},
            "expected": default_error_parser,
        },
        {
            "settings": {"blacksmith.client.error_parser": DummyErrorParser},
            "expected": DummyErrorParser(),
        },
        {
            "settings": {"blacksmith.client.error_parser": DummyErrorParser()},
            "expected": DummyErrorParser(),
        },
        {
            "settings": {
                "blacksmith.client.error_parser": (
                    "tests.unittests.fixtures:DummyErrorParser"
                )
            },
            "expected": DummyErrorParser(),
        },
    ],
)
def test_build_error_parser(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    parser = builder.build_error_parser()
    assert parser == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {},
            "expected_request_latency_seconds": [
                0.05,
                0.1,
                0.2,
                0.4,
                0.8,
                1.6,
                3.2,
                6.4,
                12.8,
                25.6,
            ],
            "expected_blacksmith_cache_latency_seconds": [
                0.005,
                0.01,
                0.02,
                0.04,
                0.08,
                0.16,
                0.32,
                0.64,
                1.28,
                2.56,
            ],
        },
        {
            "settings": {
                "blacksmith.prometheus_buckets": """
                    buckets              0.1  0.2
                    hit_cache_buckets   0.01 0.02
                """
            },
            "expected_request_latency_seconds": [
                0.1,
                0.2,
            ],
            "expected_blacksmith_cache_latency_seconds": [
                0.01,
                0.02,
            ],
        },
    ],
)
def test_metrics_builder(params: Dict[str, Any], registry: CollectorRegistry):
    builder = BlacksmithPrometheusMetricsBuilder(params["settings"])
    metric = builder.build()
    assert (
        metric.blacksmith_request_latency_seconds._kwargs["buckets"]
        == params["expected_request_latency_seconds"]
    )

    assert (
        metric.blacksmith_cache_latency_seconds._kwargs["buckets"]
        == params["expected_blacksmith_cache_latency_seconds"]
    )
    builder.__class__._instance = None  # type: ignore


@pytest.mark.parametrize(
    "params",
    [  # type: ignore
        {
            "settings": {},
            "expected": [],
        },
        {
            "settings": {
                "blacksmith.client.middlewares": """
                    prometheus
                """
            },
            "expected": [SyncPrometheusMiddleware],
        },
        {
            "settings": {
                "blacksmith.client.middlewares": """
                    static_headers
                """
            },
            "expected": [SyncHTTPAddHeadersMiddleware],
        },
        {
            "settings": {
                "blacksmith.client.middlewares": """
                    zipkin
                """
            },
            "expected": [SyncZipkinMiddleware],
        },
        {
            "settings": {
                "blacksmith.client.middlewares": """
                    dummy       tests.unittests.fixtures:DummyMiddlewareBuilder
                """
            },
            "expected": [DummyMiddleware],
        },
    ],
)
def test_build_middlewares(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    middlewares = builder.build_middlewares(metrics)
    assert [type(mw) for mw in middlewares] == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.middlewares": """
                    dummy       tests.unittests.fixtures:DummyMiddlewareBuilder
                """,
                "blacksmith.client.middleware.dummy.tracker": "tracked",
            },
            "expected": "tracked",
        },
    ],
)
def test_build_middlewares_params(params: Dict[str, Any], metrics: PrometheusMetrics):
    builder = BlacksmithClientSettingsBuilder(params["settings"], metrics)

    middlewares = builder.build_middlewares(metrics)
    middleware = next(middlewares)
    assert middleware.tracker == params["expected"]  # type: ignore


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.middleware_factories": ["forward_header"],
                "blacksmith.client.middleware_factory.forward_header": """
                        Authorization
                """,
            },
            "expected": [ForwardHeaderFactoryBuilder],
        },
    ],
)
def test_build_middleware_factory_builder(
    params: Dict[str, Any], metrics: PrometheusMetrics
):
    builder = BlacksmithMiddlewareFactoryBuilder(params["settings"], metrics)
    factories = [type(f) for f in builder.build()]
    assert factories == params["expected"]
