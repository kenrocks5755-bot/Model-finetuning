#!/usr/bin/env python3
"""CPU/GPU-compatible generation evaluation for an adapter checkpoint."""
from __future__ import annotations

import argparse
import json
from pathlib import Path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", required=True)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--limit", type=int, default=100)
    args = parser.parse_args()
    from transformers import AutoModelForCausalLM, AutoTokenizer
    from relearn.io import read_records
    from relearn.training import make_prompt

    tokenizer = AutoTokenizer.from_pretrained(args.model)
    model = AutoModelForCausalLM.from_pretrained(args.model, device_map="auto")
    rows = []
    for record in list(read_records(args.data))[: args.limit]:
        inputs = tokenizer(make_prompt(record), return_tensors="pt").to(model.device)
        generated = model.generate(**inputs, max_new_tokens=256, do_sample=False)
        answer = tokenizer.decode(generated[0][inputs.input_ids.shape[1]:], skip_special_tokens=True)
        rows.append({"provenance": record.get("provenance"), "prediction": answer, "reference_behavior": record.get("reference_behavior")})
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(json.dumps(row, ensure_ascii=False) for row in rows) + "\n")


if __name__ == "__main__":
    main()

