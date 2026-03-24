"""Client network core for JSON line protocol interactions."""

from __future__ import annotations

import socket
from typing import Any, Dict


class ClientCore:
    """Thin socket client for request/response operations."""

    def __init__(self, host: str, port: int, timeout: int = 8) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout

    def send_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Send one request and read one response."""
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout) as sock:
                body = __import__("json").dumps(payload, ensure_ascii=False) + "\n"
                sock.sendall(body.encode("utf-8"))

                reader = sock.makefile("r", encoding="utf-8")
                line = reader.readline()
                if not line:
                    return {"ok": False, "message": "服务器无响应", "error_code": "NETWORK_ERROR", "data": {}}
                return __import__("json").loads(line.strip())
        except OSError as exc:
            return {
                "ok": False,
                "message": f"网络错误: {exc}",
                "error_code": "NETWORK_ERROR",
                "data": {},
            }
