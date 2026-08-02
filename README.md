<p align="center">
  <img src="image-4.jpg" alt="Forsake Banner" width="600">
</p>

<h1 align="center">☠ FORSAKE ☠</h1>

<p align="center">
  <strong>Weaponized Phishing Orchestration — GoPhish + NGINX, Hardened, Automated, and Dashboard-Driven</strong><br>
  <code>Authorized Red-Team Operations Only</code>
</p>

<p align="center">
  <a href="https://github.com/anonymous-beta/Forsake/releases"><img src="https://img.shields.io/badge/version-2.0.0-red?style=for-the-badge"></a>
  <a href="https://github.com/anonymous-beta/Forsake/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-black?style=for-the-badge"></a>
  <a href="https://www.python.org/downloads/"><img src="https://img.shields.io/badge/python-3.8%2B-blue?style=for-the-badge"></a>
  <a href="https://fastapi.tiangolo.com/"><img src="https://img.shields.io/badge/FastAPI-0.100%2B-teal?style=for-the-badge"></a>
</p>

---

## ⚡ Arsenal

| Capability | Execution |
|------------|-----------|
| **Phishing Engine** | GoPhish v0.12.1 — campaign lifecycle management |
| **Reverse Proxy** | NGINX with TLS 1.3, HSTS, WAF rules, header stripping |
| **SSL Automation** | Let's Encrypt via acme.sh — auto-renewal, zero-touch |
| **Landing Cloning** | `wget` mirror + automatic tracking payload injection |
| **C2 Dashboard** | Cyberpunk-styled FastAPI UI — real-time telemetry |
| **Evasion Suite** | Header spoofing, bot blocking, randomized Server signatures |
| **Admin Isolation** | Separate subdomain with aggressive rate-limiting |
| **SIEM-Ready Logs** | Structured JSON logging with upstream timing metrics |
| **Dual Interface** | CLI + WebUI — full control from either front |
| **WebSocket Push** | Live dashboard updates without polling |
| **1-Command Deploy** | `curl | bash` — operational in 90 seconds |
| **Clean Kill** | Full teardown — services, configs, optional data purge |

---

## 🚀 Deployment

### ⚡ Instant (as root)

```bash
curl -fsSL https://raw.githubusercontent.com/anonymous-beta/Forsake/main/install.sh | sudo bash
```

### 🛠 Manual

```bash
git clone https://github.com/anonymous-beta/Forsake.git
cd Forsake
sudo ./install.sh
```

### 🎛 Post-Install

```bash
sudo systemctl enable --now forsake-web
# → http://localhost:8443 | admin / forsake
```

---

## 🎯 Operational Commands

### CLI Reference

```bash
# Full campaign infrastructure deployment
forsake deploy --domain phish.yourdomain.com --email admin@yourdomain.com

# Deploy with landing page cloning
forsake deploy --domain phish.example.com --clone https://login.target.com

# Generate hardened NGINX config only
forsake nginx --domain phish.example.com --output ./phish.conf

# Clone a landing page without deploying
forsake clone --url https://login.target.com --name target_portal

# Check deployment status
forsake status

# Start the web dashboard manually
forsake serve --port 8443

# Scorched-earth teardown (keeps data)
forsake teardown

# Scorched-earth teardown (removes everything)
forsake teardown --remove-data
```

### CLI Flags

| Command | Flag | Description |
|---------|------|-------------|
| `deploy` | `--domain` | **Required.** Phishing domain |
| `deploy` | `--email` | Email for Let's Encrypt ACME |
| `deploy` | `--admin-pass` | Custom admin password |
| `deploy` | `--clone` | URL to clone as landing page |
| `deploy` | `--smtp` | SMTP relay host:port |
| `nginx` | `--domain` | **Required.** Phishing domain |
| `nginx` | `--output` | Write config to file instead of installing |
| `clone` | `--url` | **Required.** Target URL to clone |
| `clone` | `--name` | Output directory name |
| `serve` | `--host` | Bind address (default: `0.0.0.0`) |
| `serve` | `--port` | Bind port (default: `8443`) |
| `serve` | `--ssl-cert` | Path to SSL certificate |
| `serve` | `--ssl-key` | Path to SSL private key |
| `teardown` | `--remove-data` | Delete all Forsake data permanently |

### Global Flags

```bash
forsake --base-dir /custom/path <command>
```

### Dashboard Shortcuts

