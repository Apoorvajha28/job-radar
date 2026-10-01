#!/bin/bash
# Install (or reinstall) the job-radar launchd agent.
# Usage: bash scripts/install_launchd.sh [INTERVAL_SECONDS]
#   e.g. bash scripts/install_launchd.sh 1800   # every 30 min
#        bash scripts/install_launchd.sh         # default: 3600 = hourly
set -euo pipefail

INTERVAL="${1:-3600}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LABEL="com.jobradar.agent"
DEST="$HOME/Library/LaunchAgents/$LABEL.plist"

mkdir -p "$HOME/Library/LaunchAgents" "$HERE/data"

# Template the project path and interval into the plist.
sed -e "s|__PROJECT_DIR__|$HERE|g" -e "s|__INTERVAL__|$INTERVAL|g" \
    "$HERE/scripts/$LABEL.plist" > "$DEST"

# Reload if already present.
launchctl unload "$DEST" 2>/dev/null || true
launchctl load "$DEST"

echo "Installed and loaded: $DEST  (every ${INTERVAL}s)"
echo "It runs now and on that interval. Tail the log with:"
echo "  tail -f \"$HERE/data/jobradar.log\""
echo
echo "To stop it:   launchctl unload \"$DEST\""
echo "To remove it: launchctl unload \"$DEST\" && rm \"$DEST\""
