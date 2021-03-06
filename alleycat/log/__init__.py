import logging
from logging import Logger
from typing import Any

from bpy.types import ID
from validator_collection import not_empty

from .console import ConsoleLogger
from .error import ErrorHandler, ErrorHandlerSupport
from .support import LoggingSupport


def get_logger_name(obj: Any, drop_last_path: bool = True) -> str:
    not_empty(obj, allow_empty=True)

    segments = obj.__module__.split(".")
    identifiers = [obj.__qualname__ if isinstance(obj, type) else type(obj).__qualname__]

    if isinstance(obj, ID):
        identifiers.append(obj.name)

    index = -1 if drop_last_path else len(segments)

    return ".".join(segments[:index] + identifiers)


def get_logger(obj: Any) -> Logger:
    return logging.getLogger(get_logger_name(obj))
