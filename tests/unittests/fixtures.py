from typing import Any, List
from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.params import CollectionParser
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from blacksmith.middleware._sync.http_caching import (
    AbstractCachingPolicy,
    AbstractSerializer,
)
from blacksmith.typing import ClientName, Path
from blacksmith.service._sync.base import SyncAbstractTransport
from prometheus_client import CollectorRegistry
from purgatory import SyncInMemoryUnitOfWork

from pyramid_blacksmith.middleware import AbstractMiddlewareBuilder


class DummyTransport(SyncAbstractTransport):
    def __call__(
        self,
        req: HTTPRequest,
        client_name: ClientName,
        path: Path,
        timeout: HTTPTimeout,
    ) -> HTTPResponse:
        return HTTPResponse(200, headers=req.headers, json=req.body)


class DummyCollectionParser(CollectionParser):
    pass


class DummyMiddleware(SyncHTTPMiddleware):
    def __init__(self, tracker: Any = None):
        self.tracker = tracker

    def __call__(self, next: SyncMiddleware) -> SyncMiddleware:
        def handle(
            req: HTTPRequest,
            client_name: ClientName,
            path: Path,
            timeout: HTTPTimeout,
        ) -> HTTPResponse:
            return next(req, client_name, path, timeout)

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
    def __init__(self, foo: Any):
        self.foo = foo

    def handle_request(self, req: HTTPRequest, client_name: str, path: str):
        """A function to decide if the http request is cachable."""
        return False

    def get_vary_key(self, client_name: str, path: str, request: HTTPRequest):
        return ""

    def get_response_cache_key(
        self, client_name: str, path: str, req: HTTPRequest, vary: List[str]
    ):
        return ""

    def get_cache_info_for_response(
        self, client_name: str, path: str, req: HTTPRequest, resp: HTTPResponse
    ):
        return (0, "", [])


class DummySerializer(AbstractSerializer):
    @staticmethod
    def loads(s: str) -> Any:
        return b""

    @staticmethod
    def dumps(obj: Any) -> str:
        return ""
