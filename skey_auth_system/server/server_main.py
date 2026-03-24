"""Server entry point."""

from __future__ import annotations

import logging
import os
import sys

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from server.auth_service import AuthService
from server.captcha_service import CaptchaService
from server.config import CAPTCHA_EXPIRE_SECONDS, DB_PATH, HOST, LOG_FILE, PORT
from server.db import Database
from server.server_core import ServerCore


def ensure_runtime_dirs() -> None:
    """Create required runtime directories for db/log files."""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)


def main() -> None:
    """Bootstrap and run the auth server."""
    ensure_runtime_dirs()
    logging.basicConfig(
        filename=LOG_FILE,
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )

    db = Database(DB_PATH)
    db.init_tables()

    captcha_service = CaptchaService(CAPTCHA_EXPIRE_SECONDS)
    auth_service = AuthService(db, captcha_service)
    server = ServerCore(HOST, PORT, auth_service)
    server.serve_forever()


if __name__ == "__main__":
    main()
