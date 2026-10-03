# Re:Learn model fine-tuning

This repository contains the data-preparation, training, and evaluation workflow for Re:Learn: a Python-programming tutor that diagnoses learner misconceptions and provides targeted interventions.

Initial Cloud setup is used to prepare secure Kaggle-based fine-tuning workflows. Credentials must be supplied through secure environment configuration and must never be committed to this repository.

## Non-GPU data contract and pipeline

The pipeline consumes pinned, licensed local exports of CircleCat/PyMETA and
the Dublin student-programming submission corpus hosted on Figshare. Raw
archives and derived records belong in `data/raw/`, `data/intermediate/`, and
`data/derived/`; those paths are ignored by Git. Download is intentionally
manifest-driven: the manifest must record the public landing page, direct file
URL, license/attribution, retrieval date, filename, and SHA-256 checksum. The
download helper refuses checksum mismatches.

```bash
python scripts/download_manifest.py /secure/path/sources.json
python -m relearn.cli convert data/raw/pymeta.jsonl data/intermediate/pymeta.jsonl --source pymeta
python -m relearn.cli convert data/raw/dublin.jsonl data/intermediate/dublin.jsonl --source dublin
python -m relearn.cli merge data/intermediate/pymeta.jsonl data/intermediate/dublin.jsonl --output data/derived/combined.jsonl
python -m relearn.cli deduplicate data/derived/combined.jsonl data/derived/deduplicated.jsonl
python -m relearn.cli split data/derived/deduplicated.jsonl data/derived/split.jsonl
python -m relearn.cli validate data/derived/split.jsonl
```

`configs/verified_sources.json` pins the current verified primary-source
metadata: PyMETA's revision and SHA-256 objects plus Dublin's publisher MD5.
The downloader writes a
checksum-verified `manifest.lock.json` beside the private raw files so
attribution and license metadata travel with the downloaded source.

The canonical record has `question`, `learner_code`,
`reference_behavior`, `source_outcome`, `source_error`, `executable_test`,
`provenance`, `learner_id`, `problem_id`, `misconception_labels`, and
`label_confidence`. Source verdicts, compile/runtime errors, and autograder
outcomes remain observations; they are never conceptual-misconception
ground truth. Concept labels must be curated, deterministically transformed
from reference code plus executable tests, or marked as weak labels requiring
human audit. Each label stores its named misconception, source, confidence,
status, and rubric/version.

Conversion removes IP addresses, emails, URLs, and long direct identifiers;
learner/problem IDs become private namespace hashes. Exact and normalized
near-duplicates are rejected. Deterministic learner/problem-aware splits
prevent group leakage, with separate unseen-problem and (when identifiers
permit) unseen-learner holdouts. Validation reports PII, schema, duplicate,
split, executable-test, and class-balance checks. It reports actual counts by
source and confidence; it never pads a corpus to a target size.

No raw data was downloaded in this repository because source licensing and
stable file URLs must be recorded in the private manifest first. The code is
ready to process a permitted export and will preserve attribution metadata.

## QLoRA preparation (not launched)

`scripts/train_qlora.py` targets `google/gemma-3-1b-it`, uses 4-bit QLoRA,
requires audited `assistant_response` fields, and masks prompt tokens so only
assistant responses contribute to loss. It refuses to launch without an
explicit `--allow-gpu`. `scripts/evaluate_qlora.py` provides deterministic
inference and writes prediction/provenance records; checkpoint validation and
adapter merge/export are documented in `docs/training.md`. Access to the
Gemma checkpoint may require accepting its Hugging Face license and supplying
Hugging Face authentication in secure environment settings. No GPU training,
Kaggle upload, model binary, dataset, or credential is committed.
