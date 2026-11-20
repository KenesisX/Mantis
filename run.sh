#!/usr/bin/env bash
# MANTIS launcher
cd "$(dirname "$0")"
PY="$(command -v python3 || command -v python)"
if [ -z "$PY" ]; then echo "Python 3.8+ is required."; exit 1; fi
exec "$PY" -m mantis "${@:-web}"
