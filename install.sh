#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
# FORSAKE — Automated Installer
# Created by ANONYMOUS-BETA
# https://github.com/anonymous-beta/Forsake
# ═══════════════════════════════════════════════════════════════════════════

set -e

VERSION="2.0.0"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${RED}"
cat << "EOF"
  ███████╗ ██████╗ ██████╗ ███████╗ █████╗ ██╗  ██╗███████╗
  ██╔════╝██╔═══██╗██╔══██╗██╔════╝██╔══██╗██║ ██╔╝██╔════╝
  █████╗  ██║   ██║██████╔╝███████╗███████║█████╔╝ █████╗  
  ██╔══╝  ██║   ██║██╔══██╗╚════██║██╔══██║██╔═██╗ ██╔══╝  
  ██║     ╚██████╔╝██║  ██║███████║██║  ██║██║  ██╗███████╗
  ╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝
EOF
echo -e "${NC}"
echo -e "${CYAN}  Forsake v${VERSION} — GoPhish + NGINX Superpower Toolkit${NC}"
echo -e "${YELLOW}  Created by ANONYMOUS-BETA${NC}"
echo -e "${RED}  Authorized penetration testing use only${NC}"
echo ""

# --- Root Check ---
if [[ $EUID -ne 0 ]]; then
    echo -e "${RED}[!] This installer must be run as root (sudo).${NC}"
    exit 1
fi

# --- Detect OS ---
OS="$(uname -s)"
if [[ "$OS" != "Linux" ]]; then
    echo -e "${RED}[!] Linux is required. Detected: $OS${NC}"
    exit 1
fi

# --- Parse Arguments ---
INSTALL_DIR="/opt/forsake"
SKIP_DEPS=false
DEV_MODE=false

while [[ $# -gt 0 ]]; do
    case "$1" in
        --dir) INSTALL_DIR="$2"; shift 2 ;;
        --skip-deps) SKIP_DEPS=true; shift ;;
        --dev) DEV_MODE=true; shift ;;
        --help)
            echo "Usage: $0 [--dir /path] [--skip-deps] [--dev]"
            echo "  --dir       Installation directory (default: /opt/forsake)"
            echo "  --skip-deps Skip system dependency installation"
            echo "  --dev       Install in development mode (no systemd)"
            exit 0 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

echo -e "${GREEN}[*] Installing Forsake to: ${INSTALL_DIR}${NC}"
echo ""

# --- Install System Dependencies ---
if [[ "$SKIP_DEPS" == "false" ]]; then
    echo -e "${GREEN}[*] Installing system dependencies...${NC}"
    
    if command -v apt &> /dev/null; then
        apt update -qq
        apt install -y -qq nginx curl wget openssl python3 python3-pip python3-venv unzip git
    elif command -v yum &> /dev/null; then
        yum install -y nginx curl wget openssl python3 python3-pip unzip git
    elif command -v dnf &> /dev/null; then
        dnf install -y nginx curl wget openssl python3 python3-pip unzip git
    else
        echo -e "${YELLOW}[!] Unsupported package manager. Install manually: nginx, python3, pip, curl, wget, openssl${NC}"
    fi
    echo -e "${GREEN}[+] System dependencies installed${NC}"
fi

# --- Create Directory Structure ---
echo -e "${GREEN}[*] Creating directory structure...${NC}"
mkdir -p "${INSTALL_DIR}"/{data,gophish,nginx,certs,landing_pages,logs,web/{css,js}}

# --- Install Python Dependencies ---
echo -e "${GREEN}[*] Installing Python dependencies...${NC}"
python3 -m venv "${INSTALL_DIR}/venv"
source "${INSTALL_DIR}/venv/bin/activate"
pip install -q --upgrade pip
pip install -q fastapi uvicorn pydantic
echo -e "${GREEN}[+] Python dependencies installed${NC}"

# --- Copy Source Files ---
echo -e "${GREEN}[*] Installing Forsake source files...${NC}"

# Copy forsake package
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cp -r "${SCRIPT_DIR}/forsake" "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/forsake_server.py" "${INSTALL_DIR}/"
cp "${SCRIPT_DIR}/forsake.py" "${INSTALL_DIR}/"

# Copy web files
cp -r "${SCRIPT_DIR}/web/"* "${INSTALL_DIR}/web/"

# Make executables
chmod +x "${INSTALL_DIR}/forsake.py"
chmod +x "${INSTALL_DIR}/forsake_server.py"

echo -e "${GREEN}[+] Source files installed${NC}"

# --- Create Symlinks ---
echo -e "${GREEN}[*] Creating symlinks...${NC}"
ln -sf "${INSTALL_DIR}/forsake.py" /usr/local/bin/forsake
ln -sf "${INSTALL_DIR}/forsake_server.py" /usr/local/bin/forsake-server

# --- Create Systemd Services ---
if [[ "$DEV_MODE" == "false" ]]; then
    echo -e "${GREEN}[*] Creating systemd services...${NC}"
    
    # Forsake Web Dashboard service
    cat > /etc/systemd/system/forsake-web.service << 'SERVICEEOF'
[Unit]
Description=Forsake Web Dashboard
Documentation=https://github.com/anonymous-beta/Forsake
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=/opt/forsake
ExecStart=/opt/forsake/venv/bin/python /opt/forsake/forsake_server.py
Restart=always
RestartSec=5
StandardOutput=append:/opt/forsake/logs/web.log
StandardError=append:/opt/forsake/logs/web_error.log
LimitNOFILE=65536

[Install]
WantedBy=multi-user.target
SERVICEEOF

    systemctl daemon-reload
    echo -e "${GREEN}[+] Systemd services created${NC}"
    echo -e "${YELLOW}[!] Start with: sudo systemctl enable --now forsake-web${NC}"
fi

# --- Download GoPhish ---
echo -e "${GREEN}[*] Downloading GoPhish v0.12.1...${NC}"
cd "${INSTALL_DIR}/data"
curl -sL "https://github.com/gophish/gophish/releases/download/v0.12.1/gophish-v0.12.1-linux-64bit.zip" -o gophish.zip
unzip -qo gophish.zip -d gophish/
rm -f gophish.zip
chmod +x gophish/gophish
echo -e "${GREEN}[+] GoPhish v0.12.1 downloaded${NC}"

# --- Install acme.sh ---
echo -e "${GREEN}[*] Installing acme.sh...${NC}"
curl -fsSL https://get.acme.sh | sh -s email=admin@forsake.local > /dev/null 2>&1 || true
echo -e "${GREEN}[+] acme.sh installed${NC}"

# --- Summary ---
echo ""
echo -e "${RED}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║               FORSAKE INSTALLATION COMPLETE                 ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Install Dir:${NC}  ${INSTALL_DIR}"
echo -e "  ${CYAN}Dashboard:${NC}    http://localhost:8443"
echo -e "  ${CYAN}CLI:${NC}          forsake --help"
echo ""
echo -e "  ${YELLOW}Quick Start:${NC}"
echo -e "    ${GREEN}1.${NC} Start the dashboard:  sudo systemctl enable --now forsake-web"
echo -e "    ${GREEN}2.${NC} Open browser:          http://localhost:8443"
echo -e "    ${GREEN}3.${NC} Login:                 admin / forsake"
echo -e "    ${GREEN}4.${NC} Deploy:                Use the Deploy tab in the UI"
echo ""
echo -e "  ${YELLOW}Or via CLI:${NC}"
echo -e "    sudo python3 ${INSTALL_DIR}/forsake.py deploy --domain phish.example.com"
echo ""
echo -e "  ${RED}☠ Authorized penetration testing use only${NC}"
echo ""
