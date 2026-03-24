"""JSON line protocol helpers for socket communication."""

from __future__ import annotations

import json
import socket
from typing import Any, Dict


def build_ok(message: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build a success response payload."""
    return {"ok": True, "message": message, "data": data or {}}


def build_error(message: str, error_code: str, data: Dict[str, Any] | None = None) -> Dict[str, Any]:
    """Build a failure response payload."""
    return {"ok": False, "message": message, "error_code": error_code, "data": data or {}}


def send_json_line(sock: socket.socket, payload: Dict[str, Any]) -> None:
    """Send one JSON object as a UTF-8 line."""
    body = json.dumps(payload, ensure_ascii=False) + "\n"
    sock.sendall(body.encode("utf-8"))


def recv_json_line(sock_file) -> Dict[str, Any] | None:
    """Receive one JSON line and parse it."""
    line = sock_file.readline()
    if not line:
        return None
    return json.loads(line.strip())
