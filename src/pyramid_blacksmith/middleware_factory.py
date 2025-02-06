"""
Middleware factories.

Create a dedicated blacksmith middleware per request to get the request
context purpose in the middleware.

This is usefull to proxify some data from parent request to sub request.
"""

import abc

from blacksmith import SyncHTTPAddHeadersMiddleware, SyncHTTPMiddleware
from pyramid.request import Request


class AbstractMiddlewareFactoryBuilder(abc.ABC):
    """Build the factory"""

    @abc.abstractmethod
    def __init__(self, **kwargs: dict[str, bool]): ...

    @abc.abstractmethod
    def __call__(self, request: Request) -> SyncHTTPMiddleware:
        """Called on demand per request to build a client with this middleware"""


class ForwardHeaderFactoryBuilder(AbstractMiddlewareFactoryBuilder):
    """
    Forward headers (every keys in kwargs)

    :param kwargs: headers
    """

    def __init__(self, **kwargs: dict[str, bool]):
        self.headers = list(kwargs.keys())

    def __call__(self, request: Request) -> SyncHTTPAddHeadersMiddleware:
        headers: dict[str, str] = {}
        for hdr in self.headers:
            val = request.headers.get(hdr)
            if val:
                headers[hdr] = val
        return SyncHTTPAddHeadersMiddleware(headers)


class AcceptLanguageFactoryBuilder(AbstractMiddlewareFactoryBuilder):
    """
    Forward the pyramid request locale_name to sub call in a Accept-Language header.
    """

    def __init__(self, **kwargs: dict[str, bool]): ...

    def __call__(self, request: Request) -> SyncHTTPAddHeadersMiddleware:
        return SyncHTTPAddHeadersMiddleware({"Accept-Language": request.locale_name})
