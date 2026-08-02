"""
NGINX Manager — generates and deploys hardened NGINX configs.
Created by ANONYMOUS-BETA
"""

from pathlib import Path
from typing import Optional

from . import config as cfg
from .utils import random_server_header, run_command, timestamp


class NginxManager:
    """Manages NGINX reverse proxy configuration for phishing engagements."""

    def __init__(self, forsake):
        self.forsake = forsake

    def generate_config(self, domain: str, admin_subdomain: str = None,
                        landing_upstream: str = None) -> str:
        """
        Generate a hardened *site* configuration suitable for
        /etc/nginx/conf.d/ (no full nginx.conf structure).
        """
        if admin_subdomain is None:
            admin_subdomain = f"admin.{domain}"
        if landing_upstream is None:
            landing_upstream = f"{cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PHISH_PORT}"

        server_header = random_server_header()

        config = f"""# ═══════════════════════════════════════════════════════════════════════════
# FORSAKE NGINX SITE CONFIG
# Generated: {timestamp()}
# Domain: {domain}
# Authorized penetration testing use only
# ═══════════════════════════════════════════════════════════════════════════

limit_req_zone $binary_remote_addr zone=forsake_phish:10m rate=30r/s;
limit_req_zone $binary_remote_addr zone=forsake_admin:10m rate=5r/s;
limit_conn_zone $binary_remote_addr zone=forsake_addr:10m;

upstream forsake_gophish_phish {{
    server {landing_upstream} max_fails=3 fail_timeout=30s;
    keepalive 64;
}}

upstream forsake_gophish_admin {{
    server {cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PORT} max_fails=3 fail_timeout=30s;
    keepalive 16;
}}

# HTTP → HTTPS + ACME
server {{
    listen 80;
    listen [::]:80;
    server_name {domain} {admin_subdomain};
    server_tokens off;

    location /.well-known/acme-challenge/ {{
        root /var/www/html;
        allow all;
    }}

    location / {{
        return 301 https://$host$request_uri;
    }}
}}

# Main phishing server
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {domain};
    server_tokens off;

    ssl_certificate     {cfg.CERTS_DIR / 'fullchain.pem'};
    ssl_certificate_key {cfg.CERTS_DIR / 'key.pem'};
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache   shared:SSL:10m;
    ssl_session_timeout 1h;
    ssl_session_tickets off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "no-referrer" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Server "{server_header}" always;

    proxy_hide_header X-Gophish-Contact;
    proxy_hide_header X-Gophish-Signature;

    limit_req zone=forsake_phish burst=40 nodelay;
    limit_conn forsake_addr 10;
    client_max_body_size 8m;

    if ($http_user_agent \~* (curl|wget|python|nikto|sqlmap|nmap|masscan|zgrab|go-http-client|Scrapy|httpie)) {{
        return 444;
    }}
    if ($http_user_agent = "") {{
        return 444;
    }}

    location \~* (wp-admin|wp-content|/admin/|\\.git/|\\.env|\\.htaccess|\\.svn|\\.DS_Store) {{
        deny all;
        return 403;
    }}

    location / {{
        proxy_pass http://forsake_gophish_phish;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_set_header X-Forwarded-Host $host;
        proxy_connect_timeout 30s;
        proxy_read_timeout 30s;
        proxy_send_timeout 30s;
    }}

    location = /track {{
        proxy_pass http://forsake_gophish_phish;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        add_header Cache-Control "no-store, no-cache, must-revalidate";
    }}
}}

# Admin interface
server {{
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name {admin_subdomain};
    server_tokens off;

    ssl_certificate     {cfg.CERTS_DIR / 'fullchain.pem'};
    ssl_certificate_key {cfg.CERTS_DIR / 'key.pem'};
    ssl_protocols       TLSv1.2 TLSv1.3;
    ssl_ciphers         ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;

    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-Frame-Options "DENY" always;
    add_header Referrer-Policy "same-origin" always;

    limit_req zone=forsake_admin burst=10 nodelay;
    limit_conn forsake_addr 3;

    location / {{
        proxy_pass https://forsake_gophish_admin;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_verify off;
        proxy_buffering off;
    }}
}}
"""
        config_path = cfg.NGINX_DIR / "forsake_nginx.conf"
        config_path.write_text(config)
        print(f"[+] NGINX site config generated: {config_path}")
        return config

    def install_config(self) -> bool:
        """Copy the generated site config into conf.d and reload NGINX."""
        try:
            src = cfg.NGINX_DIR / "forsake_nginx.conf"
            dst = Path("/etc/nginx/conf.d/forsake.conf")
            dst.write_text(src.read_text())

            rc, out, err = run_command("nginx -t")
            if rc == 0:
                run_command("systemctl reload nginx")
                print("[+] NGINX config installed and reloaded")
                return True
            else:
                print(f"[-] NGINX config test failed:\n{err}")
                return False
        except PermissionError:
            print("[!] Not root — install the config manually:")
            print(f"    cp {cfg.NGINX_DIR / 'forsake_nginx.conf'} /etc/nginx/conf.d/forsake.conf")
            print("    nginx -t && systemctl reload nginx")
            return False
