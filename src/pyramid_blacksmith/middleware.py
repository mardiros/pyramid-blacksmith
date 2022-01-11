import abc

from blacksmith import SyncPrometheusMetrics
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from pyramid.settings import aslist

from .utils import list_to_dict, resolve_entrypoint


class AbstractMiddlewareBuilder(abc.ABC):
    def __init__(self, settings, prefix):
        self.settings = settings
        self.prefix = prefix

    @abc.abstractmethod
    def build(self, *args) -> SyncHTTPMiddleware:
        """Build the Middleware"""


class PrometheusMetricsBuilder(AbstractMiddlewareBuilder):
    def build(self) -> SyncPrometheusMetrics:
        buckets = None
        settings = list_to_dict(self.settings, self.prefix)
        buckets_val = settings.get("buckets")
        if buckets_val:
            buckets = [float(val) for val in aslist(buckets_val)]

        registry_instance = settings.get("registry", "prometheus_client:REGISTRY")
        registry = resolve_entrypoint(registry_instance)
        return SyncPrometheusMetrics(buckets, registry=registry)
