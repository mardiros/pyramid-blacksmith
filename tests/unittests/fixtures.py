from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.params import CollectionParser
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from blacksmith.service._sync.base import SyncAbstractTransport
from blacksmith.middleware._sync.http_caching import (
    AbstractCachingPolicy,
    AbstractSerializer,
)
from blacksmith.typing import HttpMethod
from prometheus_client import CollectorRegistry
from purgatory import SyncInMemoryUnitOfWork

from pyramid_blacksmith.middleware import AbstractMiddlewareBuilder


class DummyTransport(SyncAbstractTransport):
    def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        return HTTPResponse(200, headers=request.headers, json=request.body)


class DummyCollectionParser(CollectionParser):
    pass


class DummyMiddleware(SyncHTTPMiddleware):
    def __init__(self, tracker=None):
        self.tracker = tracker

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(req, method, client_name, path) -> HTTPResponse:
            return next(req, method, client_name, path)

        return handle


class DummyMiddlewareBuilder(AbstractMiddlewareBuilder):
    def build(self) -> SyncHTTPMiddleware:
        tracker_key = f"{self.prefix}.tracker"
        tracked = self.settings.get(tracker_key)
        return DummyMiddleware(tracked)


registry = CollectorRegistry()


class DummyPurgatoryUow(SyncInMemoryUnitOfWork):
    def __init__(self, url: str):
        self.url = url


class DummyCachePolicy(AbstractCachingPolicy):
    def __init__(self, foo):
        self.foo = foo

    def handle_request(self, req, method, client_name, path):
        """A function to decide if the http request is cachable."""
        return False

    def get_vary_key(self, client_name, path, request):
        return ""

    def get_response_cache_key(self, client_name, path, req, vary):
        return ""

    def get_cache_info_for_response(self, client_name, path, req, resp):
        return (0, "", [])


class DummySerializer(AbstractSerializer):
    @staticmethod
    def loads(s):
        return b""

    @staticmethod
    def dumps(obj):
        return ""
