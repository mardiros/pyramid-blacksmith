from typing import Any

import pytest
from blacksmith import HTTPTimeout
from blacksmith.domain.model.http import HTTPRequest, HTTPResponse
from blacksmith.typing import ClientName, Path
from pyramid.testing import DummyRequest

from pyramid_blacksmith.middleware_factory import (
    AcceptLanguageFactoryBuilder,
    ForwardHeaderFactoryBuilder,
)


def echo_middleware(
    req: HTTPRequest,
    client_name: ClientName,
    path: Path,
    timeout: HTTPTimeout,
) -> HTTPResponse:
    return HTTPResponse(200, req.headers, json=req)


@pytest.mark.parametrize(
    "headers",
    [{"Authorization": True, "Accept-Language": True}],
)
@pytest.mark.parametrize(
    "params",
    [
        {
            "pyramid_request": DummyRequest(),
            "blacksmith_request": HTTPRequest("GET", "/", headers={}),
            "expected": {},
        },
        {
            "pyramid_request": DummyRequest(headers={"Accept-Language": "fr"}),
            "blacksmith_request": HTTPRequest("GET", "/", headers={}),
            "expected": {"Accept-Language": "fr"},
        },
        {
            "pyramid_request": DummyRequest(headers={"Accept-Language": "fr"}),
            "blacksmith_request": HTTPRequest(
                "GET", "/", headers={"Accept-Language": "en"}
            ),
            "expected": {"Accept-Language": "fr"},
        },
        {
            "pyramid_request": DummyRequest(
                headers={"Accept-Language": "fr", "Authorization": "Bearer abc"}
            ),
            "blacksmith_request": HTTPRequest(
                "GET", "/", headers={"Accept-Language": "en"}
            ),
            "expected": {"Accept-Language": "fr", "Authorization": "Bearer abc"},
        },
        {
            "pyramid_request": DummyRequest(
                headers={"Accept-Language": "fr", "Accept-Encoding": "brocoli"}
            ),
            "blacksmith_request": HTTPRequest(
                "GET", "/", headers={"Accept-Language": "en"}
            ),
            "expected": {"Accept-Language": "fr"},
        },
        {
            "pyramid_request": DummyRequest(headers={"Accept-Encoding": "brocoli"}),
            "blacksmith_request": HTTPRequest(
                "GET", "/", headers={"Accept-Language": "en"}
            ),
            "expected": {"Accept-Language": "en"},
        },
    ],
)
def test_forward_header_factory_builder(
    headers: dict[str, Any], params: dict[str, Any]
):
    facto = ForwardHeaderFactoryBuilder(**headers)
    middleware = facto(params["pyramid_request"])
    query = middleware(echo_middleware)
    resp = query(params["blacksmith_request"], "cli", "/", HTTPTimeout())
    assert resp.headers == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            {
                "pyramid_request": DummyRequest(locale_name="zh-Hans"),
                "blacksmith_request": HTTPRequest("GET", "/", headers={}),
                "expected": {
                    "Accept-Language": "zh-Hans",
                },
            },
            id="inject header",
        ),
        pytest.param(
            {
                "pyramid_request": DummyRequest(locale_name="zh-Hans"),
                "blacksmith_request": HTTPRequest(
                    "GET", "/", headers={"Accept-Language": "en"}
                ),
                "expected": {
                    "Accept-Language": "zh-Hans",
                },
            },
            id="override header",
        ),
    ],
)
def test_accept_language_factory_builder(params: dict[str, Any]):
    facto = AcceptLanguageFactoryBuilder()
    middleware = facto(params["pyramid_request"])
    query = middleware(echo_middleware)
    resp = query(params["blacksmith_request"], "cli", "/", HTTPTimeout())
    assert resp.headers == params["expected"]
