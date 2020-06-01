#!/usr/bin/env bash

# Requires superuser privileges - use sudo!

set -e

SCRIPT_DIR=$(realpath "$(dirname $0)")
THUMBSUP_DIR=$(dirname "${SCRIPT_DIR}")
SERVICE_FILE="${SCRIPT_DIR}/thumbsup.service"
TOKEN_SERVICE_FILE="${SCRIPT_DIR}/thumbsuptoken.service"
TOKEN_TIMER_FILE="${SCRIPT_DIR}/thumbsuptoken.timer"
DBWRITE_SERVICE_FILE="${SCRIPT_DIR}/thumbsupdbwrite.service"
DBWRITE_TIMER_FILE="${SCRIPT_DIR}/thumbsupdbwrite.timer"

GITHUB_SHA=${1:-master}

echo
echo
echo "Updating Thumbsup codebase at: ${THUMBSUP_DIR} from ${GITHUB_SHA}"
git -C "${THUMBSUP_DIR}" fetch origin
git -C "${THUMBSUP_DIR}" checkout "$GITHUB_SHA"
if [ "$GITHUB_SHA" = "master" ]
then
    git -C "${THUMBSUP_DIR}" pull
fi

echo
echo
echo "Updating Python dependencies"
/home/ubuntu/thumbsup/.thumbsup/bin/pip install -r /home/ubuntu/thumbsup/requirements.txt

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
echo "Replacing existing thumbsupdbwrite service and timer definitions with: ${DBWRITE_SERVICE_FILE}, ${DBWRITE_TIMER_FILE}"
chmod 644 "${DBWRITE_SERVICE_FILE}" "${DBWRITE_TIMER_FILE}"
cp "${DBWRITE_SERVICE_FILE}" /etc/systemd/system/thumbsupdbwrite.service
cp "${DBWRITE_TIMER_FILE}" /etc/systemd/system/thumbsupdbwrite.timer
systemctl daemon-reload
systemctl start thumbsupdbwrite.timer

echo
echo
echo "Replacing existing thumbsup service definition with: ${SERVICE_FILE}"
chmod 644 "${SERVICE_FILE}"
cp "${SERVICE_FILE}" /etc/systemd/system/thumbsup.service
systemctl daemon-reload
systemctl restart thumbsup.service
systemctl status thumbsup.service
