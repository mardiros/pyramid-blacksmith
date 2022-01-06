from blacksmith import SyncClientFactory, SyncConsulDiscovery

from pyramid.config import Configurator


def blacksmith_binding_factory(config):
    def blacksmith_binding(request):
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
