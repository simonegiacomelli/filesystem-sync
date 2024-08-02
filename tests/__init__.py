import tempfile
from pathlib import Path


def new_tmp_path() -> Path:
    return Path(tempfile.mkdtemp(prefix='debounce-harness'))
