#!/bin/bash

# Pronounce Web - VPS Setup Script
# Run as root on Ubuntu 22.04+

set -e # Exit on error

# Configuration
APP_DIR="/var/www/pronounce-web"
USER="root" # Running as root for simplicity on VPS, can be changed to 'www-data' or specific user
VENV_DIR="$APP_DIR/venv"
DOMAIN="" # Will ask user

echo "=========================================="
echo "   Pronounce Web - VPS Auto Installer     "
echo "=========================================="

# 1. Ask for Domain
read -p "Enter Domain Name (or IP address if local): " DOMAIN

# 2. Update System
echo "[*] Updating APT packages..."
apt-get update && apt-get upgrade -y

# 3. Install Dependencies
echo "[*] Installing Python, FFmpeg, Nginx, Certbot..."
apt-get install -y python3-pip python3-venv python3-dev build-essential libssl-dev libffi-dev nginx ffmpeg certbot python3-certbot-nginx

# 4. Setup Python Environment
echo "[*] Setting up Python Virtual Environment..."
if [ ! -d "$VENV_DIR" ]; then
    python3 -m venv "$VENV_DIR"
fi

source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install -r "$APP_DIR/requirements.txt"
pip install gunicorn

# 5. Create Systemd Service
echo "[*] Creating Gunicorn Service..."
cat > /etc/systemd/system/pronounce-web.service <<EOF
[Unit]
Description=Gunicorn instance to serve Pronounce Web
After=network.target

[Service]
User=$USER
Group=www-data
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="DATABASE_URL=sqlite:///$APP_DIR/instance/pronounce.db"
Environment="SECRET_KEY=$(openssl rand -hex 32)"
ExecStart=$VENV_DIR/bin/gunicorn --workers 3 --bind unix:pronounce-web.sock -m 007 wsgi:app

[Install]
WantedBy=multi-user.target
EOF

# 6. Configure Nginx
echo "[*] Configuring Nginx Proxy..."
cat > /etc/nginx/sites-available/pronounce-web <<EOF
server {
    listen 80;
    server_name $DOMAIN;

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/pronounce-web.sock;
    }

    # Increase upload size for audio files
    client_max_body_size 10M;
}
EOF

ln -sf /etc/nginx/sites-available/pronounce-web /etc/nginx/sites-enabled
rm -f /etc/nginx/sites-enabled/default

# 7. Setup Security (UFW)
echo "[*] Configuring Firewall (UFW)..."
ufw allow 'Nginx Full'
ufw allow 'OpenSSH'
echo "y" | ufw enable

# 8. Start Services
echo "[*] Starting Services..."
systemctl daemon-reload
systemctl start pronounce-web
systemctl enable pronounce-web
systemctl restart nginx

# 9. SSL Setup (Optional)
echo ""
read -p "Do you want to setup SSL (HTTPS) with Certbot? (y/n): " SSL_CHOICE
if [[ "$SSL_CHOICE" == "y" || "$SSL_CHOICE" == "Y" ]]; then
    certbot --nginx -d $DOMAIN
fi

echo "=========================================="
echo "   Deployment Complete!                   "
echo "   Visit: http://$DOMAIN                  "
echo "=========================================="
