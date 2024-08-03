from pathlib import Path
from typing import List, Any, Protocol

from watchdog.events import FileSystemEvent


class Sync(Protocol):

    @staticmethod
    def sync_source(source: Path, events: List[FileSystemEvent]) -> List[Any]:
        pass

    @staticmethod
    def sync_target(target: Path, changes: List[Any]) -> None:
        pass

    @staticmethod
    def sync_init(source: Path) -> List[Any]:
        pass
