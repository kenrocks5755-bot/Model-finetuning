"""Safe preflight checks for reference/test fields.

This performs syntax-only checks. Executing third-party student code requires
an isolated sandbox and is deliberately a separate, offline audit step.
"""
from __future__ import annotations

import ast
from typing import Any


def executable_preflight(record: dict[str, Any]) -> dict[str, Any]:
    result = {"has_reference": bool(record.get("reference_behavior")), "has_test": bool(record.get("executable_test")), "reference_parses": False, "test_parses": False}
    for field, key in (("reference_behavior", "reference_parses"), ("executable_test", "test_parses")):
        if record.get(field):
            try:
                ast.parse(str(record[field]))
                result[key] = True
            except SyntaxError:
                result[key] = False
    result["ready"] = result["has_reference"] and result["has_test"] and result["reference_parses"] and result["test_parses"]
    return result

