from __future__ import annotations

import hashlib
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path

import yaml

ROOT = Path(os.environ.get("CAMPUSQA_ROOT", Path(__file__).resolve().parents[1])).resolve()
os.environ.setdefault("HF_HOME", str(ROOT / ".cache" / "huggingface"))
os.environ.setdefault("TOKENIZERS_PARALLELISM", "false")
os.environ.setdefault("ANONYMIZED_TELEMETRY", "False")


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def config(name: str) -> dict:
    return yaml.safe_load((ROOT / "config" / f"{name}.yaml").read_text(encoding="utf-8"))


def model_directory() -> Path:
    selected = config('model_config')
    key = selected.get('artifact_name') or selected['model_id'].split('/')[-1].removesuffix('-Instruct').lower()
    if not re.fullmatch(r'[a-z0-9][a-z0-9.-]*',key):
        raise ValueError('Invalid model artifact directory name')
    return ROOT/'models'/key


def digest(value) -> str:
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def write_json(path: Path, value, *, exclusive: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    # Preserve the original Windows study's canonical bytes on every platform.
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\r\n") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2)


def read_json(path: Path, default=None):
    return json.loads(path.read_text(encoding="utf-8")) if path.exists() else default


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as stream:
        return [json.loads(line) for line in stream if line.strip()]


def write_jsonl(path: Path, rows, *, exclusive: bool = False):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x" if exclusive else "w", encoding="utf-8", newline="\r\n") as stream:
        for row in rows:
            stream.write(json.dumps(row, ensure_ascii=False) + "\n")
