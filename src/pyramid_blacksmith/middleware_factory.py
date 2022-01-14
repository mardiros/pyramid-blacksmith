"""Middleware"""
import abc

from blacksmith import SyncHTTPAddHeadersMiddleware, SyncHTTPMiddleware
from pyramid.request import Request


class HTTPMiddlewareFactoryBuilder(abc.ABC):
    """Build the factory"""

    @abc.abstractmethod
    def __call__(self, request: Request) -> SyncHTTPMiddleware:
        """Called on demand per request to build a client with this middleware"""


class ForwardHeaderFactoryBuilder:
    def __init__(self, **kwargs):
        self.headers = list(kwargs.keys())

    def __call__(self, request: Request) -> SyncHTTPAddHeadersMiddleware:
        headers = {}
        for hdr in self.headers:
            val = request.headers.get(hdr)
            if val:
                headers[hdr] = val
        return SyncHTTPAddHeadersMiddleware(headers)
