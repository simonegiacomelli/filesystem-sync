import json
from datetime import timedelta
from time import sleep
from typing import List

from watchdog.events import FileSystemEvent

from filesystem_sync.serializable import serializable_events
from filesystem_sync.watchdog_debouncer import WatchdogDebouncer


def test_new_file(tmp_path):
    all_events = []

    def callback(events: List[FileSystemEvent]):
        all_events.extend(events)

    debounced_watcher = WatchdogDebouncer(tmp_path, timedelta(milliseconds=100), callback)
    debounced_watcher.start()

    tmp_path.joinpath('new_file.txt').write_text('new file')
    tmp_path.joinpath('new_file2.txt').write_text('new file')
    [sleep(0.1) for _ in range(10) if not all_events]

    assert len(all_events) > 0

    target = serializable_events(all_events)
    j = json.dumps(target)
    print(f'j=```{j}```')

    debounced_watcher.stop()
    debounced_watcher.join()
