"""Deterministic learner/problem-group split to prevent evaluation leakage."""
from __future__ import annotations

import hashlib
from collections import Counter
from typing import Any


def group_key(record: dict[str, Any]) -> str:
    learner = record.get("learner_id") or "unknown_learner"
    problem = record.get("problem_id") or hashlib.sha256(record["question"].encode()).hexdigest()[:16]
    return f"{learner}\0{problem}"


def assign_split(record: dict[str, Any], seed: int = 20261004) -> str:
    digest = hashlib.sha256(f"{seed}\0{group_key(record)}".encode()).digest()[0] / 255
    return "train" if digest < 0.8 else "validation" if digest < 0.9 else "test"


def assign_group_split(value: str, seed: int = 20261004) -> str:
    digest = hashlib.sha256(f"{seed}\0{value}".encode()).digest()[0] / 255
    return "train" if digest < 0.8 else "validation" if digest < 0.9 else "test"


def split_records(records: list[dict[str, Any]], seed: int = 20261004) -> tuple[list[dict[str, Any]], Counter[str]]:
    counts: Counter[str] = Counter()
    output = []
    seen_groups: dict[str, str] = {}
    for record in records:
        group = group_key(record)
        split = seen_groups.setdefault(group, assign_split(record, seed))
        copy = dict(record)
        copy["split"] = split
        if record.get("problem_id"):
            copy["unseen_problem_holdout"] = assign_group_split(str(record["problem_id"]), seed + 11)
        if record.get("learner_id"):
            copy["unseen_learner_holdout"] = assign_group_split(str(record["learner_id"]), seed + 23)
        output.append(copy)
        counts[split] += 1
    return output, counts
