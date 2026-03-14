#!/usr/bin/env bash
# One-time server setup script.
# Run as root (or with sudo) on the target server.
# Usage: sudo bash deploy/server-setup.sh

set -euo pipefail

PROD_DIR=/opt/asd-analyzer
DEV_DIR=/opt/asd-analyzer-dev
SERVICE_DIR=/etc/systemd/system
APACHE_AVAILABLE=/etc/apache2/sites-available

# ── 1. System packages ────────────────────────────────────────────────────────
apt-get update -q
apt-get install -y python3-venv python3-pip rsync ffmpeg apache2

# Enable Apache proxy modules for Streamlit (HTTP + WebSocket)
a2enmod proxy proxy_http proxy_wstunnel rewrite headers
systemctl reload apache2

# ── 2. App directories ────────────────────────────────────────────────────────
for DIR in "$PROD_DIR" "$DEV_DIR"; do
    mkdir -p "$DIR"/{uploads,processed}
    chown -R www-data:www-data "$DIR"
done

# ── 3. Python virtual environments ───────────────────────────────────────────
# Create venvs owned by www-data
sudo -u www-data python3 -m venv "$PROD_DIR/venv"
sudo -u www-data python3 -m venv "$DEV_DIR/venv"

# ── 4. Systemd services ───────────────────────────────────────────────────────
cp "$(dirname "$0")/asd-analyzer.service"     "$SERVICE_DIR/"
cp "$(dirname "$0")/asd-analyzer-dev.service" "$SERVICE_DIR/"

systemctl daemon-reload
systemctl enable asd-analyzer.service asd-analyzer-dev.service

# ── 5. Sudoers for deploy user ────────────────────────────────────────────────
# Allow the deploy user (DEPLOY_USER from GitHub Actions secret) to restart
# the services without a password. Replace 'deploy' with your actual username.
DEPLOY_USER=${DEPLOY_USER:-deploy}
SUDOERS_FILE=/etc/sudoers.d/asd-analyzer
cat > "$SUDOERS_FILE" <<EOF
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart asd-analyzer.service
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl restart asd-analyzer-dev.service
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl is-active asd-analyzer.service
$DEPLOY_USER ALL=(ALL) NOPASSWD: /bin/systemctl is-active asd-analyzer-dev.service
EOF
chmod 440 "$SUDOERS_FILE"

echo ""
echo "Setup complete. Next steps:"
echo "  1. Copy the app files to $PROD_DIR and $DEV_DIR, then run:"
echo "       \$PROD_DIR/venv/bin/pip install -r \$PROD_DIR/requirements.txt"
echo "       \$DEV_DIR/venv/bin/pip install  -r \$DEV_DIR/requirements.txt"
echo "  2. Add the Apache Location blocks from deploy/apache-asd-analyzer.conf"
echo "     into your existing <VirtualHost *:443> for ns.cht77.com."
echo "  3. systemctl start asd-analyzer.service asd-analyzer-dev.service"
echo "  4. Add GitHub Actions secrets: DEPLOY_HOST, DEPLOY_USER, DEPLOY_SSH_KEY"
