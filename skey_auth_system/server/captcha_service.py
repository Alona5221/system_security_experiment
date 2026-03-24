"""Captcha generation and validation."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import secrets

from common.utils import now_iso


class CaptchaService:
    """Simple string captcha service for experiment usage."""

    def __init__(self, expire_seconds: int = 60) -> None:
        self.expire_seconds = expire_seconds

    def create(self) -> tuple[str, str, str, str]:
        """Generate captcha_id, code, created_at, expires_at."""
        captcha_id = secrets.token_hex(16)
        code = "".join(secrets.choice("ABCDEFGHJKLMNPQRSTUVWXYZ23456789") for _ in range(6))
        created_at = now_iso()
        expires_at = (
            datetime.now(timezone.utc).replace(microsecond=0) + timedelta(seconds=self.expire_seconds)
        ).isoformat()
        return captcha_id, code, created_at, expires_at

    @staticmethod
    def is_expired(expires_at_iso: str) -> bool:
        """Return True if the captcha has expired."""
        expires_at = datetime.fromisoformat(expires_at_iso)
        return datetime.now(timezone.utc) > expires_at
