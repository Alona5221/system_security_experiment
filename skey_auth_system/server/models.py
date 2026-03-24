"""Data model SQL definitions."""

USERS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    seed TEXT NOT NULL,
    chain_length INTEGER NOT NULL,
    current_index INTEGER NOT NULL,
    current_hash TEXT NOT NULL,
    hash_algo TEXT NOT NULL DEFAULT 'sha256',
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    status TEXT NOT NULL DEFAULT 'active'
);
"""

CAPTCHA_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS captcha_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    captcha_id TEXT NOT NULL UNIQUE,
    captcha_code TEXT NOT NULL,
    created_at TEXT NOT NULL,
    expires_at TEXT NOT NULL,
    used INTEGER NOT NULL DEFAULT 0
);
"""

LOGIN_LOGS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS login_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    client_ip TEXT,
    action TEXT NOT NULL,
    result TEXT NOT NULL,
    reason TEXT,
    seq_no INTEGER,
    detail TEXT,
    created_at TEXT NOT NULL
);
"""
