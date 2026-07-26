__version__ = "5.1.0"

from typing import Any

from .OsmApi import *  # noqa
from .errors import *  # noqa
from . import dom  # noqa
from . import errors  # noqa
from . import http  # noqa
from . import parser  # noqa
from . import xmlbuilder  # noqa


def __getattr__(name: str) -> Any:
    """
    Resolve a deprecated error name to its replacement (see PEP 562).

    Star-imports don't pick up the module-level `__getattr__` of
    `osmapi.errors`, so the deprecated names are forwarded here to keep
    `osmapi.UsernamePasswordMissingError` working (with a
    `DeprecationWarning`) until version 7.0.
    """
    if name in errors.DEPRECATED_ERROR_NAMES:
        return errors.resolve_deprecated_name(name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
