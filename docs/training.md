# Kaggle training handoff

Training is intentionally not launched during cloud setup. Before requesting
GPU time, run conversion, merge, split, validation, and executable-test audit;
create audited `assistant_response` fields; and accept the
`google/gemma-3-1b-it` license on Hugging Face if gated. Configure any needed
Hugging Face access through secure environment settings.

`scripts/train_qlora.py --data ... --output ... --allow-gpu` uses 4-bit QLoRA
and assistant-response-only loss. Validate unseen-problem and, where possible,
unseen-learner holdouts using deterministic decoding. Report audited-label
macro-F1 plus response validity, executable-test pass rate,
confidence/calibration, and abstention/error rates. Merge/export adapters only
after validation in a private artifact store.

Use `scripts/metrics.py` for response non-emptiness, provenance coverage, and
reference exact-match reporting. Use
`scripts/merge_adapter.py --adapter ... --output ... --allow-gpu` only after
the holdout report is approved.