| Key | Action |
|-----|--------|
| `` ` `` | Toggle terminal overlay |
| `d` | Dashboard |
| `c` | Campaigns |
| `p` | Deploy |
| `l` | Landing Pages |
| `r` | Resources |
| `a` | Audit Log |

---

## 🏗 Architecture

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

### Component Map

| Component | Port | Purpose |
|-----------|------|---------|
| NGINX | `80` / `443` | Public-facing reverse proxy |
| GoPhish Admin | `3333` (localhost) | Campaign management API & UI |
| GoPhish Phish | `8080` (localhost) | Phishing page delivery |
| Forsake Dashboard | `8443` | C2 Web UI & REST API |

---

## 🔒 Hardening Profile

| Control | Implementation |
|---------|----------------|
| **TLS** | TLS 1.2/1.3 only — legacy protocols rejected |
| **HSTS** | 2-year preload with subdomain coverage |
| **Rate Limiting** | Per-IP throttling across all endpoints |
| **Payload Limits** | Request size caps — buffer overflow mitigation |
| **Scanner Blocking** | `curl`/`wget`/`python`/`nmap`/`sqlmap` UA rejection |
| **Path Blacklist** | `.git`, `.env`, `/admin` blocked at proxy |
| **Header Sanitization** | NGINX version + `X-Gophish-*` stripped |
| **Server Obfuscation** | Rotating Server header signatures |
| **Admin Segregation** | Separate subdomain, stricter limits |

---

## 📊 Dashboard Features

- 🌧 Matrix rain animated background
- ⚡ Glitch text + scanline overlay effects
- 📈 Live stats: campaigns, sent, opened, clicked, credentials
- 📋 Campaign table with status badges
- 🚀 One-click deploy/teardown from UI
- 🕸 Landing page cloner with injection
- 📁 Resource browser: templates, pages, SMTP, groups
- 📜 Full audit log with event history
- 💻 Embedded terminal overlay

---

## 📁 Project Structure

```
Forsake/
├── install.sh              # One-shot installer
├── forsake.py              # CLI entrypoint
├── forsake_server.py       # Dashboard server entrypoint
├── requirements.txt        # Python dependencies
├── Dockerfile              # Container build
├── docker-compose.yml      # Container orchestration
├── forsake/                # Core package
│   ├── __init__.py
│   ├── config.py           # Global configuration
│   ├── core.py             # Main orchestration engine
│   ├── api.py              # FastAPI REST & WebSocket routes
│   ├── database.py         # SQLite session & audit backend
│   ├── gophish_module.py   # GoPhish install, config, API wrapper
│   ├── nginx_module.py     # NGINX config generator & deployer
│   ├── ssl_module.py       # acme.sh & self-signed cert manager
│   ├── clone_module.py     # wget cloner + tracking injector
│   └── utils.py            # Passwords, hashing, helpers
├── web/                    # Frontend assets
│   ├── index.html
│   ├── css/
│   └── js/
└── .github/workflows/
    └── ci.yml              # GitHub Actions CI
```

---

## 🐳 Docker Deployment

```bash
# Build & run
docker-compose up -d

# View logs
docker-compose logs -f forsake

# Shell into container
docker-compose exec forsake bash
```

---

## 🔧 Configuration

Edit `forsake/config.py` before deployment:

| Variable | Default | Description |
|----------|---------|-------------|
| `BASE_DIR` | `/opt/forsake` | Installation root |
| `GOPHISH_VERSION` | `0.12.1` | GoPhish binary version |
| `GOPHISH_PORT` | `3333` | GoPhish admin bind port |
| `GOPHISH_PHISH_PORT` | `8080` | GoPhish phishing bind port |
| `WEB_HOST` | `0.0.0.0` | Dashboard bind address |
| `WEB_PORT` | `8443` | Dashboard bind port |
| `SESSION_DURATION_HOURS` | `8` | Web session TTL |
| `MAX_LOGIN_ATTEMPTS` | `5` | Failed logins before lockout |
| `LOCKOUT_DURATION_MINUTES` | `15` | Lockout duration |

---

## 🧪 API Endpoints

| Method | Endpoint | Description | Auth |
|--------|----------|-------------|------|
| `POST` | `/api/auth/login` | Authenticate & get token | ❌ |
| `POST` | `/api/auth/logout` | Invalidate session | ✅ |
| `GET` | `/api/auth/verify` | Check token validity | ✅ |
| `GET` | `/api/dashboard/stats` | Aggregated stats + recent campaigns | ✅ |
| `GET` | `/api/campaigns` | List all campaigns | ✅ |
| `GET` | `/api/campaigns/{id}` | Get campaign details | ✅ |
| `POST` | `/api/campaigns` | Create new campaign | ✅ |
| `DELETE` | `/api/campaigns/{id}` | Delete campaign | ✅ |
| `POST` | `/api/deploy` | Trigger deployment | ✅ |
| `POST` | `/api/teardown` | Trigger teardown | ✅ |
| `GET` | `/api/status` | Deployment status | ✅ |
| `GET` | `/api/landing-pages` | List cloned pages | ✅ |
| `POST` | `/api/landing-pages/clone` | Clone a page | ✅ |
| `GET` | `/api/resources/templates` | GoPhish templates | ✅ |
| `GET` | `/api/resources/pages` | GoPhish pages | ✅ |
| `GET` | `/api/resources/smtp` | GoPhish SMTP profiles | ✅ |
| `GET` | `/api/resources/groups` | GoPhish groups | ✅ |
| `GET` | `/api/audit-log` | Audit trail | ✅ |
| `WS` | `/api/ws?token={jwt}` | Real-time updates | ✅ |

---

## 🔄 CI/CD

GitHub Actions workflow (`.github/workflows/ci.yml`):

- ✅ Linting (`flake8`, `black`)
- ✅ Unit tests (`pytest`)
- ✅ Docker build verification
- ✅ Security scan (`bandit`)

---

## ⚖️ Legal Binding

```
FORSAKE is a red-team tool for AUTHORIZED security professionals ONLY.

Acceptance of this software constitutes agreement to:
1. Possess explicit written authorization to test all target systems
2. Comply with all applicable laws and regulations
3. Hold authors harmless for unauthorized use or collateral damage

Unauthorized access is a federal crime. Use accordingly.
```

---

## ☠ Author

**ANONYMOUS-BETA**
- [GitHub](https://github.com/anonymous-beta)
- [Repository](https://github.com/anonymous-beta/Forsake)

---

<p align="center">
  <strong>☠ FORSAKE v2.0.0 — by ANONYMOUS-BETA ☠</strong>
</p>
