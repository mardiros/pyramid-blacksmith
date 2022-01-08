from typing import Callable, Dict, Optional, Type, cast
from blacksmith.domain.model.params import CollectionParser

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


Settings = Dict[str, str]


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


class BlacksmithClientSettingsBuilder:
    def __init__(self, settings: Settings, prefix: str = "client"):
        self.settings = settings
        self.prefix = f"blacksmith.{prefix}"

    def build(self) -> SyncClientFactory:
        sd = self.build_sd_strategy()
        timeout = self.get_timeout()
        proxies = self.get_proxies()
        verify = self.get_verify_certificate()
        transport = self.build_transport()
        collection_parser = self.build_collection_parser()
        return SyncClientFactory(
            sd,
            timeout=timeout,
            proxies=proxies,
            verify_certificate=verify,
            transport=transport,
            collection_parser=collection_parser,
        )

    def build_sd_static(self) -> SyncStaticDiscovery:
        key = f"{self.prefix}.static_sd_config"
        services_endpoints = list_to_dict(self.settings, key)
        services: Endpoints = {}
        for api, url in services_endpoints.items():
            api, version = api.split("/", 1) if "/" in api else (api, None)
            services[(api, version)] = url
        return SyncStaticDiscovery(services)

    def build_sd_consul(self) -> SyncConsulDiscovery:
        key = f"{self.prefix}.consul_sd_config"
        kwargs = list_to_dict(self.settings, key)
        return SyncConsulDiscovery(**kwargs)

    def build_sd_router(self) -> SyncRouterDiscovery:
        key = f"{self.prefix}.router_sd_config"
        kwargs = list_to_dict(self.settings, key)
        return SyncRouterDiscovery(**kwargs)

    def build_sd_strategy(self) -> SyncAbstractServiceDiscovery:
        sd_classes: Dict[str, Callable[[], SyncAbstractServiceDiscovery]] = {
            "static": self.build_sd_static,
            "consul": self.build_sd_consul,
            "router": self.build_sd_router,
        }
        key = f"{self.prefix}.service_discovery"
        sd_name = self.settings.get(key)
        if not sd_name:
            raise ConfigurationError(f"Missing setting {key}")

        if sd_name not in sd_classes:
            raise ConfigurationError(
                f"Invalid value {sd_name} for {key}: "
                f"not in {', '.join(sd_classes.keys())}"
            )

        return sd_classes[sd_name]()

    def get_timeout(self) -> HTTPTimeout:
        kwargs = {}
        for key in (
            (f"{self.prefix}.timeout", "timeout"),
            (f"{self.prefix}.connect_timeout", "connect"),
        ):
            if key[0] in self.settings:
                kwargs[key[1]] = int(self.settings[key[0]])
        return HTTPTimeout(**kwargs)

    def get_proxies(self) -> Optional[Proxies]:
        key = f"{self.prefix}.proxies"
        if key in self.settings:
            return cast(Proxies, list_to_dict(self.settings, key)) or None

    def get_verify_certificate(self) -> bool:
        return asbool(self.settings.get(f"{self.prefix}.verify_certificate", True))

    def build_transport(self) -> Optional[SyncAbstractTransport]:
        value = self.settings.get(f"{self.prefix}.transport")
        if not value:
            return None
        if isinstance(value, SyncAbstractTransport):
            return value
        ep = pkg_resources.EntryPoint.parse(f"x={value}")
        cls = ep.resolve()
        return cls()

    def build_collection_parser(self) -> Type[CollectionParser]:
        value = self.settings.get(f"{self.prefix}.collection_parser")
        if not value:
            return CollectionParser
        if isinstance(value, type) and issubclass(value, CollectionParser):
            return value
        ep = pkg_resources.EntryPoint.parse(f"x={value}")
        cls = ep.resolve()
        return cls


class PyramidBlacksmith:
    """
    Type of the `request.blacksmith` property.
    
    This can be used to create a ``Protocol`` of the pyramid ``Request``
    in final application for typing purpose.

    Example:

    .. code-block::

        from pyramid_blacksmith import PyramidBlacksmith

        class RequestProtocol(Protocol):
            blacksmith: PyramidBlacksmith


        def my_view(request: RequestProtocol):
            ...

    """
    def __init__(self, clients: Dict[str, SyncClientFactory]):
        self.clients = clients

    def __getattr__(self, name: str) -> SyncClientFactory:
        """
        Return the blacksmith client factory named in the configuration.
        """
        try:
            return self.clients[name]
        except KeyError as k:
            raise AttributeError(f"Client {k} is not registered")


def blacksmith_binding_factory(
    config: Configurator,
) -> Callable[[Request], PyramidBlacksmith]:

    settings = config.registry.settings
    clients_key = aslist(settings.get("blacksmith.clients", ["client"]))
    clients_dict = {
        key: BlacksmithClientSettingsBuilder(settings, key).build()
        for key in clients_key
    }
    clients = PyramidBlacksmith(clients_dict)

    def blacksmith_binding(request: Request) -> PyramidBlacksmith:
        return clients

    return blacksmith_binding


def includeme(config: Configurator):
    """
    Expose the method consume by the Configurator while using:

    ::

        config.include('pyramid_blacksmith')


    This will inject the request property ``request.blacksmith`` like 
    the pyramid view below:

    ::

        def my_view(request):

            api = request.blacksmith.client("api")
            ...

    """
    config.add_request_method(
        callable=blacksmith_binding_factory(config),
        name="blacksmith",
        property=True,
        reify=False,
    )
