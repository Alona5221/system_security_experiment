"""Common helper utilities."""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone


def now_iso() -> str:
    """Return current UTC time in ISO-8601 format."""
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def sha256_hex(text: str) -> str:
    """Return lowercase hex sha256 digest for the input string."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def is_hex_sha256(value: str) -> bool:
    """Check whether input is a valid SHA-256 hex digest."""
    if not isinstance(value, str) or len(value) != 64:
        return False
    return all(c in "0123456789abcdef" for c in value)
