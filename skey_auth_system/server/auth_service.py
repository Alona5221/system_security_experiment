"""Business service for register/login/renegotiation/log query."""

from __future__ import annotations

import sqlite3
from typing import Any, Dict

from common.constants import ERROR_CODES, LOG_ACTIONS
from common.protocol import build_error, build_ok
from common.utils import is_hex_sha256
from server.captcha_service import CaptchaService
from server.db import Database
from server.skey_service import SKeyService


class AuthService:
    """Core auth logic with strict S/Key + captcha verification order."""

    def __init__(self, db: Database, captcha_service: CaptchaService) -> None:
        self.db = db
        self.captcha_service = captcha_service

    def _log(
        self,
        username: str,
        client_ip: str,
        action: str,
        result: str,
        reason: str,
        seq_no: int | None,
        detail: str,
    ) -> None:
        self.db.insert_login_log(username, client_ip, action, result, reason, seq_no, detail)

    def register(self, data: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Handle register request."""
        username = str(data.get("username", "")).strip()
        seed = str(data.get("seed", "")).strip()
        chain_length = int(data.get("chain_length", 0) or 0)
        chain_tail = str(data.get("chain_tail", "")).strip().lower()

        if not username or not seed or chain_length <= 0 or not is_hex_sha256(chain_tail):
            self._log(username, client_ip, LOG_ACTIONS["REGISTER"], "fail", "invalid payload", None, "bad register data")
            return build_error("注册参数不合法", ERROR_CODES["INVALID_REQUEST"])

        if self.db.get_user(username):
            self._log(username, client_ip, LOG_ACTIONS["REGISTER"], "fail", "user exists", chain_length, "duplicate user")
            return build_error("用户已存在", ERROR_CODES["USER_EXISTS"])

        try:
            self.db.create_user(username, seed, chain_length, chain_tail)
        except sqlite3.DatabaseError:
            self._log(username, client_ip, LOG_ACTIONS["REGISTER"], "fail", "database error", None, "create user failed")
            return build_error("数据库错误", ERROR_CODES["DB_ERROR"])

        self._log(username, client_ip, LOG_ACTIONS["REGISTER"], "success", "ok", chain_length, "register success")
        return build_ok("注册成功", {"username": username, "chain_length": chain_length})

    def request_challenge(self, data: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Return current seed/index and captcha for login challenge."""
        username = str(data.get("username", "")).strip()
        user = self.db.get_user(username)
        if not user:
            self._log(username, client_ip, LOG_ACTIONS["REQUEST_CHALLENGE"], "fail", "user not found", None, "missing user")
            return build_error("用户不存在", ERROR_CODES["USER_NOT_FOUND"])

        if user["status"] != "active":
            self._log(username, client_ip, LOG_ACTIONS["REQUEST_CHALLENGE"], "fail", "user disabled", user["current_index"], "status inactive")
            return build_error("用户不可用", ERROR_CODES["USER_DISABLED"])

        captcha_id, captcha_code, created_at, expires_at = self.captcha_service.create()
        try:
            self.db.create_captcha(username, captcha_id, captcha_code, created_at, expires_at)
        except sqlite3.DatabaseError:
            self._log(username, client_ip, LOG_ACTIONS["REQUEST_CHALLENGE"], "fail", "database error", user["current_index"], "create captcha failed")
            return build_error("数据库错误", ERROR_CODES["DB_ERROR"])

        self._log(username, client_ip, LOG_ACTIONS["REQUEST_CHALLENGE"], "success", "ok", user["current_index"], "challenge issued")
        return build_ok(
            "挑战获取成功",
            {
                "username": username,
                "seed": user["seed"],
                "current_index": user["current_index"],
                "captcha_id": captcha_id,
                "captcha_code": captcha_code,
                "expires_in": self.captcha_service.expire_seconds,
            },
        )

    def login(self, data: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Handle login request with required strict verification order."""
        username = str(data.get("username", "")).strip()
        captcha_id = str(data.get("captcha_id", "")).strip()
        captcha_input = str(data.get("captcha_input", "")).strip().upper()
        otp = str(data.get("otp", "")).strip().lower()

        # 1) user exists
        user = self.db.get_user(username)
        if not user:
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "user not found", None, "login denied")
            return build_error("用户不存在", ERROR_CODES["USER_NOT_FOUND"])

        # 2) user active
        if user["status"] != "active":
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "user disabled", user["current_index"], "login denied")
            return build_error("用户不可用", ERROR_CODES["USER_DISABLED"])

        # 3) captcha exists
        captcha = self.db.get_captcha(captcha_id)
        if not captcha:
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "captcha not found", user["current_index"], captcha_id)
            return build_error("验证码不存在", ERROR_CODES["CAPTCHA_NOT_FOUND"])

        # 4) captcha not expired
        if self.captcha_service.is_expired(captcha["expires_at"]):
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "captcha expired", user["current_index"], captcha_id)
            return build_error("验证码已过期", ERROR_CODES["CAPTCHA_EXPIRED"])

        # 5) captcha not used
        if int(captcha["used"]) == 1:
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "captcha used", user["current_index"], captcha_id)
            return build_error("验证码已使用", ERROR_CODES["CAPTCHA_USED"])

        # 6) captcha match
        if captcha_input != str(captcha["captcha_code"]).upper():
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "captcha mismatch", user["current_index"], captcha_id)
            return build_error("验证码错误", ERROR_CODES["CAPTCHA_MISMATCH"])

        # 7) sequence not exhausted
        if int(user["current_index"]) == 0:
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "sequence exhausted", 0, "need renegotiate")
            return build_error("口令序列已耗尽，请重协商", ERROR_CODES["SEQUENCE_EXHAUSTED"])

        if not is_hex_sha256(otp):
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "invalid otp format", user["current_index"], "non-sha256")
            return build_error("OTP 格式错误", ERROR_CODES["INVALID_REQUEST"])

        # 8) verify OTP
        if not SKeyService.verify_otp(otp, user["current_hash"]):
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "otp invalid", user["current_index"], "otp mismatch")
            return build_error("动态口令错误", ERROR_CODES["OTP_INVALID"])

        next_index = int(user["current_index"]) - 1
        try:
            self.db.mark_captcha_used(captcha_id)
            self.db.consume_otp(username, otp, next_index)
        except sqlite3.DatabaseError:
            self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "fail", "database error", user["current_index"], "consume failed")
            return build_error("数据库错误", ERROR_CODES["DB_ERROR"])

        self._log(username, client_ip, LOG_ACTIONS["LOGIN"], "success", "ok", next_index, "login success")
        return build_ok("登录成功", {"remaining": next_index, "next_index": next_index})

    def renegotiate(self, data: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Reset S/Key sequence with a new seed and tail."""
        username = str(data.get("username", "")).strip()
        new_seed = str(data.get("new_seed", "")).strip()
        chain_length = int(data.get("chain_length", 0) or 0)
        new_chain_tail = str(data.get("new_chain_tail", "")).strip().lower()

        user = self.db.get_user(username)
        if not user:
            self._log(username, client_ip, LOG_ACTIONS["RENEGOTIATE"], "fail", "user not found", None, "renegotiate denied")
            return build_error("用户不存在", ERROR_CODES["USER_NOT_FOUND"])

        if user["status"] != "active":
            self._log(username, client_ip, LOG_ACTIONS["RENEGOTIATE"], "fail", "user disabled", user["current_index"], "status inactive")
            return build_error("用户不可用", ERROR_CODES["USER_DISABLED"])

        if not new_seed or chain_length <= 0 or not is_hex_sha256(new_chain_tail):
            self._log(username, client_ip, LOG_ACTIONS["RENEGOTIATE"], "fail", "invalid payload", user["current_index"], "bad renegotiate data")
            return build_error("重协商参数不合法", ERROR_CODES["INVALID_REQUEST"])

        try:
            self.db.update_user_chain(username, new_seed, chain_length, new_chain_tail, chain_length)
        except sqlite3.DatabaseError:
            self._log(username, client_ip, LOG_ACTIONS["RENEGOTIATE"], "fail", "database error", user["current_index"], "renegotiate failed")
            return build_error("数据库错误", ERROR_CODES["DB_ERROR"])

        self._log(username, client_ip, LOG_ACTIONS["RENEGOTIATE"], "success", "ok", chain_length, "renegotiate success")
        return build_ok("重协商成功", {"username": username, "seed": new_seed, "current_index": chain_length})

    def query_logs(self, data: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Return login logs with optional filters."""
        username = str(data.get("username", "")).strip()
        result = str(data.get("result", "")).strip()
        limit = int(data.get("limit", 100) or 100)
        limit = min(max(limit, 1), 1000)

        try:
            rows = self.db.query_logs(username=username, result=result, limit=limit)
        except sqlite3.DatabaseError:
            self._log(username, client_ip, LOG_ACTIONS["QUERY_LOGS"], "fail", "database error", None, "query logs failed")
            return build_error("数据库错误", ERROR_CODES["DB_ERROR"])

        self._log(username, client_ip, LOG_ACTIONS["QUERY_LOGS"], "success", "ok", None, f"rows={len(rows)}")
        return build_ok("日志查询成功", {"logs": rows})
