#!/usr/bin/env python3
"""
╔══════════════════════════════════════════════════════════════╗
║                   FORSAKE v2.0.0                            ║
║  GoPhish + NGINX Superpower Phishing Engagement Toolkit     ║
║  Created by ANONYMOUS-BETA                                  ║
║  https://github.com/anonymous-beta/Forsake                  ║
╚══════════════════════════════════════════════════════════════╝
"""

import sys
import argparse
from pathlib import Path

# Add parent to path for direct execution
sys.path.insert(0, str(Path(__file__).parent))

from forsake.core import Forsake
from forsake import __version__, __author__


def banner():
    print(f"""
{'='*60}
  ███████╗ ██████╗ ██████╗ ███████╗ █████╗ ██╗  ██╗███████╗
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔════╝
  █████╗  ██║   ██║██████╔╝███████╗███████║█████╔╝ █████╗  
  ██╔══╝  ██║   ██║██╔══██╗╚════██║██╔══██║██╔═██╗ ██╔══╝  
  ██║     ╚██████╔╝██║  ██║███████║██║  ██║██║  ██╗███████╗
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
  v{__version__} — by {__author__}
{'='*60}
""")


def main():
    parser = argparse.ArgumentParser(
        description="Forsake — GoPhish + NGINX Superpower Phishing Toolkit",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  forsake deploy --domain phish.example.com --email admin@example.com
  forsake deploy --domain phish.example.com --clone https://login.target.com
  forsake nginx --domain phish.example.com --output ./custom.conf
  forsake clone --url https://login.target.com --name target_portal
  forsake status
  forsake teardown
  forsake teardown --remove-data
        """
    )

    parser.add_argument('--base-dir', default='/opt/forsake',
                       help='Base directory (default: /opt/forsake)')

    subparsers = parser.add_subparsers(dest='command')

    # deploy
    dp = subparsers.add_parser('deploy', help='Full deployment')
    dp.add_argument('--domain', required=True, help='Phishing domain')
    dp.add_argument('--email', help='Email for Let\'s Encrypt')
    dp.add_argument('--admin-pass', help='Admin password')
    dp.add_argument('--clone', help='URL to clone as landing page')
    dp.add_argument('--smtp', help='SMTP relay host:port')

    # nginx
    np = subparsers.add_parser('nginx', help='Generate NGINX config')
    np.add_argument('--domain', required=True, help='Phishing domain')
    np.add_argument('--output', help='Output path')

    # clone
    cp = subparsers.add_parser('clone', help='Clone a landing page')
    cp.add_argument('--url', required=True, help='Target URL')
    cp.add_argument('--name', help='Output name')

    # teardown
    tp = subparsers.add_parser('teardown', help='Remove Forsake')
    tp.add_argument('--remove-data', action='store_true', help='Remove all data')

    # status
    subparsers.add_parser('status', help='Show deployment status')

    # serve
    sp = subparsers.add_parser('serve', help='Start web dashboard')
    sp.add_argument('--host', default='0.0.0.0', help='Bind address')
    sp.add_argument('--port', type=int, default=8443, help='Bind port')
    sp.add_argument('--ssl-cert', help='SSL cert path')
    sp.add_argument('--ssl-key', help='SSL key path')

    args = parser.parse_args()

    if not args.command:
        banner()
        parser.print_help()
        return

    forsake = Forsake(base_dir=args.base_dir)

    if args.command == 'deploy':
        banner()
        result = forsake.deploy(
            domain=args.domain,
            email=args.email,
            admin_password=args.admin_pass,
            clone_url=args.clone,
            smtp_host=args.smtp,
        )
        if result.get('status') == 'error':
            sys.exit(1)

    elif args.command == 'nginx':
        forsake._init_paths()
        config = forsake.nginx.generate_config(args.domain)
        if args.output:
            Path(args.output).write_text(config)
            print(f"[+] Config written to {args.output}")

    elif args.command == 'clone':
        forsake._init_paths()
        path = forsake.cloner.clone(args.url, args.name)
        forsake.cloner.inject_tracking(path)
        print(f"[+] Page cloned to {path}")

    elif args.command == 'teardown':
        banner()
        forsake.teardown(remove_data=args.remove_data)

    elif args.command == 'status':
        status = forsake.status()
        if status.get('status') == 'not_deployed':
            print("\n[!] No Forsake deployment found.\n")
        else:
            print(f"\n  Domain:     {status.get('domain', 'N/A')}")
            print(f"  Status:     {status.get('status', 'N/A')}")
            print(f"  GoPhish:    {'🟢 Running' if status.get('gophish_running') else '🔴 Stopped'}")
            print(f"  NGINX:      {'🟢 Running' if status.get('nginx_running') else '🔴 Stopped'}")
            print(f"  SSL:        {'🟢 Valid' if status.get('certs_valid') else '🔴 Missing'}")
            print(f"  Admin:      {status.get('admin_url', 'N/A')}")
            print(f"  Phishing:   {status.get('phishing_url', 'N/A')}\n")

    elif args.command == 'serve':
        banner()
        print(f"[*] Starting Forsake web dashboard...")
        from forsake_server import main as server_main
        sys.argv = ['forsake-server', '--host', args.host, '--port', str(args.port)]
        if args.ssl_cert:
            sys.argv.extend(['--ssl-cert', args.ssl_cert])
        if args.ssl_key:
            sys.argv.extend(['--ssl-key', args.ssl_key])
        server_main()


if __name__ == "__main__":
    main()
