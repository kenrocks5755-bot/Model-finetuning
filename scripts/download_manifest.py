#!/usr/bin/env python3
"""Download pinned public source archives without putting them in Git."""
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("manifest", type=Path, help="JSON manifest with a published sha256 or md5 checksum")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    parser.add_argument("--dataset", help="download only entries with this dataset field")
    args = parser.parse_args()
    entries = json.loads(args.manifest.read_text())
    if args.dataset:
        entries = [entry for entry in entries if entry.get("dataset") == args.dataset]
        if not entries:
            raise SystemExit(f"No manifest entries for dataset {args.dataset!r}")
    lock = []
    for entry in entries:
        target = args.output_dir / entry["filename"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(entry["url"]) as source, target.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        with target.open("rb") as downloaded:
            while chunk := downloaded.read(1024 * 1024):
                sha256.update(chunk)
                md5.update(chunk)
        expected_sha256, expected_md5 = entry.get("sha256"), entry.get("md5")
        if not expected_sha256 and not expected_md5:
            raise SystemExit(f"{entry['name']} has no publisher checksum")
        if (expected_sha256 and sha256.hexdigest() != expected_sha256) or (expected_md5 and md5.hexdigest() != expected_md5):
            target.unlink(missing_ok=True)
            raise SystemExit(f"checksum mismatch for {entry['name']}")
        print(f"downloaded {entry['name']} -> {target}")
        lock.append({**entry, "downloaded_filename": str(target), "verified_sha256": sha256.hexdigest(), "verified_md5": md5.hexdigest()})
    (args.output_dir / "manifest.lock.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
