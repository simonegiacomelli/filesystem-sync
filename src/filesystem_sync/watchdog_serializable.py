import json
import sys
import tempfile
import threading
from dataclasses import dataclass
from datetime import timedelta
from pathlib import Path
from typing import List

from watchdog.events import FileSystemEvent

from filesystem_sync.any_observer import AnyObserver
from filesystem_sync.debounced_watch import DebouncedObserver
from filesystem_sync.debouncer import Debouncer
from filesystem_sync.debouncer_thread import DebouncerThread


@dataclass
class FilesystemSyncEvent:
    name: str


def serializable_event(event: FileSystemEvent) -> FilesystemSyncEvent:
    return None


def main():
    def new_tmp_path() -> Path:
        return Path(tempfile.mkdtemp(prefix='debounce-harness'))

    def print_event(event):
        print(f'event={event}')
        j = serializable_event(event)
        print(json.dumps(j))

    path = new_tmp_path()
    o = AnyObserver(path, print_event)
    o.watch_directory()

    print('new file')
    path.joinpath('new_file.txt').write_text('new file')


if __name__ == '__main__':
    main()

if __name__ == '__main__':
    main()
