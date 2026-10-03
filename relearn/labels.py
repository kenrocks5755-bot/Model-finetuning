"""Conservative misconception-label helpers.

Only emit weak labels when a named transformation and executable reference/test
are available. Never infer a misconception from a verdict or error string.
"""
from __future__ import annotations

import ast
from typing import Any


def deterministic_transform_labels(record: dict[str, Any], rubric_version: str = "2026-10") -> list[dict[str, Any]]:
    if not record.get("reference_behavior") or not record.get("executable_test"):
        return []
    try:
        learner_tree = ast.parse(record["learner_code"])
        reference_tree = ast.parse(record["reference_behavior"])
    except (SyntaxError, TypeError):
        return []
    learner_nodes, reference_nodes = list(ast.walk(learner_tree)), list(ast.walk(reference_tree))
    names: set[str] = set()
    learner_ranges = any(isinstance(n, ast.For) and isinstance(n.iter, ast.Call) and getattr(n.iter.func, "id", None) == "range" for n in learner_nodes)
    reference_ranges = any(isinstance(n, ast.For) and isinstance(n.iter, ast.Call) and getattr(n.iter.func, "id", None) == "range" for n in reference_nodes)
    if learner_ranges and not reference_ranges:
        names.add("range-boundary-error")
    if any(isinstance(n, ast.FunctionDef) and n.args.defaults for n in learner_nodes):
        names.add("mutable-default-argument")
    return [{"name": name, "source": "deterministic_reference_transform", "confidence": 0.65, "status": "weak_requires_audit", "rubric_version": rubric_version} for name in sorted(names)]

