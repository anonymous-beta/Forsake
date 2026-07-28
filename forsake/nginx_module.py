"""
NGINX Manager — generates and deploys hardened NGINX configs.
Created by ANONYMOUS-BETA
"""

from pathlib import Path
from typing import Optional

from . import config as cfg
from .utils import ensure_directory, random_server_header, run_command


class NginxManager:
    """Manages NGINX reverse proxy configuration for phishing engagements."""

    def __init__(self, forsake):
        self.forsake = forsake

    def generate_config(self, domain: str, admin_subdomain: str = None,
                        landing_upstream: str = None) -> str:
        """
        Generate a hardened NGINX configuration.

        Features:
        - TLS 1.2/1.3 only with modern ciphers
        - HSTS with preload
        - Rate limiting per IP
        - Request size limits
        - Hidden server version
        - Randomised server header
        - Common exploit blocking
        - GoPhish header stripping
        - Admin subdomain isolation
        - Structured access logging
        """
        if admin_subdomain is None:
            admin_subdomain = f"admin.{domain}"
        if landing_upstream is None:
            landing_upstream = f"{cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PHISH_PORT}"

        server_header = random_server_header()

        config = f"""
# ═══════════════════════════════════════════════════════════════════════════
# FORSAKE NGINX CONFIGURATION
# Generated: {__import__('forsake').utils.timestamp()}
# Domain: {domain}
# Authorized penetration testing use only
# ═══════════════════════════════════════════════════════════════════════════

user www-data;
worker_processes auto;
pid /run/nginx.pid;
worker_rlimit_nofile 65535;

events {{
    worker_connections 4096;
    multi_accept on;
    use epoll;
}}

http {{
    # ── Basic ──
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;
    keepalive_timeout 65;
    keepalive_requests 1000;
    types_hash_max_size 2048;
    server_tokens off;
    server_names_hash_bucket_size 128;
    client_max_body_size 8m;

    include /etc/nginx/mime.types;
    default_type application/octet-stream;

    # ── Logging ──
    log_format forsake '$remote_addr - $remote_user [$time_local] '
                       '"$request" $status $body_bytes_sent '
                       '"$http_referer" "$http_user_agent" '
                       '$request_time $upstream_response_time '
                       '$upstream_addr $ssl_protocol $ssl_cipher';

    access_log {cfg.LOGS_DIR / 'nginx_access.log'} forsake;
    error_log {cfg.LOGS_DIR / 'nginx_error.log'} warn;

    # ── Rate Limiting ──
    limit_req_zone $binary_remote_addr zone=phish:10m rate=30r/s;
    limit_req_zone $binary_remote_addr zone=admin:10m rate=5r/s;
    limit_req_zone $binary_remote_addr zone=landing:10m rate=50r/s burst=100;
    limit_conn_zone $binary_remote_addr zone=addr:10m;

    # ── SSL ──
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384:ECDHE-ECDSA-CHACHA20-POLY1305:ECDHE-RSA-CHACHA20-POLY1305:DHE-RSA-AES128-GCM-SHA256:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1h;
    ssl_session_tickets off;
    ssl_buffer_size 4k;
    ssl_stapling on;
    ssl_stapling_verify on;
    resolver 1.1.1.1 8.8.8.8 valid=300s;
    resolver_timeout 5s;

    # ── Gzip ──
    gzip on;
    gzip_vary on;
    gzip_proxied any;
    gzip_comp_level 6;
    gzip_min_length 256;
    gzip_types text/plain text/css text/javascript application/javascript application/json application/xml image/svg+xml;

    # ── Real IP ──
    set_real_ip_from 10.0.0.0/8;
    set_real_ip_from 172.16.0.0/12;
    set_real_ip_from 192.168.0.0/16;
    real_ip_header X-Forwarded-For;

    # ── Upstreams ──
    upstream gophish_phish {{
        server {landing_upstream} max_fails=3 fail_timeout=30s;
        keepalive 64;
    }}

    upstream gophish_admin {{
        server {cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PORT} max_fails=3 fail_timeout=30s;
        keepalive 16;
    }}

    # ── HTTP → HTTPS Redirect ──
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

    # ── Main Phishing Server ──
    server {{
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name {domain};
        server_tokens off;

        ssl_certificate {cfg.CERTS_DIR / 'fullchain.pem'};
        ssl_certificate_key {cfg.CERTS_DIR / 'key.pem'};

        # HSTS
        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "0" always;
        add_header Referrer-Policy "no-referrer" always;
        add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;

        # Spoof server header
        more_set_headers "Server: {server_header}";

        # Remove GoPhish-specific headers
        proxy_hide_header X-Gophish-Contact;
        proxy_hide_header X-Gophish-Signature;

        # Rate limiting
        limit_req zone=phish burst=40 nodelay;
        limit_conn addr 10;

        # Block scanners and bots
        if ($http_user_agent ~* (curl|wget|python|nikto|sqlmap|nmap|masscan|zgrab|go-http-client|Scrapy|httpie)) {{
            return 444;
        }}

        if ($http_user_agent = "") {{
            return 444;
        }}

        # Block common exploit paths
        location ~* (\\\\b\\\\bwp-admin|wp-content|admin/|\.git/|\.env|\.htaccess|\.svn|\.DS_Store) {{
            deny all;
            return 403;
        }}

        # Main proxy
        location / {{
            proxy_pass http://gophish_phish;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_set_header X-Forwarded-Host $host;
            proxy_set_header X-Forwarded-Port $server_port;
            proxy_buffering on;
            proxy_buffer_size 4k;
            proxy_buffers 8 8k;
            proxy_busy_buffers_size 16k;
            proxy_cache_valid 200 302 10s;
            proxy_cache_valid 404 1m;
            proxy_cache_use_stale error timeout updating http_500 http_502 http_503 http_504;
            proxy_connect_timeout 30s;
            proxy_read_timeout 30s;
            proxy_send_timeout 30s;
        }}

        # Tracking endpoint
        location = /track {{
            proxy_pass http://gophish_phish;
            proxy_http_version 1.1;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            add_header Cache-Control "no-store, no-cache, must-revalidate";
        }}
    }}

    # ── Admin Interface ──
    server {{
        listen 443 ssl http2;
        listen [::]:443 ssl http2;
        server_name {admin_subdomain};
        server_tokens off;

        ssl_certificate {cfg.CERTS_DIR / 'fullchain.pem'};
        ssl_certificate_key {cfg.CERTS_DIR / 'key.pem'};

        add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
        add_header X-Content-Type-Options "nosniff" always;
        add_header X-Frame-Options "DENY" always;
        add_header X-XSS-Protection "0" always;
        add_header Referrer-Policy "same-origin" always;

        limit_req zone=admin burst=10 nodelay;
        limit_conn addr 3;

        location / {{
            proxy_pass https://gophish_admin;
            proxy_http_version 1.1;
            proxy_set_header Upgrade $http_upgrade;
            proxy_set_header Connection "upgrade";
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            proxy_buffering off;
            proxy_ssl_verify off;
        }}
    }}
}}
"""
        config_path = cfg.NGINX_DIR / "forsake_nginx.conf"
        config_path.write_text(config)
        print(f"[+] NGINX config generated: {config_path}")
        return config

    def install_config(self) -> bool:
        """Install the NGINX config into the system NGINX configuration."""
        nginx_include = f"# Forsake NGINX Configuration\ninclude {cfg.NGINX_DIR / 'forsake_nginx.conf'};\n"
        try:
            Path("/etc/nginx/conf.d/forsake.conf").write_text(nginx_include)
            rc, out, err = run_command("nginx -t")
            if rc == 0:
                run_command("systemctl reload nginx")
                print("[+] NGINX config installed and reloaded")
                return True
            else:
                print(f"[-] NGINX config test failed: {err}")
                return False
        except PermissionError:
            print("[!] Not root — please install NGINX config manually:")
            print(f"    cp {cfg.NGINX_DIR / 'forsake_nginx.conf'} /etc/nginx/conf.d/")
            print("    nginx -t && systemctl reload nginx")
            return False
