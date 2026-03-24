"""TCP server core for handling JSON line protocol requests."""

from __future__ import annotations

import logging
import socket
import threading
from typing import Any, Dict

from common.constants import ERROR_CODES, REQUEST_TYPES
from common.protocol import build_error, send_json_line
from server.auth_service import AuthService


class ServerCore:
    """Socket server that dispatches requests to AuthService."""

    def __init__(self, host: str, port: int, auth_service: AuthService) -> None:
        self.host = host
        self.port = port
        self.auth_service = auth_service
        self._stop_event = threading.Event()

    def serve_forever(self) -> None:
        """Start listening and process clients concurrently."""
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as srv:
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind((self.host, self.port))
            srv.listen(50)
            logging.info("Server started at %s:%s", self.host, self.port)

            while not self._stop_event.is_set():
                conn, addr = srv.accept()
                thread = threading.Thread(target=self.handle_client, args=(conn, addr), daemon=True)
                thread.start()

    def handle_client(self, conn: socket.socket, addr: tuple[str, int]) -> None:
        """Handle one client connection."""
        client_ip = addr[0]
        try:
            with conn:
                file = conn.makefile("r", encoding="utf-8")
                while True:
                    line = file.readline()
                    if not line:
                        break
                    try:
                        import json

                        request = json.loads(line.strip())
                        response = self.dispatch(request, client_ip)
                    except json.JSONDecodeError:
                        response = build_error("请求 JSON 格式错误", ERROR_CODES["INVALID_REQUEST"])
                    except Exception as exc:  # pragma: no cover
                        logging.exception("Internal server error: %s", exc)
                        response = build_error("服务器内部错误", ERROR_CODES["INTERNAL_ERROR"])

                    send_json_line(conn, response)
        except Exception as exc:  # pragma: no cover
            logging.exception("Client handling failed from %s: %s", client_ip, exc)

    def dispatch(self, request: Dict[str, Any], client_ip: str) -> Dict[str, Any]:
        """Route request to corresponding service method."""
        req_type = request.get("type")
        data = request.get("data", {})

        if req_type == REQUEST_TYPES["REGISTER"]:
            return self.auth_service.register(data, client_ip)
        if req_type == REQUEST_TYPES["REQUEST_CHALLENGE"]:
            return self.auth_service.request_challenge(data, client_ip)
        if req_type == REQUEST_TYPES["LOGIN"]:
            return self.auth_service.login(data, client_ip)
        if req_type == REQUEST_TYPES["RENEGOTIATE"]:
            return self.auth_service.renegotiate(data, client_ip)
        if req_type == REQUEST_TYPES["QUERY_LOGS"]:
            return self.auth_service.query_logs(data, client_ip)

        return build_error("不支持的请求类型", ERROR_CODES["INVALID_REQUEST"])
