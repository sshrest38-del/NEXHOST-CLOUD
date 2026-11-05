"""
NEXHOST CLOUD - Central Configuration Module
Developer: @Harsh_54x (https://t.me/Harsh_54x)
Tagline: Your Bots. Your Cloud.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base directory of the project
BASE_DIR = Path(__file__).resolve().parent

# Try loading from .env
load_dotenv(BASE_DIR / ".env", override=True)

def get_secret(key: str, default: str = "") -> str:
    """Retrieve secret from Streamlit secrets or OS environment."""
    try:
        import streamlit as st
        if hasattr(st, "secrets") and key in st.secrets:
            return str(st.secrets[key])
    except Exception:
        pass
    return os.getenv(key, default)

# Platform Branding
PLATFORM_NAME = get_secret("PLATFORM_NAME", "NEXHOST CLOUD")
TAGLINE = get_secret("TAGLINE", "Your Bots. Your Cloud.")
DEVELOPER_HANDLE = get_secret("DEVELOPER_HANDLE", "@Harsh_54x")
DEVELOPER_TELEGRAM = get_secret("DEVELOPER_TELEGRAM", "https://t.me/Harsh_54x")
CURRENCY_SYMBOL = get_secret("CURRENCY_SYMBOL", "₹")
SUPPORT_EMAIL = get_secret("SUPPORT_EMAIL", "support@nexhostcloud.local")

# Security
SECRET_KEY = get_secret("SECRET_KEY", "nexhost_default_secure_secret_key_3847291834710")
SESSION_EXPIRY_HOURS = int(get_secret("SESSION_EXPIRY_HOURS", "72"))

# Super Admin auto-provision credentials
SUPERADMIN_EMAIL = get_secret("SUPERADMIN_EMAIL", "owner@nexhost.cloud")
SUPERADMIN_USERNAME = get_secret("SUPERADMIN_USERNAME", "owner")
SUPERADMIN_PASSWORD = get_secret("SUPERADMIN_PASSWORD", "OwnerSecurePass2026!")
SUPERADMIN_NAME = get_secret("SUPERADMIN_NAME", "Super Administrator")

# Payment Settings
ADMIN_UPI_ID = get_secret("ADMIN_UPI_ID", "harsh54x@upi")
ADMIN_UPI_NAME = get_secret("ADMIN_UPI_NAME", "NEXHOST CLOUD / Harsh")
ADMIN_PAYMENT_NOTE = get_secret("ADMIN_PAYMENT_NOTE", "NEXHOST Cloud Subscription")
UPI_QR_IMAGE_PATH = get_secret("UPI_QR_IMAGE_PATH", str(BASE_DIR / "static" / "default_upi_qr.png"))

# Official NEXHOST Platform Telegram Bot & Access Control
TELEGRAM_BOT_TOKEN = get_secret("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_API_ID = get_secret("TELEGRAM_API_ID", "")
TELEGRAM_API_HASH = get_secret("TELEGRAM_API_HASH", "")
_owner_id_raw = get_secret("TELEGRAM_OWNER_ID", "0").strip()
TELEGRAM_OWNER_ID = int(_owner_id_raw) if _owner_id_raw.isdigit() else 0

# Database
DATABASE_URL = get_secret("DATABASE_URL", f"sqlite:///{BASE_DIR / 'data' / 'nexhost.db'}")
MONGO_URI = get_secret("MONGO_URI", get_secret("MONGODB_URI", ""))

# Worker Infrastructure
WORKER_TYPE = get_secret("WORKER_TYPE", "sandbox")  # 'docker' or 'sandbox'
WORKER_URL = get_secret("WORKER_URL", "http://127.0.0.1:8000")
WORKER_API_KEY = get_secret("WORKER_API_KEY", "worker_shared_secret_token_12345")
WORKER_DEFAULT_MEMORY_MB = int(get_secret("WORKER_DEFAULT_MEMORY_MB", "512"))
WORKER_DEFAULT_CPU_LIMIT = float(get_secret("WORKER_DEFAULT_CPU_LIMIT", "1.0"))

# Persistent Storage Directories
DATA_DIR = BASE_DIR / "data"
STORAGE_BASE_DIR = BASE_DIR / get_secret("STORAGE_BASE_DIR", "data/storage")
BACKUP_BASE_DIR = BASE_DIR / get_secret("BACKUP_BASE_DIR", "data/backups")
LOGS_BASE_DIR = BASE_DIR / get_secret("LOGS_BASE_DIR", "data/logs")
STATIC_DIR = BASE_DIR / "static"

# Ensure runtime directories exist
for path in [DATA_DIR, STORAGE_BASE_DIR, BACKUP_BASE_DIR, LOGS_BASE_DIR, STATIC_DIR]:
    path.mkdir(parents=True, exist_ok=True)
