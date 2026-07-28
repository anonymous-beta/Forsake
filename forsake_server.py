#!/usr/bin/env python3
"""
Forsake Web Server — FastAPI backend with the C2 dashboard.
Created by ANONYMOUS-BETA
https://github.com/anonymous-beta/Forsake

Usage:
    python3 forsake_server.py [--port 8443] [--host 0.0.0.0]
    
    Then open https://localhost:8443 in your browser.
    Default credentials: admin / forsake (change on first login)
"""

import os
import sys
import argparse
import uvicorn
from pathlib import Path

# Ensure package is importable
sys.path.insert(0, str(Path(__file__).parent))

from forsake.config import WEB_HOST, WEB_PORT
from forsake.database import ForsakeDB
from forsake.utils import generate_password


def bootstrap():
    """Create default admin user if none exists."""
    db = ForsakeDB()
    try:
        default_pass = "forsake"
        db.create_user("admin", default_pass)
        print(f"[+] Default admin user created: admin / {default_pass}")
        print("[!] CHANGE THIS PASSWORD IMMEDIATELY AFTER LOGIN!")
    except ValueError:
        pass  # User already exists


def main():
    parser = argparse.ArgumentParser(
        description="Forsake — C2 Web Dashboard",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--host", default=WEB_HOST, help="Bind address")
    parser.add_argument("--port", type=int, default=WEB_PORT, help="Bind port")
    parser.add_argument("--ssl-cert", help="Path to SSL cert (optional)")
    parser.add_argument("--ssl-key", help="Path to SSL key (optional)")
    parser.add_argument("--debug", action="store_true", help="Debug mode")

    args = parser.parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║               FORSAKE COMMAND & CONTROL v2                  ║
║     GoPhish + NGINX Superpower Phishing Toolkit             ║
║               Created by ANONYMOUS-BETA                     ║
╚══════════════════════════════════════════════════════════════╝
    """)

    # Bootstrap default user
    bootstrap()

    ssl_certfile = args.ssl_cert
    ssl_keyfile = args.ssl_key

    scheme = "https" if ssl_certfile else "http"
    print(f"[*] Dashboard: {scheme}://{args.host}:{args.port}")
    print(f"[*] API Docs:  {scheme}://{args.host}:{args.port}/api/docs")
    print(f"[*] Press Ctrl+C to stop\n")

    uvicorn.run(
        "forsake.api:app",
        host=args.host,
        port=args.port,
        reload=args.debug,
        ssl_certfile=ssl_certfile,
        ssl_keyfile=ssl_keyfile,
        log_level="info" if not args.debug else "debug",
    )


if __name__ == "__main__":
    main()
