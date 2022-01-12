import abc

from blacksmith import SyncCircuitBreaker, SyncPrometheusMetrics
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from pyramid.settings import aslist

from .utils import list_to_dict, resolve_entrypoint


class AbstractMiddlewareBuilder(abc.ABC):
    def __init__(self, settings, prefix, middlewares):
        self.settings = settings
        self.prefix = prefix
        self.middlewares = middlewares

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


class CircuitBreakerBuilder(AbstractMiddlewareBuilder):
    def build(self) -> SyncCircuitBreaker:
        settings = list_to_dict(self.settings, self.prefix)
        kwargs = {}
        for key in ("threshold", "ttl"):
            if key in settings:
                kwargs[key] = int(settings[key])

        uow = settings.get("uow", "purgatory:SyncInMemoryUnitOfWork")
        uow_cls = resolve_entrypoint(uow)
        uow_kwargs = list_to_dict(self.settings, f"{self.prefix}.uow")
        kwargs["uow"] = uow_cls(**uow_kwargs)
        if "prometheus" in self.middlewares:
            kwargs["prometheus_metrics"] = self.middlewares["prometheus"]
        return SyncCircuitBreaker(**kwargs)
