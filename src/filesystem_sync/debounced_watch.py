import json
import sys
import tempfile
import threading
from datetime import timedelta
from pathlib import Path
from time import sleep

from watchdog.observers import Observer

from filesystem_sync.any_observer import AnyObserver
from filesystem_sync.debouncer import Debouncer
from filesystem_sync.debouncer_thread import DebouncerThread


class DebouncedObserver:

    def __init__(self, path: Path, debouncer: Debouncer):
        """path need to exist, otherwise the observer will throw an exception."""
        self._debouncer = debouncer
        self._path = path
        self._observer = Observer()

    def watch_directory(self):
        self._observer.schedule(AnyObserver(self._debouncer.add_event), str(self._path), recursive=True)
        self._observer.start()

    def stop_join(self):
        self._observer.stop()
        self._observer.join()


def main():
    def new_tmp_path() -> Path:
        return Path(tempfile.mkdtemp(prefix='debounce-harness'))

    debouncer = Debouncer(timedelta(milliseconds=100))

    def print_events(events):
        print('=' * 20 + f' current thread name={threading.current_thread().name}')
        print(f'len={len(events)} events={events}')
        j = json.dumps(events)
        print(j)

    DebouncerThread(debouncer, print_events)

    tmp_path = sys.argv[1] if len(sys.argv) > 1 else new_tmp_path()
    print(f'Watching {tmp_path}')
    DebouncedObserver(tmp_path, debouncer).watch_directory()

    while True:
        sleep(1)


if __name__ == '__main__':
    main()
