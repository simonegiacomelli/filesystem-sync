from pathlib import Path
from typing import List, Any

from watchdog.events import FileSystemEvent


def sync_source(source: Path, events: List[FileSystemEvent]) -> List[Any]:
    result = []
    state = {}
    for e in events:
        if not e.is_directory and e.event_type == 'modified':
            src = Path(e.src_path)
            name = str(src.relative_to(source))
            state[name] = 'modified'
    for name, status in state.items():
        path = source / name
        try:
            result.append({'name': str(name), 'content': path.read_text()})
        except Exception as e:
            pass
    return result


def sync_target(target: Path, changes: List[Any]) -> None:
    for change in changes:
        name = target / change['name']
        name.write_text(change['content'])


def sync_init(source: Path) -> Any:
    return None
