"""Convert PyMETA and Dublin-style exports to the canonical private schema."""
from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any, Iterator

from .io import read_records, write_jsonl
from .privacy import scrub_text, stable_private_id
from .schema import FIELD_ALIASES, RelearnRecord, first_value


def _text(value: Any) -> str | None:
    if value is None:
        return None
    value = str(value).strip()
    return value or None


def normalize(row: dict[str, Any], source: str, source_file: str) -> RelearnRecord | None:
    question = _text(first_value(row, FIELD_ALIASES["question"]))
    code = _text(first_value(row, FIELD_ALIASES["learner_code"]))
    if not question or not code:
        return None
    learner_raw = first_value(row, FIELD_ALIASES["learner_id"])
    problem_raw = first_value(row, FIELD_ALIASES["problem_id"])
    clean = lambda key: scrub_text(_text(first_value(row, FIELD_ALIASES[key])))
    source_outcome = clean("source_outcome")
    record = RelearnRecord(
        question=scrub_text(question) or "",
        learner_code=scrub_text(code) or "",
        reference_behavior=clean("reference_behavior"),
        source_outcome=source_outcome,
        source_error=clean("source_error"),
        executable_test=clean("executable_test"),
        provenance={"dataset": source, "source_file": Path(source_file).name, "source_label": source_outcome},
        label_confidence=None,
        misconception_labels=[],
        learner_id=stable_private_id(learner_raw, "learner"),
        problem_id=stable_private_id(problem_raw, "problem"),
    )
    return record


def fingerprint(record: RelearnRecord) -> str:
    text = "\n".join([record.question, record.learner_code, record.reference_behavior or ""])
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def convert_file(path: Path, output: Path, source: str) -> dict[str, int]:
    seen: set[str] = set()
    stats = {"input": 0, "valid": 0, "deduplicated": 0, "output": 0}

    def records() -> Iterator[dict[str, Any]]:
        for row in read_records(path):
            stats["input"] += 1
            record = normalize(row, source, str(path))
            if record is None:
                continue
            stats["valid"] += 1
            key = fingerprint(record)
            if key in seen:
                stats["deduplicated"] += 1
                continue
            seen.add(key)
            stats["output"] += 1
            yield record.to_dict()

    write_jsonl(output, records())
    return stats


def deduplicate_records(rows: Iterator[dict[str, Any]]) -> Iterator[dict[str, Any]]:
    """Deduplicate canonical records globally, preserving the first provenance."""
    seen: set[str] = set()
    for row in rows:
        record = RelearnRecord(**row)
        key = fingerprint(record)
        if key in seen:
            continue
        seen.add(key)
        yield row
