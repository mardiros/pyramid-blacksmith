import abc

from blacksmith import SyncPrometheusMetrics
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from prometheus_client import REGISTRY
from pyramid.settings import aslist

from .utils import list_to_dict


class AbstractMiddlewareBuilder(abc.ABC):
    def __init__(self, settings, prefix):
        self.settings = settings
        self.prefix = prefix

    @abc.abstractmethod
    def build(self, *args) -> SyncHTTPMiddleware:
        """Build the Middleware"""


class PrometheusMetricsBuilder(AbstractMiddlewareBuilder):
    def build(self, registry=REGISTRY) -> SyncPrometheusMetrics:
        buckets = None
        settings = list_to_dict(self.settings, self.prefix)
        buckets_val = settings.get("buckets")
        if buckets_val:
            buckets = [float(val) for val in aslist(buckets_val)]
        return SyncPrometheusMetrics(buckets, registry=registry)
