"""PII minimization for public educational code corpora."""
from __future__ import annotations

import hashlib
import re

IP_RE = re.compile(r"(?<![\w.])(?:\d{1,3}\.){3}\d{1,3}(?![\w.])")
EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
URL_RE = re.compile(r"https?://[^\s)\]>]+", re.I)
LONG_ID_RE = re.compile(r"\b[A-Za-z0-9_-]{24,}\b")


def scrub_text(value: str | None) -> str | None:
    if value is None:
        return None
    value = IP_RE.sub("<IP_REDACTED>", str(value))
    value = EMAIL_RE.sub("<EMAIL_REDACTED>", value)
    value = URL_RE.sub("<URL_REDACTED>", value)
    return LONG_ID_RE.sub("<ID_REDACTED>", value)


def stable_private_id(value: object, namespace: str) -> str | None:
    if value is None or str(value).strip() == "":
        return None
    digest = hashlib.sha256(f"{namespace}\0{value}".encode()).hexdigest()[:20]
    return f"{namespace}_{digest}"

