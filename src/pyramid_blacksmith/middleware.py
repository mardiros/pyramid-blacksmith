import abc

from blacksmith import SyncPrometheusMetrics
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from prometheus_client import REGISTRY
from pyramid.settings import aslist


class MiddlewareBuilder(abc.ABC):
    def __init__(self, settings, prefix):
        self.settings = settings
        self.prefix = prefix

    @abc.abstractmethod
    def build(self, *args) -> SyncHTTPMiddleware:
        """Build the Middleware"""


class PrometheusMetricsBuilder(MiddlewareBuilder):
    def build(self, registry=REGISTRY) -> SyncPrometheusMetrics:
        buckets = None
        buckets_key = f"{self.prefix}.buckets"
        buckets_val = self.settings.get(buckets_key)
        if buckets_val:
            buckets = [float(val) for val in aslist(buckets_val)]
        return SyncPrometheusMetrics(buckets, registry=registry)
