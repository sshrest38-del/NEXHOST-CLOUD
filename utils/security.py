"""
NEXHOST CLOUD - Security and Cryptography Utilities
Author: @Harsh_54x
"""

import hashlib
import os
import secrets
import re
from typing import List, Optional

def hash_password(password: str) -> str:
    """Hash password using PBKDF2 with SHA-256 and salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac(
        'sha256',
        password.encode('utf-8'),
        salt.encode('utf-8'),
        100_000
    )
    return f"{salt}${key.hex()}"

def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify password against stored salt$hash."""
    try:
        if not stored_password or '$' not in stored_password:
            return False
        salt, key_hex = stored_password.split('$', 1)
        new_key = hashlib.pbkdf2_hmac(
            'sha256',
            provided_password.encode('utf-8'),
            salt.encode('utf-8'),
            100_000
        )
        return secrets.compare_digest(new_key.hex(), key_hex)
    except Exception:
        return False

def generate_secure_token(length: int = 32) -> str:
    """Generate cryptographically secure URL-safe token."""
    return secrets.token_urlsafe(length)

def mask_sensitive_text(text: str, custom_secrets: Optional[List[str]] = None) -> str:
    """
    Mask sensitive secrets, API tokens, and passwords in console logs.
    Never exposes Telegram Bot tokens or custom env var values.
    """
    if not text:
        return ""

    masked = text

    # Mask custom env values if provided
    if custom_secrets:
        for sec in custom_secrets:
            if sec and len(sec.strip()) >= 4:
                masked = masked.replace(sec.strip(), "********")

    # Mask Telegram Bot Tokens: regex matches 123456789:ABCdefGhIjkLmNoPqRsTuVwXyZ...
    bot_token_pattern = re.compile(r'\b\d{8,10}:[a-zA-Z0-9_-]{35}\b')
    masked = bot_token_pattern.sub("[MASKED_TELEGRAM_BOT_TOKEN]", masked)

    # Mask generic API Key headers or variables: API_KEY=xyz, TOKEN=xyz, PASSWORD=xyz
    generic_kv_pattern = re.compile(r'(?i)(token|key|secret|password|passwd|auth)=([^\s;&]+)')
    masked = generic_kv_pattern.sub(r'\1=********', masked)

    return masked
