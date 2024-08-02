import filecmp
import json
import shutil
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


@pytest.fixture
def target(tmp_path):
    fixture = TargetFixture(tmp_path)
    yield fixture
    fixture.debounced_watcher.stop()
    fixture.debounced_watcher.join()


def test_new_file(target):
    # GIVEN
    target.start()
    (target.source / 'new_file.txt').write_text('new file')
    target.wait_at_rest()

    # WHEN
    target.do_sync()

    # THEN
    assert (target.target / 'new_file.txt').exists()
    assert (target.target / 'new_file.txt').read_text() == 'new file'


def test_new_file__optimize(target):
    # GIVEN
    target.start()
    (target.source / 'new_file.txt').write_text('new file')
    (target.source / 'new_file.txt').write_text('new file2')
    target.wait_at_rest()

    # WHEN
    changes = target.do_sync()

    # THEN
    assert (target.target / 'new_file.txt').exists()
    assert (target.target / 'new_file.txt').read_text() == 'new file2'
    assert len(changes) == 1


def test_new_file_and_delete(target):
    # GIVEN
    target.start()
    (target.source / 'new_file.txt').write_text('new file')
    (target.source / 'new_file.txt').write_text('new file2')
    (target.source / 'new_file.txt').unlink()
    target.wait_at_rest()

    # WHEN
    changes = target.get_changes()

    # THEN
    assert changes == []


def test_new_file_in_subfolder(target):
    # GIVEN
    target.start()
    sub1 = target.source / 'sub1'
    sub1.mkdir()
    (sub1 / 'foo.txt').write_text('sub-file')
    target.wait_at_rest()

    # WHEN
    target.do_sync()

    # THEN
    assert (target.target / 'sub1/foo.txt').exists()
    assert (target.target / 'sub1/foo.txt').read_text() == 'sub-file'


def test_delete_file(target):
    # GIVEN
    source_foo = target.source / 'foo.txt'
    source_foo.write_text('content1')
    target_foo = target.target / 'foo.txt'
    target_foo.write_text('content1')
    target.start()

    source_foo.unlink()
    target.wait_at_rest()

    # WHEN
    changes = target.do_sync()

    # THEN
    assert not target_foo.exists()
    assert len(changes) == 1


def test_created(target):
    # GIVEN
    target.start()
    (target.source / 'foo.txt').touch()
    target.wait_at_rest()

    # WHEN
    changes = target.do_sync()

    # THEN
    assert (target.target / 'foo.txt').exists()
    assert (target.target / 'foo.txt').stat().st_size == 0
    assert len(changes) == 1


def test_init(target):
    # GIVEN
    (target.source / 'foo.txt').write_text('c1')

    # WHEN
    target.do_init()

    # THEN
    assert (target.target / 'foo.txt').read_text() == 'c1'
    assert target.synchronized(), target.sync_error()


def test_synchronized_no_files(target):
    # GIVEN

    # WHEN
    target.do_init()

    # THEN
    assert target.synchronized()
    assert target.sync_error() is None


def test_synchronized_some_files(target):
    # GIVEN
    (target.source / 'foo.txt').write_text('c1')

    assert target.synchronized() is False
    assert target.sync_error() is not None


def test_delete_folder(target):
    # GIVEN
    (target.source / 'sub1').mkdir()
    (target.source / 'sub1/foo.txt').write_text('content1')
    target.copy_source_to_target()
    target.start()

    shutil.rmtree(target.source / 'sub1')
    target.wait_at_rest()

    # WHEN
    target.do_sync()

    # THEN
    assert target.synchronized(), target.sync_error()

def test_delete_folder__and_recreate_it(target):
    def build():
        (target.source / 'sub1').mkdir()
        (target.source / 'sub1/foo.txt').write_text('content1')

    # GIVEN
    build()
    target.copy_source_to_target()
    target.start()

    # WHEN
    shutil.rmtree(target.source / 'sub1')
    build()
    target.wait_at_rest()

    target.do_sync()

    # THEN
    assert target.synchronized(), target.sync_error()
