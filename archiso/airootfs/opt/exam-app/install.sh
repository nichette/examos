#!/bin/bash
# install.sh - Install the exam application on the target system
# Run as root on the exam OS

set -e
echo "[1/5] Installing Python dependencies..."
pip install python-pam python-gnupg PyGObject --break-system-packages

echo "[2/5] Copying application to /opt/examapp..."
cp -r "$(dirname "$0")" /opt/examapp

echo "[3/5] Setting permissions..."
chmod -R 755 /opt/examapp
chmod +x /opt/examapp/main.py

echo "[4/5] Installing systemd service..."
cp /opt/examapp/examapp.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable examapp@student

echo "[5/5] Creating config directory..."
mkdir -p /etc/examapp
cp /opt/examapp/config.example.json /etc/examapp/config.json

echo "Done. Edit /etc/examapp/config.json then run: systemctl start examapp@student"
