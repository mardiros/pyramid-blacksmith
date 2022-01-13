import pytest

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
def test_list_to_dict(params):
    dict_ = list_to_dict(params["settings"], "key")
    assert dict_ == params["expected"]
