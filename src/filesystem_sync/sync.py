from pathlib import Path
from typing import List, Any

from watchdog.events import FileSystemEvent


def sync_source(source: Path, events: List[FileSystemEvent]) -> Any:
    return None


def sync_target(target: Path, events: Any) -> None:
    return None


def sync_init(source: Path) -> Any:
    return None
