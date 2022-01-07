from typing import Callable, Dict, Optional, Protocol, cast

import pkg_resources
from blacksmith import (
    SyncClientFactory,
    SyncConsulDiscovery,
    SyncRouterDiscovery,
    SyncStaticDiscovery,
)
from blacksmith.domain.model.http import HTTPTimeout
from blacksmith.sd._sync.adapters.static import Endpoints
from blacksmith.sd._sync.base import SyncAbstractServiceDiscovery
from blacksmith.service._sync.base import SyncAbstractTransport
from blacksmith.typing import Proxies
from pyramid.config import Configurator
from pyramid.exceptions import ConfigurationError
from pyramid.request import Request
from pyramid.settings import asbool, aslist

SD_KEY = "blacksmith.service_discovery"

Settings = Dict[str, str]


class SDBuilder(Protocol):
    def __call__(self, settings: Settings) -> SyncAbstractServiceDiscovery:
        ...


def list_to_dict(settings: Settings, setting: str) -> Settings:
    list_ = aslist(settings[setting], flatten=False)
    dict_ = {}
    for idx, param in enumerate(list_):
        try:
            key, val = param.split(maxsplit=1)
            dict_[key] = val
        except ValueError:
            raise ConfigurationError(f"Invalid value {param} in {setting}[{idx}]")
    return dict_


def build_sd_static(settings: Settings) -> SyncStaticDiscovery:
    key = "blacksmith.static_sd_config"
    services_endpoints = list_to_dict(settings, key)
    services: Endpoints = {}
    for api, url in services_endpoints.items():
        api, version = api.split("/", 1) if "/" in api else (api, None)
        services[(api, version)] = url
    return SyncStaticDiscovery(services)


def build_sd_consul(settings: Settings) -> SyncConsulDiscovery:
    key = "blacksmith.consul_sd_config"
    kwargs = list_to_dict(settings, key)
    return SyncConsulDiscovery(**kwargs)


def build_sd_router(settings: Settings) -> SyncRouterDiscovery:
    key = "blacksmith.router_sd_config"
    kwargs = list_to_dict(settings, key)
    return SyncRouterDiscovery(**kwargs)


def get_sd_strategy(settings: Settings) -> SDBuilder:
    sd_classes: Dict[str, SDBuilder] = {
        "static": build_sd_static,
        "consul": build_sd_consul,
        "router": build_sd_router,
    }
    sd_name = settings.get(SD_KEY)
    if not sd_name:
        raise ConfigurationError(f"Missing setting {SD_KEY}")

    if sd_name not in sd_classes:
        raise ConfigurationError(
            f"Invalid value {sd_name} for {SD_KEY}: "
            f"not in {', '.join(sd_classes.keys())}"
        )

    return sd_classes[sd_name]


def get_timeout(settings: Settings) -> HTTPTimeout:
    kwargs = {}
    for key in (
        ("blacksmith.timeout", "timeout"),
        ("blacksmith.connect_timeout", "connect"),
    ):
        if key[0] in settings:
            kwargs[key[1]] = int(settings[key[0]])
    return HTTPTimeout(**kwargs)


def get_proxies(settings) -> Optional[Proxies]:
    key = "blacksmith.proxies"
    if key in settings:
        return cast(Proxies, list_to_dict(settings, key)) or None


def get_verify_certificate(settings: Settings) -> bool:
    return asbool(settings.get("blacksmith.verify_certificate", True))


def build_transport(settings: Settings) -> Optional[SyncAbstractTransport]:
    value = settings.get("blacksmith.transport")
    if not value:
        return None
    if isinstance(value, SyncAbstractTransport):
        return value
    ep = pkg_resources.EntryPoint.parse(f"x={value}")
    cls = ep.resolve()
    return cls()


def blacksmith_binding_factory(
    config: Configurator,
) -> Callable[[Request], SyncClientFactory]:

    settings = config.registry.settings
    sd = get_sd_strategy(settings)(settings)
    timeout = get_timeout(settings)
    proxies = get_proxies(settings)
    verify = get_verify_certificate(settings)
    transport = build_transport(settings)
    client = SyncClientFactory(
        sd,
        timeout=timeout,
        proxies=proxies,
        verify_certificate=verify,
        transport=transport,
    )

    def blacksmith_binding(request: Request) -> SyncClientFactory:
        return client

    return blacksmith_binding


def includeme(config: Configurator):
    config.add_request_method(
        callable=blacksmith_binding_factory(config),
        name="blacksmith",
        property=True,
        reify=False,
    )
