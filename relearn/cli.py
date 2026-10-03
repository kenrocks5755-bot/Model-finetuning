"""Command line entry point for CPU-only data preparation."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .convert import convert_file, deduplicate_records
from .io import read_records, write_jsonl
from .split import split_records
from .validate import validate


def main() -> None:
    parser = argparse.ArgumentParser(description="Re:Learn private dataset preparation")
    sub = parser.add_subparsers(dest="command", required=True)
    convert = sub.add_parser("convert")
    convert.add_argument("input", type=Path)
    convert.add_argument("output", type=Path)
    convert.add_argument("--source", required=True, choices=["pymeta", "dublin"])
    split = sub.add_parser("split")
    split.add_argument("input", type=Path)
    split.add_argument("output", type=Path)
    split.add_argument("--seed", type=int, default=20261004)
    merge = sub.add_parser("merge")
    merge.add_argument("inputs", type=Path, nargs="+")
    merge.add_argument("--output", type=Path, required=True)
    deduplicate = sub.add_parser("deduplicate")
    deduplicate.add_argument("input", type=Path)
    deduplicate.add_argument("output", type=Path)
    check = sub.add_parser("validate")
    check.add_argument("input", type=Path)
    args = parser.parse_args()
    if args.command == "convert":
        print(json.dumps(convert_file(args.input, args.output, args.source), sort_keys=True))
    elif args.command == "merge":
        def rows():
            for path in args.inputs:
                yield from read_records(path)
        print(json.dumps({"records": write_jsonl(args.output, rows())}, sort_keys=True))
    elif args.command == "deduplicate":
        print(json.dumps({"records": write_jsonl(args.output, deduplicate_records(read_records(args.input)))}, sort_keys=True))
    elif args.command == "split":
        records = list(read_records(args.input))
        values, counts = split_records(records, args.seed)
        write_jsonl(args.output, iter(values))
        print(json.dumps(dict(counts), sort_keys=True))
    else:
        result = validate(list(read_records(args.input)))
        print(json.dumps(result, indent=2, sort_keys=True))
        raise SystemExit(0 if result["ok"] else 1)


if __name__ == "__main__":
    main()
