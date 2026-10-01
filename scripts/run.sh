#!/bin/bash
# Wrapper launchd (or cron) calls. Runs one pass, appending to a log.
set -euo pipefail
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$HERE"
mkdir -p data
exec ./.venv/bin/python run.py -v >> data/jobradar.log 2>&1
