#!/usr/bin/env python3
"""Compute lightweight, label-agnostic generation metrics."""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("predictions", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    rows = [json.loads(line) for line in args.predictions.read_text().splitlines() if line.strip()]
    nonempty = [row for row in rows if row.get("prediction", "").strip()]
    exact = [row for row in rows if row.get("reference_behavior") and re.sub(r"\s+", " ", row["prediction"].strip()) == re.sub(r"\s+", " ", row["reference_behavior"].strip())]
    metrics = {"records": len(rows), "nonempty_response_rate": len(nonempty) / len(rows) if rows else 0.0, "reference_exact_match_rate": len(exact) / len(rows) if rows else None, "provenance_coverage": sum(bool(row.get("provenance")) for row in rows) / len(rows) if rows else 0.0}
    args.output.write_text(json.dumps(metrics, indent=2, sort_keys=True) + "\n")
    print(json.dumps(metrics, sort_keys=True))


if __name__ == "__main__":
    main()

