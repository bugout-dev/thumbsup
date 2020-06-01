#!/usr/bin/env bash

# Requires superuser privileges - use sudo!

set -e

SCRIPT_DIR=$(realpath "$(dirname $0)")
THUMBSUP_DIR=$(dirname "${SCRIPT_DIR}")

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

bash "${SCRIPT_DIR}"/update.bash
