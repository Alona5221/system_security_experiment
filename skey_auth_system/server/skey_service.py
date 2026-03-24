"""S/Key hash-chain verification service."""

from __future__ import annotations

from common.utils import sha256_hex


class SKeyService:
    """S/Key helper service used by server-side auth."""

    @staticmethod
    def verify_otp(submitted_otp: str, current_hash: str) -> bool:
        """Verify OTP by checking H(submitted_otp) == stored current_hash."""
        return sha256_hex(submitted_otp) == current_hash
