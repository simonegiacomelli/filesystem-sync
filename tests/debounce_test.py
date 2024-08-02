import pytest
from datetime import datetime, timedelta
from typing import List, Any

from filesystem_sync.debounce import Debouncer


class TimeMock:
    def __init__(self):
        self.now = datetime(2023, 1, 1, 0, 0, 0)

    def __call__(self):
        return self.now

    def advance(self, delta: timedelta):
        self.now += delta

class EventRecorder:
    def __init__(self):
        self.events: List[List[Any]] = []

    def record(self, events: List[Any]):
        self.events.append(events)

@pytest.fixture
def debouncer_fixture():
    time_mock = TimeMock()
    event_recorder = EventRecorder()
    debouncer = Debouncer(100, event_recorder.record, time_mock)
    return debouncer, time_mock, event_recorder

def test_add_single_event(debouncer_fixture):
    debouncer, time_mock, event_recorder = debouncer_fixture

    debouncer.add_event("event1")
    debouncer.process()

    assert event_recorder.events == []

    time_mock.advance(timedelta(milliseconds=101))
    debouncer.process()

    assert event_recorder.events == [["event1"]]

def test_add_multiple_events_within_window(debouncer_fixture):
    debouncer, time_mock, event_recorder = debouncer_fixture

    debouncer.add_event("event1")
    time_mock.advance(timedelta(milliseconds=50))
    debouncer.add_event("event2")
    debouncer.process()

    assert event_recorder.events == []

    time_mock.advance(timedelta(milliseconds=51))
    debouncer.process()

    assert event_recorder.events == [["event1", "event2"]]

def test_add_events_across_windows(debouncer_fixture):
    debouncer, time_mock, event_recorder = debouncer_fixture

    debouncer.add_event("event1")
    time_mock.advance(timedelta(milliseconds=101))
    debouncer.process()

    debouncer.add_event("event2")
    time_mock.advance(timedelta(milliseconds=50))
    debouncer.add_event("event3")
    time_mock.advance(timedelta(milliseconds=51))
    debouncer.process()

    assert event_recorder.events == [["event1"], ["event2", "event3"]]

def test_time_until_next_emission(debouncer_fixture):
    debouncer, time_mock, _ = debouncer_fixture

    assert debouncer.time_until_next_emission() is None

    debouncer.add_event("event1")
    assert debouncer.time_until_next_emission() == timedelta(milliseconds=100)

    time_mock.advance(timedelta(milliseconds=50))
    assert debouncer.time_until_next_emission() == timedelta(milliseconds=50)

    time_mock.advance(timedelta(milliseconds=51))
    assert debouncer.time_until_next_emission() == timedelta(milliseconds=0)

def test_no_events_after_emission(debouncer_fixture):
    debouncer, time_mock, event_recorder = debouncer_fixture

    debouncer.add_event("event1")
    time_mock.advance(timedelta(milliseconds=101))
    debouncer.process()

    assert event_recorder.events == [["event1"]]
    assert debouncer.time_until_next_emission() is None

def test_multiple_process_calls(debouncer_fixture):
    debouncer, time_mock, event_recorder = debouncer_fixture

    debouncer.add_event("event1")
    debouncer.process()
    debouncer.process()

    assert event_recorder.events == []

    time_mock.advance(timedelta(milliseconds=101))
    debouncer.process()
    debouncer.process()

    assert event_recorder.events == [["event1"]]
    assert len(event_recorder.events) == 1