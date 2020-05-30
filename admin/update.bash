#!/usr/bin/env bash

# Requires superuser privileges - use sudo!

set -e

SCRIPT_DIR=$(dirname $0)
echo "Path to new systemd service definition: ${SCRIPT_DIR}/thumbsup.service"
