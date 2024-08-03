from __future__ import annotations

from datetime import datetime, timedelta
from typing import Callable

import pytest

from tests.time_mock import TimeMock

_time_mock = TimeMock()


class ActivityMonitor:

    def __init__(self, window: timedelta, time_func: Callable[[], datetime] = datetime.utcnow):
        super().__init__()
        self._last_touch: datetime | None = None
        self.window = window
        self._time_func = time_func

    def at_rest(self) -> bool:
        delta = self.rest_delta()
        if delta is None:
            print('at_rest: True')
            return True
        ar = delta >= self.window
        print(f'at_rest: {ar}')
        return ar

    def rest_delta(self) -> timedelta | None:
        lt = self._last_touch
        if lt is None:
            return None
        delta = self._time_func() - lt
        return delta

    def touch(self):
        self._last_touch = self._time_func()


@pytest.fixture
def target():
    _time_mock.reset()
    return ActivityMonitor(timedelta(milliseconds=20), time_func=_time_mock)


def test_activity_monitor(target):
    assert target.at_rest()


def test_touch__change_at_rest(target):
    target.touch()
    assert not target.at_rest()


def test_touch_after_time_window(target):
    target.touch()
    _time_mock.advance(timedelta(milliseconds=21))
    assert target.at_rest()
