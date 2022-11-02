#!/usr/bin/env sh
set -e

if dtdl-validate -f "$@"; then
    echo "Validation Success"
else
    exit 1
fi
