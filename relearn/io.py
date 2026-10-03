"""Streaming JSON/JSONL/CSV input and JSONL output with no extra dependency."""
from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, Iterator


def read_records(path: Path) -> Iterator[dict[str, Any]]:
    suffix = path.name.lower()
    if suffix.endswith(".jsonl") or suffix.endswith(".jsonl.gz"):
        import gzip
        opener = gzip.open if suffix.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as handle:
            for line_number, line in enumerate(handle, 1):
                if line.strip():
                    value = json.loads(line)
                    if not isinstance(value, dict):
                        raise ValueError(f"{path}:{line_number} is not an object")
                    yield value
    elif suffix.endswith(".csv"):
        with path.open(newline="", encoding="utf-8-sig") as handle:
            yield from csv.DictReader(handle)
    elif suffix.endswith(".json"):
        value = json.loads(path.read_text(encoding="utf-8"))
        values = value if isinstance(value, list) else value.get("records", value.get("data", []))
        if not isinstance(values, list):
            raise ValueError(f"{path}: expected a list or records/data list")
        yield from values
    else:
        raise ValueError(f"Unsupported input format: {path}")


def write_jsonl(path: Path, records: Iterator[dict[str, Any]]) -> int:
    path.parent.mkdir(parents=True, exist_ok=True)
    count = 0
    with path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            count += 1
    return count

