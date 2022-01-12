from typing import Type

import pkg_resources
from pyramid.exceptions import ConfigurationError
from pyramid.settings import aslist

from .typing import Settings


def list_to_dict(settings: Settings, setting: str) -> Settings:
    """
    Cast the setting ``setting`` from the settings `settings`.

    .. code-block:: ini

        setting =
            key value
            key2 yet another value

    will return

    .. code-block:: python

        {"key": "value", "key2": "yet another value"}

    """
    list_ = aslist(settings.get(setting, ""), flatten=False)
    dict_ = {}
    for idx, param in enumerate(list_):
        try:
            key, val = param.split(maxsplit=1)
            dict_[key] = val
        except ValueError:
            raise ConfigurationError(f"Invalid value {param} in {setting}[{idx}]")
    return dict_


def resolve_entrypoint(path: str) -> Type:
    """
    Resolve a class from the configuration.

    string ``path.to:Class`` will return the type ``Class``.
    """
    ep = pkg_resources.EntryPoint.parse(f"x={path}")
    return ep.resolve()
