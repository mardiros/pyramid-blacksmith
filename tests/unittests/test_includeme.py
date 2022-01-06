import pytest
from blacksmith.sd._sync.adapters.static import SyncStaticDiscovery
from blacksmith.service._sync.client import SyncClientFactory
from pyramid.exceptions import ConfigurationError
from pyramid.interfaces import IRequestExtensions

from pyramid_blacksmith.binding import (
    build_sd_consul,
    build_sd_router,
    build_sd_static,
    get_sd_strategy,
)


def test_includeme(config):
    ext = config.registry.queryUtility(IRequestExtensions)
    assert "blacksmith" in ext.descriptors


def test_req_attr(dummy_request):
    assert isinstance(dummy_request.blacksmith, SyncClientFactory)


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
                "blacksmith.static_sd_config": [
                    "api/v1 http://api.v1",
                    "smtp smtp://host/",
                ]
            },
            "expected": {
                ("api", "v1"): "http://api.v1",
                ("smtp", None): "smtp://host/",
            },
        },
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
    sd: SyncStaticDiscovery = build_sd_static(params["settings"])
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
