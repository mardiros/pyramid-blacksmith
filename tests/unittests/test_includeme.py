import sys
from pathlib import Path
from blacksmith.domain.model.params import CollectionParser

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
    build_collection_parser,
    build_sd_consul,
    build_sd_router,
    build_sd_static,
    build_transport,
    get_proxies,
    get_sd_strategy,
    get_verify_certificate,
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
                "blacksmith.service_discovery": "consul",
                "blacksmith.consul_sd_config": "",
            },
        }
    ],
)
def test_includeme(config):
    ext = config.registry.queryUtility(IRequestExtensions)
    assert "blacksmith" in ext.descriptors


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.service_discovery": "consul",
                "blacksmith.consul_sd_config": "",
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
                "blacksmith.service_discovery": "consul",
                "blacksmith.consul_sd_config": "",
                "blacksmith.timeout": "5",
                "blacksmith.connect_timeout": "2",
                "blacksmith.proxies": ["http://  http//p/"],
                "blacksmith.verify_certificate": False,
                "blacksmith.collection_parser": DummyCollectionParser,
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
                "blacksmith.service_discovery": "consul",
                "blacksmith.consul_sd_config": "",
                "blacksmith.transport": DummyTransport(),
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
    assert isinstance(dummy_request.blacksmith, SyncClientFactory)
    assert isinstance(dummy_request.blacksmith.sd, params["expected"]["sd"])
    assert dummy_request.blacksmith.timeout == params["expected"]["timeout"]
    assert dummy_request.blacksmith.transport.proxies == params["expected"]["proxies"]
    assert (
        dummy_request.blacksmith.transport.verify_certificate
        == params["expected"]["verify"]
    )
    assert isinstance(
        dummy_request.blacksmith.transport, params["expected"]["transport"]
    )
    assert (
        dummy_request.blacksmith.collection_parser
        is params["expected"]["collection_parser"]
    )


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {"blacksmith.service_discovery": "static"},
            "expected": build_sd_static,
        },
        {
            "settings": {"blacksmith.service_discovery": "consul"},
            "expected": build_sd_consul,
        },
        {
            "settings": {"blacksmith.service_discovery": "router"},
            "expected": build_sd_router,
        },
    ],
)
def test_get_sd_strategy(params):
    assert get_sd_strategy(params["settings"]) == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {},
            "expected": "Missing setting blacksmith.service_discovery",
        },
        {
            "settings": {"blacksmith.service_discovery": "Static"},
            "expected": (
                "Invalid value Static for blacksmith.service_discovery: "
                "not in static, consul, router"
            ),
        },
    ],
)
def test_get_sd_strategy_error(params):
    with pytest.raises(ConfigurationError) as ctx:
        get_sd_strategy(params["settings"])
    assert str(ctx.value) == params["expected"]


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
                "blacksmith.static_sd_config": """
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
    sd = build_sd_static(params["settings"])
    assert isinstance(sd, SyncStaticDiscovery)
    assert sd.endpoints == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.static_sd_config": [
                    "api/v1 http://api.v1",
                    "smtp://host/",
                ]
            },
            "expected": "Invalid value smtp://host/ in blacksmith.static_sd_config[1]",
        },
    ],
)
def test_build_sd_static_error(params):
    with pytest.raises(ConfigurationError) as ctx:
        build_sd_static(params["settings"])
    assert str(ctx.value) == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "blacksmith.consul_sd_config": """
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
                "blacksmith.consul_sd_config": """
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
    sd = build_sd_consul(params["settings"])
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
                "blacksmith.router_sd_config": """
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
                "blacksmith.router_sd_config": """
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
    sd = build_sd_router(params["settings"])
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
                "blacksmith.proxies": """
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
                "blacksmith.proxies": """
                """
            },
            "expected": None,
        },
        {"settings": {}, "expected": None},
    ],
)
def test_get_proxies(params):
    proxies = get_proxies(params["settings"])
    assert proxies == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {"settings": {}, "expected": True},
        {"settings": {"blacksmith.verify_certificate": "true"}, "expected": True},
        {"settings": {"blacksmith.verify_certificate": "1"}, "expected": True},
        {"settings": {"blacksmith.verify_certificate": True}, "expected": True},
        {"settings": {"blacksmith.verify_certificate": "0"}, "expected": False},
        {"settings": {"blacksmith.verify_certificate": "whatever"}, "expected": False},
    ],
)
def test_get_verify_certificate(params):
    verify = get_verify_certificate(params["settings"])
    assert verify is params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {"settings": {}, "expected": NoneType},
        {"settings": {"blacksmith.transport": ""}, "expected": NoneType},
        {
            "settings": {"blacksmith.transport": DummyTransport()},
            "expected": DummyTransport,
        },
        {
            "settings": {
                "blacksmith.transport": "tests.unittests.fixtures:DummyTransport"
            },
            "expected": DummyTransport,
        },
    ],
)
def test_build_transport(params):
    transport = build_transport(params["settings"])
    assert isinstance(transport, params["expected"])


@pytest.mark.parametrize(
    "params",
    [
        {"settings": {}, "expected": CollectionParser},
        {
            "settings": {"blacksmith.collection_parser": ""},
            "expected": CollectionParser,
        },
        {
            "settings": {"blacksmith.collection_parser": DummyCollectionParser},
            "expected": DummyCollectionParser,
        },
        {
            "settings": {
                "blacksmith.collection_parser": "tests.unittests.fixtures:DummyCollectionParser"
            },
            "expected": DummyCollectionParser,
        },
    ],
)
def test_build_collection_parser(params):
    parser = build_collection_parser(params["settings"])
    assert parser == params["expected"]
