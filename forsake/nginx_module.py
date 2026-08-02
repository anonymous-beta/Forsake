"""
NGINX Manager — generates and deploys hardened NGINX configs.
Created by ANONYMOUS-BETA
"""

from pathlib import Path
from typing import Optional

from . import config as cfg
from .utils import ensure_directory, random_server_header, run_command, timestamp


class NginxManager:
    """Manages NGINX reverse proxy configuration for phishing engagements."""

    def __init__(self, forsake):
        self.forsake = forsake

    def generate_config(self, domain: str, admin_subdomain: str = None,
                        landing_upstream: str = None) -> str:
        """
        Generate a hardened NGINX *site* configuration suitable for conf.d.
        Features retained:
        - TLS 1.2/1.3 only with modern ciphers
        - HSTS with preload
        - Rate limiting per IP
        - Request size limits
        - Hidden server version
        - Randomised Server header
        - Common exploit / scanner blocking
        - GoPhish header stripping
        - Admin subdomain isolation
        - Structured access logging (via main nginx.conf)
        """
        if admin_subdomain is None:
            admin_subdomain = f"admin.{domain}"
        if landing_upstream is None:
            landing_upstream = f"{cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PHISH_PORT}"

        server_header = random_server_header()

        config = f"""# ═══════════════════════════════════════════════════════════════════════════
# FORSAKE NGINX SITE CONFIGURATION
# Generated: {timestamp()}
# Domain: {domain}
# Authorized penetration testing use only
# ═══════════════════════════════════════════════════════════════════════════

# Rate-limit zones
limit_req_zone $binary_remote_addr zone=forsake_phish:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=forsake_admin:10m rate=5r/s;
limit_conn_zone $binary_remote_addr zone=forsake_addr:10m;

upstream forsake_gophish_phish {{
    server {landing_upstream} max_fails=3 fail_timeout=30s;
    keepalive 64;
}}

upstream forsake_gophish_admin {{
    server {cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PORT} max_fails=3 fail_timeout
