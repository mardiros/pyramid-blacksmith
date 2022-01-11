from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.domain.model.params import CollectionParser
from blacksmith.domain.typing import SyncMiddleware
from blacksmith.middleware._sync.base import SyncHTTPMiddleware
from blacksmith.service._sync.base import SyncAbstractTransport
from blacksmith.typing import HttpMethod
from prometheus_client import CollectorRegistry

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
