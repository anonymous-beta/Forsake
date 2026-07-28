"""Global configuration for Forsake."""

import os
from pathlib import Path

# Base directories
BASE_DIR = Path("/opt/forsake")
DATA_DIR = BASE_DIR / "data"
LOGS_DIR = BASE_DIR / "logs"
CERTS_DIR = BASE_DIR / "certs"
NGINX_DIR = BASE_DIR / "nginx"
LANDING_DIR = BASE_DIR / "landing_pages"
DB_PATH = DATA_DIR / "forsake.db"

# GoPhish
GOPHISH_VERSION = "0.12.1"
GOPHISH_URL = (
    f"https://github.com/gophish/gophish/releases/download/"
    f"v{GOPHISH_VERSION}/gophish-v{GOPHISH_VERSION}-linux-64bit.zip"
)
GOPHISH_PORT = 3333
GOPHISH_PHISH_PORT = 8080
GOPHISH_LISTEN_IP = "127.0.0.1"

# SSL / ACME
ACME_DIR = Path.home() / ".acme.sh"
ACME_BIN = ACME_DIR / "acme.sh"
DOMAIN = None
EMAIL = None

# Web server
WEB_HOST = "0.0.0.0"
WEB_PORT = 8443

# Security
SECRET_KEY = None  # Generated at runtime if None
SESSION_DURATION_HOURS = 8
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_DURATION_MINUTES = 15

# Default smtp relay
SMTP_DEFAULT_HOST = "localhost"
SMTP_DEFAULT_PORT = 25
