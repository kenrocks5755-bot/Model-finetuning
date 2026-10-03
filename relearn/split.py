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
    """Split connected learner/problem/template components, not isolated rows.

    A component links rows sharing a learner, a problem, or a normalized
    question/code template. This prevents both learner/problem and exact
    near-duplicate leakage across the main split.
    """
    parent = list(range(len(records)))

    def find(value: int) -> int:
        while parent[value] != value:
            parent[value] = parent[parent[value]]
            value = parent[value]
        return value

    def union(left: int, right: int) -> None:
        left, right = find(left), find(right)
        if left != right:
            parent[right] = left

    seen: dict[str, int] = {}
    for index, record in enumerate(records):
        normalized = " ".join(" ".join(str(record.get(k) or "").lower().split()) for k in ("question", "learner_code"))
        keys = [f"template:{hashlib.sha256(normalized.encode()).hexdigest()}"]
        if record.get("learner_id"):
            keys.append(f"learner:{record['learner_id']}")
        if record.get("problem_id"):
            keys.append(f"problem:{record['problem_id']}")
        for key in keys:
            if key in seen:
                union(index, seen[key])
            else:
                seen[key] = index

    counts: Counter[str] = Counter()
    output = []
    components: dict[int, str] = {}
    for index, record in enumerate(records):
        root = find(index)
        split = components.setdefault(root, assign_group_split(f"component:{root}", seed))
        copy = dict(record)
        copy["split"] = split
        if record.get("problem_id"):
            copy["unseen_problem_holdout"] = assign_group_split(str(record["problem_id"]), seed + 11)
        if record.get("learner_id"):
            copy["unseen_learner_holdout"] = assign_group_split(str(record["learner_id"]), seed + 23)
        output.append(copy)
        counts[split] += 1
    return output, counts
