"""Canonical record schema and source-field normalization.

Source verdicts/errors are deliberately retained as observations. They are not
misconception labels; a later audited labelling stage must create those labels.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class RelearnRecord:
    question: str
    learner_code: str
    reference_behavior: str | None
    source_outcome: str | None
    source_error: str | None
    executable_test: str | None
    provenance: dict[str, Any]
    label_confidence: float | None
    misconception_labels: list[dict[str, Any]]
    learner_id: str | None = None
    problem_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


FIELD_ALIASES: dict[str, tuple[str, ...]] = {
    "question": ("question", "prompt", "problem", "problem_statement", "description", "task"),
    "learner_code": ("learner_code", "code", "submission", "source_code", "program", "answer"),
    "reference_behavior": ("reference_behavior", "expected", "expected_output", "reference", "solution", "test_oracle"),
    "source_outcome": ("source_outcome", "outcome", "verdict", "result", "status", "label"),
    "source_error": ("source_error", "error", "error_message", "stderr", "exception", "feedback"),
    "executable_test": ("executable_test", "tests", "test_code", "unit_test", "oracle_code"),
    "learner_id": ("learner_id", "student_id", "user_id", "author_id", "user", "student"),
    "problem_id": ("problem_id", "task_id", "exercise_id", "question_id", "problem", "challenge_id"),
}


def first_value(row: dict[str, Any], names: tuple[str, ...]) -> Any:
    lowered = {str(k).lower(): v for k, v in row.items()}
    for name in names:
        value = lowered.get(name)
        if value is not None and str(value).strip() != "":
            return value
    return None
