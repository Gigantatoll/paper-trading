#!/bin/bash
# Pulls latest data from GitHub and refreshes the "📊 Live Trading Data" folder.
# Runs automatically every 10 minutes via macOS LaunchAgent.

REPO="/Users/vincent/Desktop/paper_trading"
DEST="/Users/vincent/Desktop/paper_trading/📊 Live Trading Data"

echo "=== Sync started at $(date) ==="

# Pull latest from GitHub
cd "$REPO"
git pull origin main --quiet

# Create the output folder
mkdir -p "$DEST"

# Copy the key files with readable names
cp "$REPO/data/trades.csv"        "$DEST/All Trades.csv"          2>/dev/null || true
cp "$REPO/data/snapshots.json"    "$DEST/Portfolio Snapshots.json" 2>/dev/null || true

# Generate a plain-English summary
python3 "$REPO/summary.py" > "$DEST/Summary.txt" 2>/dev/null || true

echo "✓ Sync complete — files updated in: $DEST"
echo "=== Done at $(date) ==="
