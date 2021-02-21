from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional

from bpy.types import Action
from returns.maybe import Maybe
from validator_collection import validators


class PlayMode(Enum):
    """bge.logic.KX_ACTION_MODE_PLAY"""
    Play = 0

    """bge.logic.KX_ACTION_MODE_LOOP"""
    Loop = 1

    """bge.logic.KX_ACTION_MODE_PING_PONG"""
    PingPong = 2


class BlendMode(Enum):
    """bge.logic.KX_ACTION_BLEND_BLEND"""
    Blend = 0

    """bge.logic.KX_ACTION_BLEND_ADD"""
    Add = 1


class Animator(ABC):
    __slots__ = ["_time_delta", "_layer", "_weight", "_speed"]

    def __init__(self, time_delta: float = 0, layer: int = 0, weight: float = 1.0) -> None:
        self.time_delta = time_delta
        self.layer = layer
        self.weight = weight
        self._speed = 1.0

    @property
    def time_delta(self) -> float:
        return self._time_delta

    @time_delta.setter
    def time_delta(self, value: float) -> None:
        self._time_delta = validators.float(value, minimum=0.0)

    @property
    def layer(self) -> int:
        return self._layer

    @layer.setter
    def layer(self, value: int) -> None:
        self._layer = validators.integer(value, minimum=0)

    @property
    def weight(self) -> float:
        return self._weight

    @weight.setter
    def weight(self, value: float) -> None:
        self._weight = validators.float(value, minimum=0.0, maximum=1.0)

    @property
    def speed(self) -> float:
        return self._speed

    @abstractmethod
    def play(self,
             action: Action,
             start_frame: Optional[float] = None,
             end_frame: Optional[float] = None,
             priority=0,
             blend: float = 0,
             play_mode: PlayMode = PlayMode.Play,
             blend_mode: BlendMode = BlendMode.Blend) -> None:
        pass

    @abstractmethod
    def stop(self):
        pass

    @property
    @abstractmethod
    def action(self) -> Maybe[Action]:
        pass

    # TODO See python/mypy#1362 and python/mypy#4165. I HATE Python.
    @property  # type: ignore
    @abstractmethod
    def frame(self) -> float:
        pass

    @frame.setter  # type: ignore
    @abstractmethod
    def frame(self, value: float) -> None:
        pass

    @property
    @abstractmethod
    def playing(self) -> bool:
        pass