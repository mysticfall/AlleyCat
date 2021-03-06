from abc import ABC
from datetime import datetime, timedelta
from enum import Enum
from queue import PriorityQueue
from time import mktime
from typing import Final, Optional

import bge
from rx import Observable, operators as ops
from rx.core.typing import AbsoluteTime, RelativeTime, ScheduledAction, TState
from rx.disposable import Disposable
from rx.scheduler import ScheduledItem
from rx.scheduler.periodicscheduler import PeriodicScheduler
from rx.subject import Subject
from validator_collection import not_empty

from alleycat.event import EventLoopAware
from alleycat.log import LoggingSupport

DELTA_ZERO: Final = timedelta(0)


class TimeMode(Enum):
    Frame = 0
    Clock = 1
    Real = 2


class EventLoopScheduler(Disposable, LoggingSupport, PeriodicScheduler):

    def __init__(self, init_time: Optional[datetime] = None, mode: TimeMode = TimeMode.Frame) -> None:
        super().__init__()

        self.logger.info("Creating a scheduler with timer: %s.", mode.name)

        self._queue: PriorityQueue[ScheduledItem] = PriorityQueue()
        self._init_time = mktime((init_time if init_time else datetime.now()).timetuple())

        if mode == TimeMode.Frame:
            self._timer = bge.logic.getFrameTime
        elif mode == TimeMode.Clock:
            self._timer = bge.logic.getClockTime
        elif mode == TimeMode.Real:
            self._timer = bge.logic.getRealTime
        else:
            assert False

        self._on_process = Subject()

    @property
    def now(self) -> datetime:
        return datetime.fromtimestamp(self._init_time + self._timer())

    def schedule(self, action: ScheduledAction, state: Optional[TState] = None) -> Disposable:
        return self.schedule_absolute(self.now, action, state)

    def schedule_relative(self,
                          due: RelativeTime,
                          action: ScheduledAction,
                          state: Optional[TState] = None) -> Disposable:
        due = max(DELTA_ZERO, self.to_timedelta(due))

        return self.schedule_absolute(self.now + due, action, state)

    def schedule_absolute(self,
                          due: AbsoluteTime,
                          action: ScheduledAction,
                          state: Optional[TState] = None) -> Disposable:
        item = ScheduledItem(self, state, action, self.to_datetime(due))

        self._queue.put(item)

        return Disposable(item.cancel)

    def _peek(self) -> Optional[ScheduledItem]:
        return None if self._queue.empty() else self._queue.queue[0]

    def process(self) -> None:
        item: Optional[ScheduledItem] = self._peek()

        now = self.now

        self._on_process.on_next(now)

        while item and item.duetime <= now:
            item = self._queue.get()

            if not item.is_cancelled():
                item.invoke()

            item = self._peek()

    @property
    def on_process(self) -> Observable:
        return self._on_process

    def dispose(self) -> None:
        self.logger.info("Disposing scheduler instance.")

        self._on_process.dispose()

        super().dispose()


class SchedulerLoopSupport(EventLoopAware, ABC):

    def __init__(self, scheduler: EventLoopScheduler) -> None:
        self._scheduler = not_empty(scheduler)

        super().__init__()

        self.on_process \
            .pipe(ops.filter(lambda _: self.processing), ops.take_until(self.on_dispose)) \
            .subscribe(lambda _: self.process(), on_error=self.error_handler)

    @property
    def scheduler(self) -> EventLoopScheduler:
        return self._scheduler

    @property
    def on_process(self) -> Observable:
        return self.scheduler.on_process
