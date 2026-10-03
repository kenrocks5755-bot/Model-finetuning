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
    parser.add_argument("manifest", type=Path, help="private JSON manifest of {name,url,sha256,filename}")
    parser.add_argument("--output-dir", type=Path, default=Path("data/raw"))
    args = parser.parse_args()
    entries = json.loads(args.manifest.read_text())
    lock = []
    for entry in entries:
        target = args.output_dir / entry["filename"]
        target.parent.mkdir(parents=True, exist_ok=True)
        with urllib.request.urlopen(entry["url"]) as source, target.open("wb") as destination:
            while chunk := source.read(1024 * 1024):
                destination.write(chunk)
        digest = hashlib.sha256(target.read_bytes()).hexdigest()
        if digest != entry["sha256"]:
            target.unlink(missing_ok=True)
            raise SystemExit(f"checksum mismatch for {entry['name']}: expected {entry['sha256']}, got {digest}")
        print(f"downloaded {entry['name']} -> {target}")
        lock.append({**entry, "downloaded_filename": str(target), "verified_sha256": digest})
    (args.output_dir / "manifest.lock.json").write_text(json.dumps(lock, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
