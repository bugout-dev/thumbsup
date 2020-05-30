#!/usr/bin/env bash

# Requires superuser privileges - use sudo!

set -e

SCRIPT_DIR=$(realpath "$(dirname $0)")
THUMBSUP_DIR=$(dirname "${SCRIPT_DIR}")
SERVICE_FILE="${SCRIPT_DIR}/thumbsup.service"
TOKEN_SERVICE_FILE="${SCRIPT_DIR}/thumbsuptoken.service"
TOKEN_TIMER_FILE="${SCRIPT_DIR}/thumbsuptoken.timer"

echo
echo
echo "Updating Thumbsup codebase at: ${THUMBSUP_DIR}"
git -C "${THUMBSUP_DIR}" checkout master
git -C "${THUMBSUP_DIR}" pull

echo
echo
echo "Replacing existing thumbsuptoken service and timer definitions with: ${TOKEN_SERVICE_FILE}, ${TOKEN_TIMER_FILE}"
chmod 644 "${TOKEN_SERVICE_FILE}" "${TOKEN_TIMER_FILE}"
cp "${TOKEN_SERVICE_FILE}" /etc/systemd/system/thumbsuptoken.service
cp "${TOKEN_TIMER_FILE}" /etc/systemd/system/thumbsuptoken.timer
systemctl daemon-reload
systemctl start thumbsuptoken.timer

echo
echo
echo "Replacing existing thumbsup service definition with: ${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"
cp "${SERVICE_FILE}" /etc/systemd/system/thumbsup.service
systemctl daemon-reload
systemctl restart thumbsup.service
systemctl status thumbsup.service
