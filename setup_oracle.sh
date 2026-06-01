#!/bin/bash
# -----------------------------------------------------------------------------
# setup_oracle.sh — TransferRadar AI
# -----------------------------------------------------------------------------
# Highly automated setup script to deploy the Telegram bot on an Oracle Cloud
# Always Free Ubuntu VM instance. Runs the bot 24/7 as a systemd service.
# -----------------------------------------------------------------------------

set -e

# Color definitions
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}===================================================================${NC}"
echo -e "${GREEN}          TransferRadar AI — Oracle Cloud Always Free Deployer      ${NC}"
echo -e "${BLUE}===================================================================${NC}"

# Check if script is run as root
if [ "$EUID" -ne 0 ]; then
  echo -e "${RED}❌ Please run this script with sudo:${NC}"
  echo -e "${YELLOW}sudo bash $0${NC}"
  exit 1
fi

# 1. Update and install packages
echo -e "\n${YELLOW}🔄 Step 1: Updating system packages and installing dependencies...${NC}"
apt update && apt upgrade -y
apt install -y git python3 python3-pip python3-venv sqlite3 build-essential

# 2. Setup user and directories
echo -e "\n${YELLOW}📁 Step 2: Preparing folder structure...${NC}"
INSTALL_DIR="/opt/transferradar-ai"
mkdir -p "$INSTALL_DIR"
cd "$INSTALL_DIR"

# 3. Clone Repository
echo -e "\n${YELLOW}📥 Step 3: Fetching codebase from GitHub...${NC}"
if [ -d "$INSTALL_DIR/.git" ]; then
  echo -e "${GREEN}Codebase directory already exists. Pulling latest changes...${NC}"
  git pull origin main || true
else
  echo -e "${YELLOW}Please paste your GitHub Repository URL (or press Enter for default):${NC}"
  read -r REPO_URL
  if [ -z "$REPO_URL" ]; then
    REPO_URL="https://github.com/Kenacoder/transferradar-ai.git"
  fi
  git clone "$REPO_URL" .
fi

# 4. Create Virtual Environment
echo -e "\n${YELLOW}🐍 Step 4: Creating Python virtual environment...${NC}"
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt

# 5. Setup Environment Variables
echo -e "\n${YELLOW}⚙️ Step 5: Configuring environment variables...${NC}"
ENV_FILE="$INSTALL_DIR/.env"

if [ -f "$ENV_FILE" ]; then
  echo -e "${GREEN}Existing .env file detected.${NC}"
else
  echo -e "${YELLOW}Please enter your TELEGRAM_TOKEN:${NC}"
  read -r TELEGRAM_TOKEN
  while [ -z "$TELEGRAM_TOKEN" ]; do
    echo -e "${RED}TELEGRAM_TOKEN cannot be empty. Please enter your token:${NC}"
    read -r TELEGRAM_TOKEN
  done

  echo -e "${YELLOW}Please enter your GEMINI_API_KEY:${NC}"
  read -r GEMINI_API_KEY
  while [ -z "$GEMINI_API_KEY" ]; do
    echo -e "${RED}GEMINI_API_KEY cannot be empty. Please enter your key:${NC}"
    read -r GEMINI_API_KEY
  done

  cat <<EOF > "$ENV_FILE"
# ─── Credentials ───────────────────────────────────────────────────────────────
TELEGRAM_TOKEN=$TELEGRAM_TOKEN
GEMINI_API_KEY=$GEMINI_API_KEY
EOF
  echo -e "${GREEN}✅ .env file created at $ENV_FILE${NC}"
fi

# Ensure correct folder permissions
chown -R ubuntu:ubuntu "$INSTALL_DIR"
chmod 600 "$ENV_FILE"

# 6. Create systemd Service
echo -e "\n${YELLOW}🛡️ Step 6: Registering systemd system service...${NC}"
SERVICE_FILE="/etc/systemd/system/transferradar.service"

cat <<EOF > "$SERVICE_FILE"
[Unit]
Description=TransferRadar AI - 24/7 Telegram Bot & Scheduler
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=$INSTALL_DIR
EnvironmentFile=$ENV_FILE
ExecStart=$INSTALL_DIR/venv/bin/python3 main.py
Restart=on-failure
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

echo -e "\n${YELLOW}🚀 Starting and enabling TransferRadar AI...${NC}"
systemctl daemon-reload
systemctl enable transferradar.service
systemctl restart transferradar.service

echo -e "\n${BLUE}===================================================================${NC}"
echo -e "${GREEN}🎉 CONGRATULATIONS! Deploy Completed Successfully!${NC}"
echo -e "${BLUE}===================================================================${NC}"
echo -e "Your bot is now running continuously in the background on Oracle Cloud."
echo -e "Here are useful command utilities for maintenance:"
echo -e ""
echo -e "🔹 ${YELLOW}Check bot status:${NC}"
echo -e "   sudo systemctl status transferradar"
echo -e ""
echo -e "🔹 ${YELLOW}Restart the bot:${NC}"
echo -e "   sudo systemctl restart transferradar"
echo -e ""
echo -e "🔹 ${YELLOW}View live logs:${NC}"
echo -e "   sudo journalctl -u transferradar -f"
echo -e ""
echo -e "🔹 ${YELLOW}Stop the bot:${NC}"
echo -e "   sudo systemctl stop transferradar"
echo -e "${BLUE}===================================================================${NC}"
