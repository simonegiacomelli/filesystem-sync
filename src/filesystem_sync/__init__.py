import tempfile
from pathlib import Path
from typing import List

from watchdog.events import FileSystemEvent


def new_tmp_path() -> Path:
    return Path(tempfile.mkdtemp(prefix='debounce-tmp-path-'))


def filesystemevents_print(events: List[FileSystemEvent]):
    for e in events:
        print(f'  {e}')
    print(f'len events={len(events)}')
