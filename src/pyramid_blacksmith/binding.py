from typing import Callable, Dict, Protocol
from blacksmith import (
    SyncClientFactory,
    SyncConsulDiscovery,
    SyncStaticDiscovery,
    SyncRouterDiscovery,
)
from blacksmith.sd._sync.base import SyncAbstractServiceDiscovery

from pyramid.config import Configurator
from pyramid.request import Request
from pyramid.exceptions import ConfigurationError


SD_KEY = "blacksmith.service_discovery"


class SDBuilder(Protocol):
    def __call__(self, settings: Dict[str, str]) -> SyncAbstractServiceDiscovery:
        ...


def build_sd_static(settings: Dict[str, str]) -> SyncStaticDiscovery:
    pass


def build_sd_consul(settings: Dict[str, str]) -> SyncConsulDiscovery:
    pass


def build_sd_router(settings: Dict[str, str]) -> SyncRouterDiscovery:
    pass


def get_sd_strategy(settings: Dict[str, str]) -> SDBuilder:
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


def blacksmith_binding_factory(
    config: Configurator,
) -> Callable[[Request], SyncClientFactory]:

    settings = config.registry.settings

    def blacksmith_binding(request: Request) -> SyncClientFactory:
        sd = SyncConsulDiscovery()
        return SyncClientFactory(sd)

    return blacksmith_binding


def includeme(config: Configurator):
    config.add_request_method(
        callable=blacksmith_binding_factory(config),
        name="blacksmith",
        property=True,
        reify=False,
    )
