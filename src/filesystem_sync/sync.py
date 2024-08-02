from pathlib import Path
from typing import List, Any

from watchdog.events import FileSystemEvent


def sync_source(source: Path, events: List[FileSystemEvent]) -> List[Any]:
    result = []
    for e in events:
        if not e.is_directory and e.event_type == 'modified':
            src = Path(e.src_path)
            name = src.relative_to(source)
            # avoid race conditions where the file is deleted before we can read it
            result.append({'name': str(name), 'content': src.read_text()})
    return result


def sync_target(target: Path, changes: List[Any]) -> None:
    for change in changes:
        name = target / change['name']
        name.write_text(change['content'])


def sync_init(source: Path) -> Any:
    return None
