from blacksmith.domain.model import HTTPRequest, HTTPResponse, HTTPTimeout
from blacksmith.service._sync.base import SyncAbstractTransport
from blacksmith.typing import HttpMethod


class DummyTransport(SyncAbstractTransport):
    def request(
        self, method: HttpMethod, request: HTTPRequest, timeout: HTTPTimeout
    ) -> HTTPResponse:
        return HTTPResponse(200, headers=request.headers, json=request.body)
