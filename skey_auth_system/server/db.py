"""Database access layer for server side."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional

from common.utils import now_iso
from server.models import CAPTCHA_TABLE_SQL, LOGIN_LOGS_TABLE_SQL, USERS_TABLE_SQL


class Database:
    """SQLite database wrapper with domain-specific CRUD helpers."""

    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    def _conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, check_same_thread=False)
        conn.row_factory = sqlite3.Row
        return conn

    def init_tables(self) -> None:
        """Create required tables if absent."""
        with self._conn() as conn:
            conn.execute(USERS_TABLE_SQL)
            conn.execute(CAPTCHA_TABLE_SQL)
            conn.execute(LOGIN_LOGS_TABLE_SQL)
            conn.commit()

    def create_user(self, username: str, seed: str, chain_length: int, chain_tail: str) -> None:
        """Insert a new user with initial S/Key chain state."""
        ts = now_iso()
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO users (username, seed, chain_length, current_index, current_hash, created_at, updated_at, status)
                VALUES (?, ?, ?, ?, ?, ?, ?, 'active')
                """,
                (username, seed, chain_length, chain_length, chain_tail, ts, ts),
            )
            conn.commit()

    def get_user(self, username: str) -> Optional[Dict[str, Any]]:
        """Get a user by username."""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
            return dict(row) if row else None

    def update_user_chain(self, username: str, seed: str, chain_length: int, current_hash: str, current_index: int) -> None:
        """Reset user chain data (used during renegotiation)."""
        with self._conn() as conn:
            conn.execute(
                """
                UPDATE users
                SET seed=?, chain_length=?, current_index=?, current_hash=?, updated_at=?
                WHERE username=?
                """,
                (seed, chain_length, current_index, current_hash, now_iso(), username),
            )
            conn.commit()

    def consume_otp(self, username: str, submitted_otp: str, next_index: int) -> None:
        """Advance chain state after successful OTP verification."""
        with self._conn() as conn:
            conn.execute(
                "UPDATE users SET current_hash=?, current_index=?, updated_at=? WHERE username=?",
                (submitted_otp, next_index, now_iso(), username),
            )
            conn.commit()

    def create_captcha(self, username: str, captcha_id: str, captcha_code: str, created_at: str, expires_at: str) -> None:
        """Persist captcha challenge."""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO captcha_records (username, captcha_id, captcha_code, created_at, expires_at, used)
                VALUES (?, ?, ?, ?, ?, 0)
                """,
                (username, captcha_id, captcha_code, created_at, expires_at),
            )
            conn.commit()

    def get_captcha(self, captcha_id: str):
        """Fetch captcha record by id."""
        with self._conn() as conn:
            row = conn.execute("SELECT * FROM captcha_records WHERE captcha_id=?", (captcha_id,)).fetchone()
            return dict(row) if row else None

    def mark_captcha_used(self, captcha_id: str) -> None:
        """Mark captcha as used once validation is successful."""
        with self._conn() as conn:
            conn.execute("UPDATE captcha_records SET used=1 WHERE captcha_id=?", (captcha_id,))
            conn.commit()

    def insert_login_log(
        self,
        username: str,
        client_ip: str,
        action: str,
        result: str,
        reason: str,
        seq_no: Optional[int],
        detail: str,
    ) -> None:
        """Insert one audit log row."""
        with self._conn() as conn:
            conn.execute(
                """
                INSERT INTO login_logs (username, client_ip, action, result, reason, seq_no, detail, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (username, client_ip, action, result, reason, seq_no, detail, now_iso()),
            )
            conn.commit()

    def query_logs(self, username: str = "", result: str = "", limit: int = 100) -> List[Dict[str, Any]]:
        """Query logs with simple filters, sorted by newest first."""
        conditions = []
        params: list[Any] = []
        if username:
            conditions.append("username = ?")
            params.append(username)
        if result:
            conditions.append("result = ?")
            params.append(result)

        where_sql = " WHERE " + " AND ".join(conditions) if conditions else ""
        sql = f"SELECT * FROM login_logs{where_sql} ORDER BY created_at DESC, id DESC LIMIT ?"
        params.append(limit)

        with self._conn() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
            return [dict(row) for row in rows]
