import hashlib
from pathlib import Path


def tree_fingerprint(path: Path):
    """Hash artifact filenames and bytes without depending on filesystem ordering."""
    result = hashlib.sha256()
    for file in sorted(path.rglob("*")):
        if file.is_file() and file.name not in {"training_manifest.json", "current.json"}:
            result.update(file.relative_to(path).as_posix().encode())
            with file.open("rb") as stream:
                for chunk in iter(lambda: stream.read(1024*1024), b""):
                    result.update(chunk)
    return result.hexdigest()
