import pytest
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from pyramid.testing import DummyRequest

from pyramid_blacksmith.middleware_factory import ForwardHeaderFactoryBuilder


def echo_middleware(req, method, client_name, path) -> HTTPResponse:
    return HTTPResponse(200, req.headers, json=req)


@pytest.mark.parametrize(
    "headers",
    [{"Authorization": True, "Accept-Language": True}],
)
@pytest.mark.parametrize(
    "params",
    [
        {
            "pyramid_request": DummyRequest({}, headers={}),
            "blacksmith_request": HTTPRequest("/", headers={}),
            "expected": {},
        },
        {
            "pyramid_request": DummyRequest({}, headers={"Accept-Language": "fr"}),
            "blacksmith_request": HTTPRequest("/", headers={}),
            "expected": {"Accept-Language": "fr"},
        },
        {
            "pyramid_request": DummyRequest({}, headers={"Accept-Language": "fr"}),
            "blacksmith_request": HTTPRequest("/", headers={"Accept-Language": "en"}),
            "expected": {"Accept-Language": "fr"},
        },
        {
            "pyramid_request": DummyRequest(
                {}, headers={"Accept-Language": "fr", "Authorization": "Bearer abc"}
            ),
            "blacksmith_request": HTTPRequest("/", headers={"Accept-Language": "en"}),
            "expected": {"Accept-Language": "fr", "Authorization": "Bearer abc"},
        },
        {
            "pyramid_request": DummyRequest(
                {}, headers={"Accept-Language": "fr", "Accept-Encoding": "brocoli"}
            ),
            "blacksmith_request": HTTPRequest("/", headers={"Accept-Language": "en"}),
            "expected": {"Accept-Language": "fr"},
        },
        {
            "pyramid_request": DummyRequest({}, headers={"Accept-Encoding": "brocoli"}),
            "blacksmith_request": HTTPRequest("/", headers={"Accept-Language": "en"}),
            "expected": {"Accept-Language": "en"},
        },
    ],
)
def test_forward_header_factory_builder(headers, params):
    facto = ForwardHeaderFactoryBuilder(**headers)
    middleware = facto(params["pyramid_request"])
    query = middleware(echo_middleware)
    resp = query(params["blacksmith_request"], "GET", "cli", "/")
    assert resp.headers == params["expected"]
