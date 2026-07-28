"""
GoPhish Manager — installs, configures, and manages GoPhish instances.
Created by ANONYMOUS-BETA
"""

import json
import os
import shutil
import ssl
import urllib.request
import zipfile
from pathlib import Path
from typing import Optional

from . import config as cfg
from .utils import ensure_directory, generate_password, generate_api_key, run_command


class GoPhishManager:
    """Manages GoPhish installation and API interaction."""

    def __init__(self, forsake):
        self.forsake = forsake
        self.gophish_dir = cfg.DATA_DIR / "gophish"
        self.config_path = self.gophish_dir / "config.json"

    def install(self) -> bool:
        """Download and install GoPhish if not already present."""
        if (self.gophish_dir / "gophish").exists():
            print("[*] GoPhish binary already present, skipping download.")
            return True

        ensure_directory(self.gophish_dir)
        zip_path = self.gophish_dir.parent / "gophish.zip"

        print(f"[*] Downloading GoPhish v{cfg.GOPHISH_VERSION}...")
        try:
            ctx = ssl._create_unverified_context()
            with urllib.request.urlopen(cfg.GOPHISH_URL, context=ctx) as resp:
                with open(zip_path, 'wb') as f:
                    shutil.copyfileobj(resp, f)

            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(self.gophish_dir)

            (self.gophish_dir / "gophish").chmod(0o755)
            zip_path.unlink()
            print(f"[+] GoPhish v{cfg.GOPHISH_VERSION} installed at {self.gophish_dir}")
            return True
        except Exception as e:
            raise RuntimeError(f"GoPhish download failed: {e}")

    def configure(self, admin_password: str, api_key: str) -> dict:
        """Write hardened GoPhish config.json."""
        config = {
            "admin_server": {
                "listen_url": f"{cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PORT}",
                "use_tls": True,
                "cert_path": str(cfg.CERTS_DIR / "gophish_admin.crt"),
                "key_path": str(cfg.CERTS_DIR / "gophish_admin.key"),
            },
            "phish_server": {
                "listen_url": f"{cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PHISH_PORT}",
                "use_tls": False,
            },
            "db_name": "sqlite3",
            "db_path": str(self.gophish_dir / "gophish.db"),
            "migrations_prefix": "db_",
            "trusted_origins": [
                f"https://{forsake.domain}" if self.forsake.domain else "https://localhost",
                f"https://admin.{forsake.domain}" if self.forsake.domain else "https://localhost:3333",
            ],
            "password": admin_password,
            "api_key": api_key,
        }

        with open(self.config_path, 'w') as f:
            json.dump(config, f, indent=4)

        self.config_path.chmod(0o600)

        # Generate self-signed cert for GoPhish admin interface
        self._generate_admin_cert()

        print(f"[+] GoPhish configuration written to {self.config_path}")
        return config

    def _generate_admin_cert(self):
        """Generate self-signed cert for GoPhish admin UI."""
        domain = self.forsake.domain or "forsake.local"
        subj = f"/C=US/ST=State/L=City/O=Forsake/CN={domain}"
        cmd = (
            f'openssl req -x509 -nodes -days 365 -newkey rsa:2048 '
            f'-keyout {cfg.CERTS_DIR / "gophish_admin.key"} '
            f'-out {cfg.CERTS_DIR / "gophish_admin.crt"} '
            f'-subj "{subj}"'
        )
        rc, out, err = run_command(cmd)
        if rc != 0:
            raise RuntimeError(f"Admin cert generation failed: {err}")

    # ─── GoPhish API ──────────────────────────────────────────────────────

    def api_request(self, method: str, endpoint: str, data: dict = None) -> Optional[dict]:
        """Make an authenticated request to the GoPhish API."""
        import urllib.request as req_lib

        api_key = self.forsake.api_key
        if not api_key:
            config = self.forsake.load_config()
            api_key = config.get("api_key") if config else None
            if api_key:
                self.forsake.api_key = api_key

        if not api_key:
            raise RuntimeError("No GoPhish API key available")

        url = f"https://{cfg.GOPHISH_LISTEN_IP}:{cfg.GOPHISH_PORT}/api/{endpoint}/"
        headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        }

        req = req_lib.Request(url, headers=headers, method=method)
        if data:
            req.data = json.dumps(data).encode()

        ctx = ssl._create_unverified_context()
        try:
            with req_lib.urlopen(req, context=ctx) as resp:
                return json.loads(resp.read().decode())
        except req_lib.HTTPError as e:
            print(f"[-] GoPhish API error ({endpoint}): {e.code} - {e.read().decode()}")
            return None
        except Exception as e:
            print(f"[-] GoPhish API request failed: {e}")
            return None

    def get_campaigns(self) -> list:
        """Get all campaigns from GoPhish."""
        result = self.api_request("GET", "campaigns")
        return result if result else []

    def get_campaign(self, campaign_id: int) -> Optional[dict]:
        """Get a specific campaign by ID."""
        return self.api_request("GET", f"campaigns/{campaign_id}")

    def create_campaign(self, name: str, template_id: int, page_id: int,
                        smtp_id: int, group_ids: list,
                        launch_date: str = None) -> Optional[dict]:
        """Create a new campaign."""
        data = {
            "name": name,
            "template": {"id": template_id},
            "page": {"id": page_id},
            "smtp": {"id": smtp_id},
            "groups": [{"id": gid} for gid in group_ids],
        }
        if launch_date:
            data["launch_date"] = launch_date
        else:
            data["launch_date"] = "immediate"

        return self.api_request("POST", "campaigns", data)

    def launch_campaign(self, campaign_id: int) -> Optional[dict]:
        """Launch a campaign immediately."""
        return self.api_request("POST", f"campaigns/{campaign_id}/launch")

    def delete_campaign(self, campaign_id: int) -> bool:
        """Delete a campaign."""
        result = self.api_request("DELETE", f"campaigns/{campaign_id}")
        return result is not None

    def get_templates(self) -> list:
        """Get all email templates."""
        result = self.api_request("GET", "templates")
        return result if result else []

    def get_pages(self) -> list:
        """Get all landing pages."""
        result = self.api_request("GET", "pages")
        return result if result else []

    def get_smtp_profiles(self) -> list:
        """Get all SMTP sending profiles."""
        result = self.api_request("GET", "smtp")
        return result if result else []

    def get_groups(self) -> list:
        """Get all target groups."""
        result = self.api_request("GET", "groups")
        return result if result else []

    def get_dashboard_stats(self) -> dict:
        """Get aggregated dashboard statistics."""
        campaigns = self.get_campaigns()
        if not campaigns:
            return {"total_campaigns": 0, "total_sent": 0, "total_opened": 0,
                    "total_clicked": 0, "total_submitted": 0, "total_reported": 0}

        total_sent = total_opened = total_clicked = total_submitted = total_reported = 0

        for c in campaigns:
            for r in c.get("results", []):
                status = r.get("status", "")
                if status == "Email Sent":
                    total_sent += 1
                if r.get("opened_at"):
                    total_opened += 1
                if r.get("clicked_at"):
                    total_clicked += 1
                if r.get("submitted_data"):
                    total_submitted += 1

            timeline = c.get("timeline", [])
            for event in timeline:
                if event.get("message") == "Email Reported":
                    total_reported += 1

        return {
            "total_campaigns": len(campaigns),
            "total_sent": total_sent,
            "total_opened": total_opened,
            "total_clicked": total_clicked,
            "total_submitted": total_submitted,
            "total_reported": total_reported,
      }
