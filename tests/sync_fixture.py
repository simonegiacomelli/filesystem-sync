import filecmp
import json
import shutil
from datetime import timedelta
from pathlib import Path
from time import sleep
from typing import List

from watchdog.events import FileSystemEvent

from filesystem_sync import sync
from filesystem_sync.watchdog_debouncer import WatchdogDebouncer
from tests.activity_monitor import ActivityMonitor


class SyncFixture:

    def __init__(self, tmp_path: Path):
        self.source = tmp_path / 'source'
        self.source.mkdir()
        self.target = tmp_path / 'target'
        self.target.mkdir()
        self.all_events = []
        self.window = timedelta(milliseconds=100)
        self.activities = ActivityMonitor(self.window + timedelta(milliseconds=10))
        self.dircmp = None

        def callback(events: List[FileSystemEvent]):
            self.activities.touch()
            self.all_events.extend(events)

        self.debounced_watcher = WatchdogDebouncer(tmp_path, self.window, callback)

        self.activities.touch()

    def start(self):
        self.debounced_watcher.start()

    def wait_at_rest(self):
        [sleep(0.1) for _ in range(20) if not self.activities.at_rest()]
        assert self.activities.at_rest()

    def do_sync(self):
        changes = self.get_changes()
        self.apply_changes(changes)
        return changes

    def apply_changes(self, changes):
        sync.sync_target(self.target, json.loads(json.dumps(changes)))

    def get_changes(self):
        changes = sync.sync_source(self.source, self.all_events)
        dumps = json.dumps(changes)
        print(f'\ndumps=```{dumps}```')
        return changes

    def do_init(self):
        self.apply_changes(sync.sync_init(self.source))

    def synchronized(self):
        self._calc_synchronized()
        return self._is_synchronized()

    def _is_synchronized(self) -> bool:
        return not self.dircmp.left_only and not self.dircmp.right_only and not self.dircmp.diff_files

    def _calc_synchronized(self):
        self.dircmp = filecmp.dircmp(self.source, self.target)

    def sync_error(self):
        def diff_printable():
            return f'source_only={self.dircmp.left_only} target_only={self.dircmp.right_only} diff_files={self.dircmp.diff_files}'

        return None if self._is_synchronized() else diff_printable()

    def copy_source_to_target(self):
        shutil.rmtree(self.target, ignore_errors=True)
        shutil.copytree(self.source, self.target, dirs_exist_ok=True)
