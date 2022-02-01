import abc
from typing import Any, Dict

from blacksmith import (
    PrometheusMetrics,
    SyncCircuitBreakerMiddleware,
    SyncHTTPCacheMiddleware,
    SyncHTTPMiddleware,
    SyncPrometheusMiddleware,
)
from pyramid.exceptions import ConfigurationError  # type: ignore

from pyramid_blacksmith.typing import Settings

from .utils import list_to_dict, resolve_entrypoint


class AbstractMiddlewareBuilder(abc.ABC):
    def __init__(
        self,
        settings: Settings,
        prefix: str,
        metrics: PrometheusMetrics,
    ):
        self.settings = settings
        self.prefix = prefix
        self.metrics = metrics

    @abc.abstractmethod
    def build(self) -> SyncHTTPMiddleware:
        """Build the Middleware"""


class PrometheusMetricsBuilder(AbstractMiddlewareBuilder):
    def build(self) -> SyncPrometheusMiddleware:
        return SyncPrometheusMiddleware(metrics=self.metrics)


class CircuitBreakerBuilder(AbstractMiddlewareBuilder):
    def build(self) -> SyncCircuitBreakerMiddleware:
        settings = list_to_dict(self.settings, self.prefix)
        kwargs: Dict[str, Any] = {}
        for key in ("threshold", "ttl"):
            if key in settings:
                kwargs[key] = int(settings[key])

        uow = settings.get("uow", "purgatory:SyncInMemoryUnitOfWork")
        uow_cls = resolve_entrypoint(uow)
        uow_kwargs = list_to_dict(self.settings, f"{self.prefix}.uow")
        kwargs["uow"] = uow_cls(**uow_kwargs)
        kwargs["metrics"] = self.metrics
        return SyncCircuitBreakerMiddleware(**kwargs)  # type: ignore


class HTTPCacheBuilder(AbstractMiddlewareBuilder):
    def build(self) -> SyncHTTPCacheMiddleware:
        import redis  # noqa

        settings = list_to_dict(self.settings, self.prefix)
        kwargs = {}

        mod = "blacksmith.domain.model.middleware.http_cache"
        redis_url = settings.get("redis")
        if not redis_url:
            raise ConfigurationError(f"Missing sub-key redis in setting {self.prefix}")
        kwargs["cache"] = redis.from_url(redis_url)

        policy_key = settings.get("policy", f"{mod}:CacheControlPolicy")
        policy_params = list_to_dict(self.settings, f"{self.prefix}.policy")
        policy_cls = resolve_entrypoint(policy_key)
        kwargs["policy"] = policy_cls(**policy_params)  # type: ignore

        srlz_key = settings.get("serializer", "json")
        kwargs["serializer"] = resolve_entrypoint(srlz_key)  # type: ignore
        kwargs["metrics"] = self.metrics  # type: ignore
        return SyncHTTPCacheMiddleware(**kwargs)  # type: ignore
