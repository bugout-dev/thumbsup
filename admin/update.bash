#!/usr/bin/env bash

# Requires superuser privileges - use sudo!

set -e

SCRIPT_DIR=$(dirname $0)
SERVICE_FILE="${SCRIPT_DIR}/thumbsup.service"
echo "Replacing existing thumbsup service definition with: ${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"
mv "${SERVICE_FILE}" /etc/systemd/system/thumbsup.service
systemctl daemon-reload
systemctl restart thumbsup.service
systemctl status thumbsup.service
