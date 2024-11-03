from typing import Any

import pytest
from pyramid.exceptions import ConfigurationError

from pyramid_blacksmith.binding import list_to_dict


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "key": [
                    "api/v1 http://api.v1",
                    "smtp smtp://host/",
                ]
            },
            "expected": {
                "api/v1": "http://api.v1",
                "smtp": "smtp://host/",
            },
        },
        {
            "settings": {
                "key": """
                    api/v1 http://api.v1
                    smtp   smtp://host/
                """
            },
            "expected": {
                "api/v1": "http://api.v1",
                "smtp": "smtp://host/",
            },
        },
    ],
)
def test_list_to_dict(params: dict[str, Any]):
    dict_ = list_to_dict(params["settings"], "key")
    assert dict_ == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {
                "key": """
                    tip
                    top
                """
            },
            "expected": {"tip": True, "top": True},
        },
        {
            "settings": {"key": ["tip", "top"]},
            "expected": {"tip": True, "top": True},
        },
        {
            "settings": {"key": ["tip tip", "top"]},
            "expected": {"tip": "tip", "top": True},
        },
    ],
)
def test_list_to_dict_with_flag(params: dict[str, Any]):
    dict_ = list_to_dict(params["settings"], "key", with_flag=True)
    assert dict_ == params["expected"]


@pytest.mark.parametrize(
    "params",
    [
        {
            "settings": {"key": ["tip", "top"]},
            "expected": "Invalid value tip in key[0]",
        },
        {
            "settings": {"key": ["tip tip", "top"]},
            "expected": "Invalid value top in key[1]",
        },
        {
            "settings": {
                "key": """
                    tip tip
                    top
                """
            },
            "expected": "Invalid value top in key[1]",
        },
    ],
)
def test_list_to_dict_raise(params: dict[str, Any]):
    with pytest.raises(ConfigurationError) as ctx:
        list_to_dict(params["settings"], "key")
    assert str(ctx.value) == params["expected"]
