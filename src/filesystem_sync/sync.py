from pathlib import Path
from typing import List, Any

from watchdog.events import FileSystemEvent


def sync_source(source: Path, events: List[FileSystemEvent]) -> List[Any]:
    result = []
    state = {}
    for e in events:
        if not e.is_directory:
            src = Path(e.src_path)
            name = str(src.relative_to(source))
            prev = state.get(name, None)
            if e.event_type == 'created':
                state[name] = 'modified'
            if e.event_type == 'modified':
                state[name] = state.get(name, 'modified')  # if it was created, it stays created
            elif e.event_type == 'deleted':
                if prev == 'modified':
                    del state[name]
                else:
                    state[name] = 'deleted'

    for name, status in state.items():
        path = source / name
        if status == 'deleted':
            result.append({'name': str(name), 'content': None})
        elif status == 'modified':
            try:
                result.append({'name': str(name), 'content': path.read_text()})
            except Exception as e:
                pass
    return result


def sync_target(target_root: Path, changes: List[Any]) -> None:
    for change in changes:
        target = target_root / change['name']
        content = change['content']
        if content is None:
            target.unlink(missing_ok=True)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)


from pathlib import Path
from typing import List, Any


def sync_init(source: Path) -> List[Any]:
    result = []
    for path in source.rglob('*'):
        if path.is_file():
            result.append({'name': str(path.relative_to(source)), 'content': path.read_text()})
    return result
