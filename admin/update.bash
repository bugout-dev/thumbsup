#!/usr/bin/env bash

# Requires superuser privileges - use sudo!

set -e

SCRIPT_DIR=$(realpath $(dirname $0))
THUMBSUP_DIR=$(dirname "${SCRIPT_DIR}")
SERVICE_FILE="${SCRIPT_DIR}/thumbsup.service"

echo "Updating Thumbsup codebase at: ${THUMBSUP_DIR}"
git -C "${THUMBSUP_DIR}" checkout master
git -C "${THUMBSUP_DIR}" pull

echo "Replacing existing thumbsup service definition with: ${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"
cp "${SERVICE_FILE}" /etc/systemd/system/thumbsup.service
systemctl daemon-reload
systemctl restart thumbsup.service
systemctl status thumbsup.service
