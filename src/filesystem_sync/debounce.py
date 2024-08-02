from __future__ import annotations

from typing import Any, Callable, List
from datetime import datetime, timedelta

class Debouncer:
    def __init__(self, window_ms: int, callback: Callable[[List[Any]], None], time_func: Callable[[], datetime] = datetime.now):
        self.window_ms = window_ms
        self.callback = callback
        self.time_func = time_func
        self.events: List[Any] = []
        self.last_event_time: datetime | None = None

    def add_event(self, event: Any) -> None:
        current_time = self.time_func()
        self.events.append(event)
        self.last_event_time = current_time

    def process(self) -> None:
        if not self.events or self.last_event_time is None:
            return

        current_time = self.time_func()
        time_since_last_event = current_time - self.last_event_time

        if time_since_last_event >= timedelta(milliseconds=self.window_ms):
            events_to_emit = self.events.copy()
            self.events.clear()
            self.last_event_time = None
            self.callback(events_to_emit)

    def time_until_next_emission(self) -> timedelta | None:
        if not self.events or self.last_event_time is None:
            return None

        current_time = self.time_func()
        time_since_last_event = current_time - self.last_event_time
        time_remaining = timedelta(milliseconds=self.window_ms) - time_since_last_event

        return max(time_remaining, timedelta(0))