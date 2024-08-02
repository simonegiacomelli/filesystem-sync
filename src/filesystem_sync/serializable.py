from typing import List, NamedTuple

from watchdog.events import FileSystemEvent


class FilesystemSyncEvent(NamedTuple):
    dest_path: str
    event_type: str
    is_directory: bool
    src_path: str
    is_synthetic: bool


def serializable_event(event: FileSystemEvent) -> FilesystemSyncEvent:
    return FilesystemSyncEvent(
        dest_path=str(event.dest_path),
        event_type=event.event_type,
        is_directory=event.is_directory,
        src_path=str(event.src_path),
        is_synthetic=event.is_synthetic
    )


def serializable_events(events: List[FileSystemEvent]) -> List[FilesystemSyncEvent]:
    return [serializable_event(event) for event in events]
