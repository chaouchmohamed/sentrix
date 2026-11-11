
#!/usr/bin/env bash
set -Eeuo pipefail

# SENTRIX end-to-end demo:
# Docker -> Cowrie attack -> SENTRIX engine -> SQLite -> Turso

cd "$(dirname "$0")"
ROOT="$PWD"

DB="data/sentrix.db"
COWRIE_LOG="honeypot/cowrie-var/log/cowrie/cowrie.json"
ENGINE_LOG="data/demo/sentrix-live.log"

echo "======================================"
echo "       SENTRIX AUTOMATED DEMO"
echo "======================================"

# 1. Load Turso credentials
if [[ ! -f .env ]]; then
    echo "[ERROR] .env not found"
    exit 1
fi

set -a
source .env
set +a

if [[ -z "${TURSO_DATABASE_URL:-}" || -z "${TURSO_AUTH_TOKEN:-}" ]]; then
    echo "[ERROR] Missing Turso credentials in .env"
    exit 1
fi

# 2. Start Docker containers
echo
echo "[1/5] Starting Cowrie and Kali..."

docker compose up -d cowrie kali

# Wait for Cowrie log
for i in {1..20}; do
    [[ -f "$COWRIE_LOG" ]] && break
    sleep 0.5
done

if [[ ! -f "$COWRIE_LOG" ]]; then
    echo "[ERROR] Cowrie log not found: $COWRIE_LOG"
    exit 1
fi

# 3. Record initial local event count
BASELINE=$(python3 - "$DB" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
print(c.execute("SELECT COUNT(*) FROM events").fetchone()[0])
c.close()
PY
)

echo "[INFO] Initial local events: $BASELINE"

# 4. Start SENTRIX live ingestion
echo
echo "[2/5] Starting SENTRIX live engine..."

mkdir -p data/demo

python3 -m sentrix.main --live "$COWRIE_LOG" \
    > "$ENGINE_LOG" 2>&1 &

ENGINE_PID=$!

cleanup() {
    if kill -0 "$ENGINE_PID" 2>/dev/null; then
        kill "$ENGINE_PID" 2>/dev/null || true
        wait "$ENGINE_PID" 2>/dev/null || true
    fi
}

trap cleanup EXIT INT TERM

sleep 1

if ! kill -0 "$ENGINE_PID" 2>/dev/null; then
    echo "[ERROR] SENTRIX engine failed to start:"
    tail -n 30 "$ENGINE_LOG"
    exit 1
fi

# 5. Generate controlled brute-force attempts against Cowrie
echo
echo "[3/5] Generating SSH brute-force activity..."

docker exec sentrix-kali bash -lc '
    printf "%s\n" \
    "sentrix-demo-wrong-01" \
    "sentrix-demo-wrong-02" \
    "sentrix-demo-wrong-03" \
    "sentrix-demo-wrong-04" \
    "sentrix-demo-wrong-05" \
    "sentrix-demo-wrong-06" \
    "sentrix-demo-wrong-07" \
    "sentrix-demo-wrong-08" \
    "sentrix-demo-wrong-09" \
    "sentrix-demo-wrong-10" \
    "sentrix-demo-wrong-11" \
    "sentrix-demo-wrong-12" \
    > /tmp/sentrix-demo-passwords.txt

    hydra -l root \
      -P /tmp/sentrix-demo-passwords.txt \
      -t 4 -I \
      172.28.0.10 ssh -s 2222
'

# 6. Wait until SENTRIX inserts new events into SQLite
echo
echo "[4/5] Waiting for local database updates..."

UPDATED=0

for i in {1..40}; do
    CURRENT=$(python3 - "$DB" <<'PY'
import sqlite3, sys
c = sqlite3.connect(sys.argv[1])
print(c.execute("SELECT COUNT(*) FROM events").fetchone()[0])
c.close()
PY
)

    if (( CURRENT > BASELINE )); then
        UPDATED=1
        break
    fi

    sleep 0.5
done

if (( UPDATED == 0 )); then
    echo "[ERROR] No new SENTRIX events detected within 20 seconds."
    echo "Engine log:"
    tail -n 30 "$ENGINE_LOG"
    exit 1
fi

echo "[OK] Local events: $BASELINE -> $CURRENT"

# 7. Push SQLite changes to Turso
echo
echo "[5/5] Synchronizing with Turso..."

python3 tools/sentrix_sync.py --once --verbose

# 8. Verify local and remote database counts
echo
echo "======================================"
echo "         DATABASE VERIFICATION"
echo "======================================"

python3 - "$DB" <<'PY'
import sqlite3, sys, os
sys.path.insert(0, "tools")
from sentrix_sync import Remote

db_path = sys.argv[1]
local = sqlite3.connect(db_path)
remote = Remote(
    os.environ["TURSO_DATABASE_URL"],
    os.environ["TURSO_AUTH_TOKEN"]
)

tables = (
    "events",
    "alerts",
    "alert_events",
    "incidents",
    "incident_alerts",
    "actions"
)

all_match = True

print(f"{'TABLE':<18}{'LOCAL':>10}{'TURSO':>10}{'STATUS':>12}")

for table in tables:
    local_count = local.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    remote_count = remote.scalar(
        f"SELECT COUNT(*) FROM {table}"
    )

    status = "MATCH" if local_count == remote_count else "MISMATCH"
    if status != "MATCH":
        all_match = False

    print(f"{table:<18}{local_count:>10}{remote_count:>10}{status:>12}")

local.close()

print()
if all_match:
    print("[SUCCESS] Local SQLite and Turso are synchronized.")
else:
    print("[WARNING] Database counts do not match.")
    sys.exit(1)
PY

echo
echo "======================================"
echo "          DEMO COMPLETED"
echo "======================================"
echo "SENTRIX engine log: $ENGINE_LOG"
echo "Cowrie log:         $COWRIE_LOG"
echo "Docker containers remain running."
