#!/usr/bin/env bash
set -euo pipefail
rm -f data/sentrix.db data/sentrix.db-wal data/sentrix.db-shm
cp -f data/demo/demo.db data/sentrix.db 2>/dev/null || true
echo "[reset] live DB wiped; demo DB restored if present."
