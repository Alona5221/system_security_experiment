"""Shared constants for the S/Key authentication system."""

ERROR_CODES = {
    "USER_NOT_FOUND": "USER_NOT_FOUND",
    "USER_EXISTS": "USER_EXISTS",
    "USER_DISABLED": "USER_DISABLED",
    "INVALID_REQUEST": "INVALID_REQUEST",
    "CAPTCHA_NOT_FOUND": "CAPTCHA_NOT_FOUND",
    "CAPTCHA_EXPIRED": "CAPTCHA_EXPIRED",
    "CAPTCHA_USED": "CAPTCHA_USED",
    "CAPTCHA_MISMATCH": "CAPTCHA_MISMATCH",
    "OTP_INVALID": "OTP_INVALID",
    "SEQUENCE_EXHAUSTED": "SEQUENCE_EXHAUSTED",
    "NETWORK_ERROR": "NETWORK_ERROR",
    "DB_ERROR": "DB_ERROR",
    "INTERNAL_ERROR": "INTERNAL_ERROR",
}

REQUEST_TYPES = {
    "REGISTER": "register",
    "REQUEST_CHALLENGE": "request_challenge",
    "LOGIN": "login",
    "RENEGOTIATE": "renegotiate",
    "QUERY_LOGS": "query_logs",
}

LOG_ACTIONS = {
    "REGISTER": "register",
    "REQUEST_CHALLENGE": "request_challenge",
    "LOGIN": "login",
    "RENEGOTIATE": "renegotiate",
    "QUERY_LOGS": "query_logs",
}
