import json
from datetime import timedelta
from pathlib import Path
from time import sleep
from typing import List

import pytest
from watchdog.events import FileSystemEvent

from filesystem_sync.watchdog_debouncer import WatchdogDebouncer
from filesystem_sync import sync
from tests.activity_monitor import ActivityMonitor


class TargetFixture:

    def __init__(self, tmp_path: Path):
        self.tmp_path = tmp_path
        self.all_events = []
        self.window = timedelta(milliseconds=100)
        self.activities = ActivityMonitor(self.window + timedelta(milliseconds=10))

        def callback(events: List[FileSystemEvent]):
            self.activities.touch()
            self.all_events.extend(events)

        debounced_watcher = WatchdogDebouncer(tmp_path, self.window, callback)
        debounced_watcher.start()
        self.activities.touch()

    def wait_at_rest(self):
        [sleep(0.1) for _ in range(20) if not self.activities.at_rest()]
        assert self.activities.at_rest()


@pytest.fixture
def target(tmp_path):
    return TargetFixture(tmp_path)


def test_new_file(target):
    target.tmp_path.joinpath('new_file.txt').write_text('new file')
    target.wait_at_rest()

    assert len(target.all_events) > 0


    return
    target = serializable_events(all_events)
    j = json.dumps(target)
    print(f'j=```{j}```')

    debounced_watcher.stop()
    debounced_watcher.join()
