from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers import Observer

from filesystem_sync.debouncer import Debouncer


class DebouncedObserver:

    def __init__(self, path: Path, debouncer: Debouncer):
        """path need to exist, otherwise the observer will throw an exception."""
        self._debouncer = debouncer
        self._path = path
        self._observer = Observer()

    def watch_directory(self):
        self._observer.schedule(_Handler(self._debouncer.add_event), str(self._path), recursive=True)
        self._observer.start()

    def stop_join(self):
        self._observer.stop()
        self._observer.join()


class _Handler(FileSystemEventHandler):

    def __init__(self, callback: Callable[[FileSystemEvent], None]):
        super().__init__()
        self._callback = callback

    def on_any_event(self, event: FileSystemEvent) -> None:
        self._callback(event)


