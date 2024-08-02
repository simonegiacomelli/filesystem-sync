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
        self.source = tmp_path / 'source'
        self.source.mkdir()
        self.target = tmp_path / 'target'
        self.target.mkdir()
        self.all_events = []
        self.window = timedelta(milliseconds=100)
        self.activities = ActivityMonitor(self.window + timedelta(milliseconds=10))

        def callback(events: List[FileSystemEvent]):
            self.activities.touch()
            self.all_events.extend(events)

        self.debounced_watcher = WatchdogDebouncer(tmp_path, self.window, callback)
        self.debounced_watcher.start()
        self.activities.touch()

    def wait_at_rest(self):
        [sleep(0.1) for _ in range(20) if not self.activities.at_rest()]
        assert self.activities.at_rest()

    def do_sync(self):
        changes = self.get_changes()
        self.apply_changes(changes)

    def apply_changes(self, changes):
        sync.sync_target(self.target, json.loads(json.dumps(changes)))

    def get_changes(self):
        changes = sync.sync_source(self.source, self.all_events)
        dumps = json.dumps(changes)
        print(f'\ndumps=```{dumps}```')
        return changes


@pytest.fixture
def target(tmp_path):
    fixture = TargetFixture(tmp_path)
    yield fixture
    fixture.debounced_watcher.stop()
    fixture.debounced_watcher.join()


def test_new_file(target):
    # GIVEN
    (target.source / 'new_file.txt').write_text('new file')
    target.wait_at_rest()

    # WHEN
    target.do_sync()

    # THEN
    assert (target.target / 'new_file.txt').exists()
    assert (target.target / 'new_file.txt').read_text() == 'new file'


def test_new_file__optimize(target):
    # GIVEN
    (target.source / 'new_file.txt').write_text('new file')
    (target.source / 'new_file.txt').write_text('new file2')
    target.wait_at_rest()

    # WHEN
    changes = target.get_changes()
    target.apply_changes(changes)

    # THEN
    assert (target.target / 'new_file.txt').exists()
    assert (target.target / 'new_file.txt').read_text() == 'new file2'
    assert len(changes) == 1


def test_new_file_and_delete(target):
    # GIVEN
    (target.source / 'new_file.txt').write_text('new file')
    (target.source / 'new_file.txt').write_text('new file2')
    (target.source / 'new_file.txt').unlink()
    target.wait_at_rest()

    # WHEN
    changes = target.get_changes()

    # THEN
    assert changes == []
