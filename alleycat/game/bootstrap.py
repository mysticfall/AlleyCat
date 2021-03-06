import json
import logging
import sys
from collections import OrderedDict
from importlib import import_module
from logging.config import fileConfig
from pathlib import Path
from typing import Callable, List, Sequence

from bge.types import KX_GameObject, KX_PythonComponent
from bpy.path import abspath
from validator_collection import not_empty, validators

from alleycat.event import EventLoopScheduler
from alleycat.game import GameContext
from alleycat.log import LoggingSupport

Initializer = Callable[[], None]

_initialized = False
_initializers: List[Initializer] = []


class Bootstrap(LoggingSupport, KX_PythonComponent):
    args = OrderedDict((
        ("key", "alleycat"),
        ("config", "//config.json")
    ))

    context: GameContext

    scheduler: EventLoopScheduler

    # noinspection PyUnusedLocal
    def __init__(self, obj: KX_GameObject):
        super().__init__()

    def start(self, args: dict) -> None:
        key = validators.string(args["key"])
        config_path = validators.string(args["config"])

        print(f"Starting {key}.")

        self.context = GameContext()

        config_file = Path(abspath(config_path))

        print(f"Loading configuration from {config_file}.")

        injection_targets: Sequence[str] = ()

        if config_file.exists():
            with open(config_file) as f:
                config = json.load(f)

                self.context.config.from_dict(config)

                if "logging" in config:
                    logging_conf = config["logging"]
                    logging_conf["disable_existing_loggers"] = False

                    logging.config.dictConfig(logging_conf)

                if "dependency-injection" in config:
                    di_config = config["dependency-injection"]

                    injection_targets = di_config["modules"] if "modules" in di_config else ()

        def except_hook(tpe, value, traceback):
            if tpe != KeyboardInterrupt:
                self.logger.exception("Unhandled error occurred:", exc_info=value, stack_info=traceback)

            sys.__excepthook__(tpe, value, traceback)

        self.scheduler = self.context.scheduler()

        # noinspection SpellCheckingInspection
        sys.excepthook = except_hook

        if len(injection_targets) > 0:
            self.logger.info("Injecting dependencies to modules: %s", injection_targets)

            self.context.wire(modules=tuple(map(import_module, injection_targets)))

        for callback in _initializers:
            try:
                callback()
            except Exception as e:
                self.logger.exception(e, exc_info=True)

        global _initialized

        _initialized = True
        _initializers.clear()

        self.logger.info("Bootstrap has completed successfully.")

    def update(self) -> None:
        if self.scheduler:
            self.scheduler.process()

    def dispose(self) -> None:
        self.logger.info("Disposing context.")

        if self.context:
            self.context.unwire()
            self.context.shutdown_resources()

    @staticmethod
    def on_ready(callback: Initializer) -> None:
        not_empty(callback)

        if _initialized:
            callback()
        else:
            _initializers.append(callback)
