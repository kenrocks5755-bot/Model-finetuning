"""Validation checks used before a dataset can be handed to training."""
from __future__ import annotations

import re
import hashlib
from collections import Counter
from typing import Any

from .privacy import IP_RE, EMAIL_RE
from .split import group_key
from .executable import executable_preflight


REQUIRED = {"question", "learner_code", "reference_behavior", "source_outcome", "source_error", "executable_test", "provenance", "label_confidence", "misconception_labels"}


def validate(records: list[dict[str, Any]], require_all_splits: bool = True) -> dict[str, Any]:
    errors: list[str] = []
    groups: dict[str, str] = {}
    fingerprints: dict[str, str] = {}
    for i, record in enumerate(records):
        missing = REQUIRED - record.keys()
        if missing:
            errors.append(f"record {i}: missing {sorted(missing)}")
        for field in ("question", "learner_code", "reference_behavior", "source_outcome", "source_error", "executable_test"):
            value = record.get(field)
            if value and (IP_RE.search(str(value)) or EMAIL_RE.search(str(value))):
                errors.append(f"record {i}: unscreened PII in {field}")
        if "split" in record:
            key = group_key(record)
            prior = groups.setdefault(key, record["split"])
            if prior != record["split"]:
                errors.append(f"record {i}: group crosses split boundary")
            normalized = " ".join(" ".join(str(record.get(k) or "").lower().split()) for k in ("question", "learner_code"))
            fingerprint = hashlib.sha256(normalized.encode()).hexdigest()
            previous = fingerprints.setdefault(fingerprint, record["split"])
            if previous != record["split"]:
                errors.append(f"record {i}: near-duplicate crosses split boundary")
        for holdout in ("unseen_problem_holdout", "unseen_learner_holdout"):
            if holdout in record and record[holdout] not in {"train", "validation", "test"}:
                errors.append(f"record {i}: invalid {holdout}")
        for label in record.get("misconception_labels", []):
            if not all(label.get(k) for k in ("name", "source", "confidence", "status")):
                errors.append(f"record {i}: incomplete misconception label")
    by_source = Counter(r.get("provenance", {}).get("dataset") for r in records)
    by_confidence = Counter("unlabelled" if r.get("label_confidence") is None else str(r.get("label_confidence")) for r in records)
    labels = Counter(label.get("name") for r in records for label in r.get("misconception_labels", []))
    executable = Counter("ready" if executable_preflight(r)["ready"] else "missing_or_invalid" for r in records)
    splits = Counter(r.get("split") for r in records)
    missing_splits = {"train", "validation", "test"} - set(splits)
    if require_all_splits and missing_splits:
        errors.append(f"missing leakage-safe split(s): {sorted(missing_splits)}")
    return {"records": len(records), "splits": dict(splits), "problem_holdout": dict(Counter(r.get("unseen_problem_holdout") for r in records if r.get("unseen_problem_holdout"))), "learner_holdout": dict(Counter(r.get("unseen_learner_holdout") for r in records if r.get("unseen_learner_holdout"))), "by_source": dict(by_source), "by_confidence": dict(by_confidence), "label_balance": dict(labels), "executable_tests": dict(executable), "errors": errors, "ok": not errors}
