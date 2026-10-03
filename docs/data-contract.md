# Re:Learn data contract and audit gate

Every record contains `question`, `learner_code`, `reference_behavior`,
`executable_test`, `source_outcome`, `source_error`, `provenance`,
`learner_id`, `problem_id`, `misconception_labels`, and `label_confidence`.
Missing source observations are null, never invented.

`source_outcome` and `source_error` describe source observations. They are not
conceptual-misconception ground truth: a compile failure can be a syntax
error, environment issue, or many different misconceptions.

Labels are tiered: `curated` means expert-reviewed under a versioned rubric;
`deterministic_reference_transform` means a conservative AST transformation
paired with executable reference/test behavior and still requiring audit; and
`weak` means a documented heuristic/source annotation requiring audit. Each
label stores name, source, confidence, status, and rubric version.

Custom examples require a named misconception, executable test/reference
behavior, provenance, and successful duplicate/split checks.

