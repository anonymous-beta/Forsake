"""Utility functions for Forsake."""

import os
import re
import json
import random
import string
import hashlib
import secrets
import subprocess
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Union

try:
    import bcrypt
    _HAS_BCRYPT = True
except ImportError:
    _HAS_BCRYPT = False


def generate_password(length: int = 32) -> str:
    """Generate a cryptographically secure random password."""
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+[]{}|;:,.<>?"
    return ''.join(secrets.SystemRandom().choice(alphabet) for _ in range(length))


def generate_api_key() -> str:
    """Generate a GoPhish-compatible API key."""
    return secrets.token_hex(32)


def random_server_header() -> str:
    """Return a realistic random server header to mask NGINX."""
    headers = [
        "cloudflare",
        "Apache/2.4.62 (Ubuntu)",
        "Apache/2.4.63 (Debian)",
        "Microsoft-IIS/10.0",
        "Microsoft-IIS/8.5",
        "openresty/1.25.3.1",
        "AkamaiGHost",
        "Caddy",
        "AmazonS3",
        "CloudFront",
        "LiteSpeed",
        "nginx/1.24.0",
        "Apache/2.4.61 (CentOS)",
    ]
    return random.choice(headers)


def hash_password(password: str) -> str:
    """Hash a password using bcrypt (preferred) or strong PBKDF2."""
    if _HAS_BCRYPT:
        return "bcrypt:" + bcrypt.hashpw(password.encode(), bcrypt.gensalt(rounds=12)).decode()
    salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000)
    return f"pbkdf2:{salt}:{dk.hex()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash (constant-time where possible)."""
    try:
        if hashed.startswith("bcrypt:"):
            if not _HAS_BCRYPT:
                return False
            return bcrypt.checkpw(password.encode(), hashed[7:].encode())
        if hashed.startswith("pbkdf2:"):
            _, salt, expected = hashed.split(":", 2)
            dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 600_000)
            return secrets.compare_digest(dk.hex(), expected)
        # Legacy SHA-256 support for migration
        if ":" in hashed:
            salt, h = hashed.split(":", 1)
            candidate = hashlib.sha256((salt + password).encode()).hexdigest()
            return secrets.compare_digest(candidate, h)
    except Exception:
        return False
    return False


def sanitize_domain(domain: str) -> str:
    """Sanitize and validate domain name."""
    domain = domain.strip().lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.rstrip('/')
    if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$', domain):
        raise ValueError(f"Invalid domain: {domain}")
    return domain


def run_command(cmd: Union[str, List[str]], timeout: int = 120, shell: bool = False) -> tuple:
    """
    Run a command and return (returncode, stdout, stderr).
    Prefer list form to avoid shell injection.
    """
    if isinstance(cmd, str) and not shell:
        import shlex
        cmd = shlex.split(cmd)
    result = subprocess.run(
        cmd, shell=shell, capture_output=True, text=True, timeout=timeout
    )
    return result.returncode, result.stdout.strip(), result.stderr.strip()


def ensure_directory(path: Path) -> Path:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)
    return path


def timestamp() -> str:
    """Get current ISO timestamp."""
    return datetime.now().isoformat()


def format_bytes(bytes_val: int) -> str:
    """Format bytes to human-readable string."""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_val < 1024:
            return f"{bytes_val:.1f} {unit}"
        bytes_val /= 1024
    return f"{bytes_val:.1f} TB"
