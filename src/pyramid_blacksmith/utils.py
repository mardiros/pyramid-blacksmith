from pyramid.exceptions import ConfigurationError
from pyramid.settings import aslist

from .typing import Settings


def list_to_dict(settings: Settings, setting: str) -> Settings:
    list_ = aslist(settings.get(setting, ""), flatten=False)
    dict_ = {}
    for idx, param in enumerate(list_):
        try:
            key, val = param.split(maxsplit=1)
            dict_[key] = val
        except ValueError:
            raise ConfigurationError(f"Invalid value {param} in {setting}[{idx}]")
    return dict_
