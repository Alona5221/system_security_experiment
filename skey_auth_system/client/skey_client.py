"""S/Key client-side chain generation logic."""

from __future__ import annotations

import secrets

from common.utils import sha256_hex


class SKeyClient:
    """Generate S/Key chain values locally from password + seed."""

    @staticmethod
    def generate_seed() -> str:
        """Generate random seed string."""
        return secrets.token_hex(8)

    @staticmethod
    def compute_x0(password: str, seed: str) -> str:
        """Compute x0 = H(password:seed)."""
        return sha256_hex(f"{password}:{seed}")

    @staticmethod
    def compute_chain_tail(password: str, seed: str, chain_length: int) -> str:
        """Compute xN by iterating hash from x0 for N times."""
        value = SKeyClient.compute_x0(password, seed)
        for _ in range(chain_length):
            value = sha256_hex(value)
        return value

    @staticmethod
    def compute_otp(password: str, seed: str, current_index: int) -> str:
        """Compute x_(current_index - 1) for current server index."""
        if current_index <= 0:
            raise ValueError("current_index must be > 0")

        value = SKeyClient.compute_x0(password, seed)
        for _ in range(current_index - 1):
            value = sha256_hex(value)
        return value
