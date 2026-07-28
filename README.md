<p align="center">
  <img src="image-4.jpg" alt="FORSAKE Logo" width="200" />
</p>

# ☠ FORSAKE — Phishing Engagement Framework

<p align="center">
  <img src="https://img.shields.io/badge/Status-Combat_Ready-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/GoPhish-0.12.1-cyan?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-crimson?style=for-the-badge" />
</p>

<p align="center">
  <strong>Weaponized phishing orchestration — GoPhish + NGINX, hardened, automated, and dashboard-driven.</strong><br>
  <code>Authorized red-team operations only.</code>
</p>

---

## ⚡ Arsenal

| Capability | Execution |
|------------|-----------|
| **Phishing Engine** | GoPhish v0.12.1 — campaign lifecycle management |
| **Reverse Proxy** | NGINX with TLS 1.3, HSTS, WAF rules, header stripping |
| **SSL Automation** | Let's Encrypt via acme.sh — auto-renewal, zero-touch |
| **Landing Cloning** | wget mirror + automatic tracking payload injection |
| **C2 Dashboard** | Cyberpunk-styled FastAPI UI — real-time telemetry |
| **Evasion Suite** | Header spoofing, bot blocking, randomized Server signatures |
| **Admin Isolation** | Separate subdomain with aggressive rate-limiting |
| **SIEM-Ready Logs** | Structured JSON logging with upstream timing metrics |
| **Dual Interface** | CLI + WebUI — full control from either front |
| **WebSocket Push** | Live dashboard updates without polling |
| **1-Command Deploy** | `curl \| bash` — operational in 90 seconds |
| **Clean Kill** | Full teardown — services, configs, optional data purge |

---

## 🚀 Deployment

### Instant (as root)

```bash
curl -fsSL https://raw.githubusercontent.com/anonymous-beta/Forsake/main/install.sh | sudo bash
```

Manual

```bash
git clone https://github.com/anonymous-beta/Forsake.git
cd Forsake
sudo ./install.sh
```

Post-Install

```bash
sudo systemctl enable --now forsake-web
# → https://localhost:8443 | admin / forsake
```

---

🎯 Operational Commands

```bash
# Deploy campaign infrastructure
forsake deploy --domain phish.yourdomain.com --email admin@yourdomain.com

# Clone a target landing page
forsake deploy --domain phish.example.com --clone https://login.target.com

# Generate hardened NGINX config only
forsake nginx --domain phish.example.com --output ./phish.conf

# Clone without deployment
forsake clone --url https://login.target.com --name target_portal

# Status check
forsake status

# Launch dashboard
forsake serve --port 8443

# Scorched-earth teardown
forsake teardown --remove-data
```

Dashboard Shortcuts

Key Action
 `  Toggle terminal overlay
d Dashboard
c Campaigns
p Deploy
l Landing Pages
r Resources
a Audit Log

---

🏗 Architecture

```
         ┌─────────────────┐
         │   Internet      │
         │  :80 / :443     │
         └────────┬────────┘
                  │
         ┌────────▼────────┐
         │   NGINX         │
         │  (Hardened)     │
         └──┬──────────┬───┘
            │          │
   ┌────────▼──┐  ┌───▼────────┐
   │ GoPhish   │  │ Landing    │
   │ :3333     │  │ Pages      │
   └───────────┘  └────────────┘
   
   ┌──────────────────────────────┐
   │ Forsake Dashboard (FastAPI)  │
   │ Port 8443                    │
   └──────────────────────────────┘
```

---

🔒 Hardening Profile

Control Implementation
TLS 1.2/1.3 only — legacy protocols rejected
HSTS 2-year preload with subdomain coverage
Rate Limiting Per-IP throttling across all endpoints
Payload Limits Request size caps — buffer overflow mitigation
Scanner Blocking curl/wget/python/nmap/sqlmap UA rejection
Path Blacklist .git, .env, /admin blocked at proxy
Header Sanitization NGINX version + X-Gophish-* stripped
Server Obfuscation Rotating Server header signatures
Admin Segregation Separate subdomain, stricter limits

---

📊 Dashboard Features

· Matrix rain animated background
· Glitch text + scanline overlay effects
· Live stats: campaigns, sent, opened, clicked, credentials
· Campaign table with status badges
· One-click deploy/teardown from UI
· Landing page cloner with injection
· Resource browser: templates, pages, SMTP, groups
· Full audit log with event history
· Embedded terminal overlay

---

⚖️ Legal Binding

```
FORSAKE is a red-team tool for AUTHORIZED security professionals ONLY.

Acceptance of this software constitutes agreement to:
1. Possess explicit written authorization to test all target systems
2. Comply with all applicable laws and regulations
3. Hold authors harmless for unauthorized use or collateral damage

Unauthorized access is a federal crime. Use accordingly.
```

---

☠ Author

ANONYMOUS-BETA
GitHub · Repository

---

<p align="center">
  <strong>☠ FORSAKE v2.0.0 — by ANONYMOUS-BETA ☠</strong>
</p>
