import sys
from pathlib import Path
from blacksmith.domain.model.params import CollectionParser
from blacksmith.domain.registry import registry

import pytest
from blacksmith.domain.model.http import HTTPTimeout
from blacksmith.middleware._sync.auth import SyncHTTPBearerAuthorization
from blacksmith.sd._sync.adapters.consul import SyncConsulDiscovery
from blacksmith.sd._sync.adapters.router import SyncRouterDiscovery
from blacksmith.sd._sync.adapters.static import SyncStaticDiscovery
from blacksmith.service._sync.adapters.httpx import SyncHttpxTransport
from blacksmith.service._sync.client import SyncClientFactory
from pydantic.typing import NoneType
from pyramid.exceptions import ConfigurationError
from pyramid.interfaces import IRequestExtensions

from pyramid_blacksmith.binding import (
    BlacksmithClientSettingsBuilder,
    PyramidBlacksmith,
    list_to_dict,
)

here = Path(__file__).parent.parent.parent
sys.path.insert(0, str(here))
from tests.unittests.fixtures import DummyCollectionParser, DummyTransport  # noqa


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
def test_includeme(config):
    ext = config.registry.queryUtility(IRequestExtensions)
    assert "blacksmith" in ext.descriptors

    # check that the scan is loading resources
    assert registry.clients == {
        "api": {"dummy": registry.clients["api"]["dummy"]},
    }
    assert registry.clients["api"]["dummy"].collection is None
    assert registry.clients["api"]["dummy"].resource.path == "/dummies/{name}"


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "key": [
                    "api/v1 http://api.v1",
                    "smtp smtp://host/",
                ]
            },
            "expected": {
                "api/v1": "http://api.v1",
                "smtp": "smtp://host/",
            },
        },
        {
            "settings": {
                "key": """
                    api/v1 http://api.v1
                    smtp   smtp://host/
                """
            },
            "expected": {
                "api/v1": "http://api.v1",
                "smtp": "smtp://host/",
            },
        },
    ],
)
def test_list_to_dict(params):
    dict_ = list_to_dict(params["settings"], "key")
    assert dict_ == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.client.service_discovery": "consul",
                "blacksmith.client.consul_sd_config": "",
            },
            "expected": {
                "sd": SyncConsulDiscovery,
                "timeout": HTTPTimeout(30, 15),
                "proxies": None,
                "verify": True,
                "transport": SyncHttpxTransport,
                "collection_parser": CollectionParser,
            },
        },
        {
            "settings": {
                "blacksmith.client.service_discovery": "consul",
                "blacksmith.client.consul_sd_config": "",
                "blacksmith.client.timeout": "5",
                "blacksmith.client.connect_timeout": "2",
                "blacksmith.client.proxies": ["http://  http//p/"],
                "blacksmith.client.verify_certificate": False,
                "blacksmith.client.collection_parser": DummyCollectionParser,
            },
            "expected": {
                "sd": SyncConsulDiscovery,
                "timeout": HTTPTimeout(5, 2),
                "proxies": {"http://": "http//p/"},
                "verify": False,
                "transport": SyncHttpxTransport,
                "collection_parser": DummyCollectionParser,
            },
        },
        {
            "settings": {
                "blacksmith.client.service_discovery": "consul",
                "blacksmith.client.consul_sd_config": "",
                "blacksmith.client.transport": DummyTransport(),
            },
            "expected": {
                "sd": SyncConsulDiscovery,
                "timeout": HTTPTimeout(30, 15),
                "proxies": None,
                "verify": True,
                "transport": DummyTransport,
                "collection_parser": CollectionParser,
            },
        },
    ],
)
def test_req_attr(params, dummy_request):
    assert isinstance(dummy_request.blacksmith, PyramidBlacksmith)
    assert isinstance(dummy_request.blacksmith.client, SyncClientFactory)
    assert isinstance(dummy_request.blacksmith.client.sd, params["expected"]["sd"])
    assert dummy_request.blacksmith.client.timeout == params["expected"]["timeout"]
    assert (
        dummy_request.blacksmith.client.transport.proxies
        == params["expected"]["proxies"]
    )
    assert (
        dummy_request.blacksmith.client.transport.verify_certificate
        == params["expected"]["verify"]
    )
    assert isinstance(
        dummy_request.blacksmith.client.transport, params["expected"]["transport"]
    )
    assert (
        dummy_request.blacksmith.client.collection_parser
        is params["expected"]["collection_parser"]
    )


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
            },
            "expected": {
                "client1": SyncConsulDiscovery,
                "client2": SyncStaticDiscovery,
            },
        }
    ],
)
def test_multi_client(params, dummy_request):
    assert isinstance(
        dummy_request.blacksmith.client1.sd, params["expected"]["client1"]
    )
    assert isinstance(
        dummy_request.blacksmith.client2.sd, params["expected"]["client2"]
    )


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
    ],
)
def test_get_sd_strategy(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])
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
                "not in static, consul, router"
            ),
        },
    ],
)
def test_get_sd_strategy_error(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])
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
def test_build_sd_static(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])

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
def test_build_sd_static_error(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])
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
def test_build_sd_consul(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])

    sd = builder.build_sd_consul()
    assert isinstance(sd, SyncConsulDiscovery)
    if "consul_token" in params["expected"]:
        assert len(sd.blacksmith_cli.middlewares) == 1
        assert isinstance(
            sd.blacksmith_cli.middlewares[0],
            SyncHTTPBearerAuthorization,
        )
        assert sd.blacksmith_cli.middlewares[0].headers == {
            "Authorization": "Bearer abc"
        }
    else:
        assert len(sd.blacksmith_cli.middlewares) == 0

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
def test_build_sd_router(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])

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
def test_get_proxies(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])

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
def test_get_verify_certificate(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])

    verify = builder.get_verify_certificate()
    assert verify is params["expected"]


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
def test_build_transport(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])

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
def test_build_collection_parser(params):
    builder = BlacksmithClientSettingsBuilder(params["settings"])

    parser = builder.build_collection_parser()
    assert parser == params["expected"]
