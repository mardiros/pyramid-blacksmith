import importlib
from typing import Any

from pyramid.exceptions import ConfigurationError  # type: ignore
from pyramid.settings import aslist  # type: ignore

from .typing import Settings


def list_to_dict(
    settings: Settings,
    setting: str,
    with_flag: bool = False,
) -> Settings:
    """
    Cast the setting ``setting`` from the settings `settings`.

    .. code-block:: ini

        setting =
            key value
            key2 yet another value
            flag_key

    will return

    .. code-block:: python

        {"key": "value", "key2": "yet another value", "flag_key": True}

    """
    list_ = aslist(settings.get(setting, ""), flatten=False)
    dict_ = {}
    for idx, param in enumerate(list_):
        try:
            key, val = param.split(maxsplit=1)
            dict_[key] = val
        except ValueError:
            if with_flag:
                dict_[param] = True
            else:
                raise ConfigurationError(f"Invalid value {param} in {setting}[{idx}]")
    return dict_


def resolve_entrypoint(path: str) -> Any:
    """
    Resolve a class from the configuration.

    string ``path.to:Class`` will return the type ``Class``.
    """
    module_name, _, attr = path.partition(":")
    module = importlib.import_module(module_name)
    return getattr(module, attr) if attr else module
