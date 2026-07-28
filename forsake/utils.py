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
from typing import Optional


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
    """Hash a password using SHA-256 with salt."""
    salt = secrets.token_hex(16)
    return f"{salt}:{hashlib.sha256((salt + password).encode()).hexdigest()}"


def verify_password(password: str, hashed: str) -> bool:
    """Verify a password against its hash."""
    salt, h = hashed.split(":")
    return h == hashlib.sha256((salt + password).encode()).hexdigest()


def sanitize_domain(domain: str) -> str:
    """Sanitize and validate domain name."""
    domain = domain.strip().lower()
    domain = re.sub(r'^https?://', '', domain)
    domain = domain.rstrip('/')
    if not re.match(r'^[a-z0-9]([a-z0-9-]*[a-z0-9])?(\.[a-z0-9]([a-z0-9-]*[a-z0-9])?)*$', domain):
        raise ValueError(f"Invalid domain: {domain}")
    return domain


def run_command(cmd: str, timeout: int = 120) -> tuple:
    """Run a shell command and return (returncode, stdout, stderr)."""
    result = subprocess.run(
        cmd, shell=True, capture_output=True, text=True, timeout=timeout
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
