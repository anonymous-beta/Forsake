"""
Forsake Core — Main orchestration engine.
Created by ANONYMOUS-BETA
"""

import os
import sys
import json
import time
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

from . import config as cfg
from .utils import (
    generate_password, generate_api_key, random_server_header,
    ensure_directory, run_command, timestamp, sanitize_domain
)
from .gophish_module import GoPhishManager
from .nginx_module import NginxManager
from .ssl_module import CertManager
from .clone_module import LandingPageCloner


class Forsake:
    """
    Forsake — Enterprise phishing engagement orchestrator.
    Combines GoPhish with a hardened NGINX reverse proxy,
    automatic SSL management, and landing page cloning.
    """

    def __init__(self, base_dir: str = None):
        self.base_dir = Path(base_dir) if base_dir else cfg.BASE_DIR
        self._init_paths()
        self.gophish = GoPhishManager(self)
        self.nginx = NginxManager(self)
        self.ssl = CertManager(self)
        self.cloner = LandingPageCloner(self)

        # State
        self.domain = None
        self.admin_password = None
        self.api_key = None
        self.config_data = {}

    def _init_paths(self):
        """Initialize all directory paths."""
        cfg.BASE_DIR = self.base_dir
        cfg.DATA_DIR = ensure_directory(self.base_dir / "data")
        cfg.LOGS_DIR = ensure_directory(self.base_dir / "logs")
        cfg.CERTS_DIR = ensure_directory(self.base_dir / "certs")
        cfg.NGINX_DIR = ensure_directory(self.base_dir / "nginx")
        cfg.LANDING_DIR = ensure_directory(self.base_dir / "landing_pages")

    # ─── Deployment ───────────────────────────────────────────────────────

    def deploy(self, domain: str, email: str = None,
               admin_password: str = None, clone_url: str = None,
               smtp_host: str = None) -> dict:
        """
        Full end-to-end deployment.
        
        Returns a dict with deployment results and credentials.
        """
        start = time.time()
        self.domain = sanitize_domain(domain)
        self.admin_password = admin_password or generate_password(32)
        self.api_key = generate_api_key()

        if email:
            cfg.EMAIL = email

        steps = []
        errors = []

        # Step 1: Setup directories
        try:
            self._init_paths()
            steps.append(("directories", "ok"))
        except Exception as e:
            errors.append(f"Directory setup failed: {e}")
            return {"status": "error", "errors": errors}

        # Step 2: Install & configure GoPhish
        try:
            self.gophish.install()
            self.gophish.configure(admin_password, self.api_key)
            steps.append(("gophish", "ok"))
        except Exception as e:
            errors.append(f"GoPhish failed: {e}")

        # Step 3: Obtain SSL certificate
        try:
            self.ssl.obtain(domain, email)
            steps.append(("ssl", "ok"))
        except Exception as e:
            errors.append(f"SSL failed: {e}")
            # Fallback to self-signed
            try:
                self.ssl.generate_self_signed(domain)
                steps.append(("ssl_self_signed", "ok"))
            except Exception as e2:
                errors.append(f"Self-signed SSL also failed: {e2}")

        # Step 4: Generate NGINX config
        try:
            self.nginx.generate_config(domain)
            self.nginx.install_config()
            steps.append(("nginx", "ok"))
        except Exception as e:
            errors.append(f"NGINX config failed: {e}")

        # Step 5: Clone landing page (optional)
        if clone_url:
            try:
                result = self.cloner.clone(clone_url)
                self.cloner.inject_tracking(result)
                steps.append(("landing_page", "ok"))
            except Exception as e:
                errors.append(f"Landing page clone failed: {e}")

        # Step 6: Write systemd services
        try:
            self._write_systemd_services()
            steps.append(("systemd", "ok"))
        except Exception as e:
            errors.append(f"Systemd services failed: {e}")

        # Step 7: Save deployment config
        self._save_config()

        elapsed = time.time() - start

        result = {
            "status": "deployed" if not errors else "deployed_with_warnings",
            "domain": self.domain,
            "admin_password": self.admin_password,
            "api_key": self.api_key,
            "steps": steps,
            "errors": errors,
            "elapsed_seconds": round(elapsed, 1),
            "timestamp": timestamp(),
            "admin_url": f"https://admin.{self.domain}",
            "phishing_url": f"https://{self.domain}",
            "version": __import__('forsake').__version__
        }

        self._print_deployment_banner(result)
        return result

    def _print_deployment_banner(self, result: dict):
        """Print the deployment completion banner."""
        banner = f"""
{'='*60}
  ███████╗ ██████╗ ██████╗ ███████╗ █████╗ ██╗  ██╗███████╗
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔════╝
  █████╗  ██║   ██║██████╔╝███████╗███████║█████╔╝ █████╗  
  ██╔══╝  ██║   ██║██╔══██╗╚════██║██╔══██║██╔═██╗ ██╔══╝  
  ██║     ╚██████╔╝██║  ██║███████║██║  ██║██║  ██╗███████╗
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
  v{result['version']} — by ANONYMOUS-BETA
{'='*60}
  ✅ Deployment Complete! ({result['elapsed_seconds']}s)
{'='*60}

  🌐 Phishing URL:   https://{result['domain']}
  🔐 Admin Panel:    {result['admin_url']}
  🔑 Admin Password: {result['admin_password']}
  🔑 API Key:        {result['api_key']}

  📁 Config:     {cfg.DATA_DIR / 'forsake_config.json'}
  📂 Landing:    {cfg.LANDING_DIR}
  📋 Logs:       {cfg.LOGS_DIR}

  ▶ Start:  sudo systemctl start forsake-gophish forsake-nginx
  ⏹ Stop:   sudo systemctl stop forsake-gophish forsake-nginx
  📊 Status: sudo systemctl status forsake-gophish forsake-nginx

  ⚠ CHANGE YOUR ADMIN PASSWORD ON FIRST LOGIN ⚠
{'='*60}
"""
        print(banner)

    # ─── Configuration Persistence ────────────────────────────────────────

    def _save_config(self):
        """Save deployment config to disk."""
        config = {
            "version": __import__('forsake').__version__,
            "created": timestamp(),
            "domain": self.domain,
            "admin_password": self.admin_password,
            "api_key": self.api_key,
            "gophish_port": cfg.GOPHISH_PORT,
            "gophish_phish_port": cfg.GOPHISH_PHISH_PORT,
            "base_dir": str(self.base_dir),
            "certs_dir": str(cfg.CERTS_DIR),
            "landing_dir": str(cfg.LANDING_DIR),
            "logs_dir": str(cfg.LOGS_DIR),
            "nginx_config": str(cfg.NGINX_DIR / "forsake_nginx.conf"),
        }

        config_path = cfg.DATA_DIR / "forsake_config.json"
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=4)
        config_path.chmod(0o600)

    def load_config(self) -> Optional[dict]:
        """Load existing deployment config."""
        config_path = cfg.DATA_DIR / "forsake_config.json"
        if config_path.exists():
            with open(config_path) as f:
                self.config_data = json.load(f)
                self.domain = self.config_data.get("domain")
                self.admin_password = self.config_data.get("admin_password")
                self.api_key = self.config_data.get("api_key")
                return self.config_data
        return None

    # ─── Systemd ──────────────────────────────────────────────────────────

    def _write_systemd_services(self):
        """Create systemd service files for Forsake services."""
        gophish_svc = f"""[Unit]
Description=Forsake — GoPhish Phishing Engine
Documentation=https://github.com/anonymous-beta/Forsake
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory={cfg.BASE_DIR / 'data' / 'gophish'}
ExecStart={cfg.BASE_DIR / 'data' / 'gophish' / 'gophish'}
Restart=always
RestartSec=5
StandardOutput=append:{cfg.LOGS_DIR / 'gophish.log'}
StandardError=append:{cfg.LOGS_DIR / 'gophish_error.log'}
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
"""
        svc_path = Path("/etc/systemd/system/forsake-gophish.service")
        try:
            svc_path.write_text(gophish_svc)
            run_command("systemctl daemon-reload")
        except PermissionError:
            print("[!] Cannot write systemd service (not root). Manual install required.")

    # ─── Teardown ─────────────────────────────────────────────────────────

    def teardown(self, remove_data: bool = False):
        """Remove Forsake deployment from the system."""
        print("\n[!] Forsake Teardown initiated\n")

        # Stop services
        for svc in ["forsake-gophish", "forsake-nginx"]:
            run_command(f"systemctl stop {svc}")
            run_command(f"systemctl disable {svc}")

        # Remove systemd files
        for path in Path("/etc/systemd/system").glob("forsake-*.service"):
            path.unlink(missing_ok=True)

        # Remove NGINX config
        nginx_conf = Path("/etc/nginx/conf.d/forsake.conf")
        nginx_conf.unlink(missing_ok=True)

        run_command("systemctl daemon-reload")

        if remove_data:
            import shutil
            shutil.rmtree(self.base_dir, ignore_errors=True)
            print("[+] All Forsake data removed.")
        else:
            print(f"[+] Data preserved at {self.base_dir}")

        print("[+] Forsake removed from system.")

    # ─── Status ───────────────────────────────────────────────────────────

    def status(self) -> dict:
        """Get current deployment status."""
        config = self.load_config()
        if not config:
            return {"status": "not_deployed"}

        gophish_running = run_command(
            "systemctl is-active forsake-gophish"
        )[0] == 0

        nginx_running = run_command(
            "systemctl is-active nginx"
        )[0] == 0

        certs_exist = (cfg.CERTS_DIR / "fullchain.pem").exists()

        return {
            "status": "active" if gophish_running else "deployed",
            "domain": config.get("domain"),
            "version": config.get("version"),
            "created": config.get("created"),
            "gophish_running": gophish_running,
            "nginx_running": nginx_running,
            "certs_valid": certs_exist,
            "admin_url": f"https://admin.{config.get('domain', '?')}",
            "phishing_url": f"https://{config.get('domain', '?')}",
                 }
