#!/usr/bin/env python3
"""
sentrix_sync.py — mirror the SENTRIX SQLite database to Turso (hosted libSQL)

Runs on the machine that runs the SENTRIX engine. It READS the engine's
data/sentrix.db (read-only, never writes to it) and pushes new/changed rows to
a Turso database over HTTPS, so the hosted dashboard can show live data.

  * Python 3.9+, standard library only (no pip install needed)
  * Incremental: only rows added or changed since the last cycle are sent
  * Idempotent: safe to stop/restart at any time (the remote DB is the cursor)
  * Self-healing: if the engine DB is reset (make reset) the mirror is rebuilt
  * Resilient: each HTTPS request is retried (fast-fail connect, 5 attempts)
    and one connection is reused, to survive flaky network paths

Usage
  export TURSO_DATABASE_URL="libsql://sentrix-<org>.turso.io"
  export TURSO_AUTH_TOKEN="<full-access token>"
  export SENTRIX_DB_PATH="/path/to/sentrix/data/sentrix.db"

  python3 sentrix_sync.py --once          # one sync, then exit (first test)
  python3 sentrix_sync.py                 # keep syncing every 10 s
  python3 sentrix_sync.py --interval 5 --verbose
"""
from __future__ import annotations

import argparse
import base64
import http.client
import json
import logging
import os
import re
import sqlite3
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

log = logging.getLogger("sentrix_sync")

BATCH = 200
CREATE_RE = re.compile(r"^CREATE\s+(UNIQUE\s+INDEX|INDEX|TABLE)\s+", re.IGNORECASE)

# Column lists are explicit so the mirror never depends on column order.
COLS = {
    "events": [
        "id", "ts_utc", "event_type", "src_ip", "session", "username",
        "password", "command", "raw_json", "raw_hash",
    ],
    "alerts": [
        "id", "ts_utc", "rule_id", "severity", "src_ip", "session",
        "window_start", "window_end", "explanation", "technique",
    ],
    "incidents": [
        "id", "src_ip", "first_seen", "last_seen", "severity", "status",
        "stages", "alert_count", "session_count",
    ],
    "actions": [
        "id", "ts_utc", "src_ip", "action", "mode", "expires_at", "incident_id",
    ],
}


class FatalError(Exception):
    """Configuration / authentication problems — retrying will not help."""


class RemoteError(Exception):
    """The remote database rejected a statement."""


# ─── Remote (Turso over HTTPS, "Hrana over HTTP") ────────────────────────────

class Remote:
    def __init__(self, url: str, token: str, timeout: int = 25) -> None:
        url = url.strip().rstrip("/")
        if url.startswith("libsql://"):
            url = "https://" + url[len("libsql://"):]
        if not url.startswith(("https://", "http://")):
            raise FatalError("TURSO_DATABASE_URL must look like libsql://name-org.turso.io")
        self.endpoint = url + "/v2/pipeline"
        self.token = token
        self.timeout = timeout
        u = urllib.parse.urlparse(self.endpoint)
        self.scheme, self.host, self.path = u.scheme, u.netloc, u.path
        self.conn = None

    @staticmethod
    def _arg(v):
        if v is None:
            return {"type": "null"}
        if isinstance(v, bool):
            return {"type": "integer", "value": str(int(v))}
        if isinstance(v, int):
            return {"type": "integer", "value": str(v)}
        if isinstance(v, float):
            return {"type": "float", "value": v}
        if isinstance(v, (bytes, bytearray)):
            return {"type": "blob", "base64": base64.b64encode(bytes(v)).decode()}
        return {"type": "text", "value": str(v)}

    @staticmethod
    def _decode(cell):
        t = cell.get("type")
        if t == "null":
            return None
        if t == "integer":
            return int(cell["value"])
        if t == "float":
            return float(cell["value"])
        return cell.get("value")

    def _close(self):
        if self.conn is not None:
            try:
                self.conn.close()
            except Exception:
                pass
            self.conn = None

    def _post(self, body: bytes):
        last = None
        for attempt in range(1, 6):
            try:
                if self.conn is None:
                    cls = http.client.HTTPSConnection if self.scheme == "https" else http.client.HTTPConnection
                    self.conn = cls(self.host, timeout=6)   # fast-fail connect
                    self.conn.connect()
                    self.conn.sock.settimeout(self.timeout)  # patient reads
                self.conn.request("POST", self.path, body=body, headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json",
                })
                resp = self.conn.getresponse()
                data = resp.read()
                if self.conn.sock is None:      # server closed the connection
                    self.conn = None
                return resp.status, data
            except (OSError, http.client.HTTPException) as e:
                last = e
                self._close()
                log.debug("request attempt %d/5 failed: %s", attempt, e)
                time.sleep(min(0.5 * attempt, 2.0))
        raise last

    def run(self, statements):
        """Executes [(sql, args), ...] in ONE HTTPS request; returns raw results."""
        reqs = []
        for sql, args in statements:
            stmt = {"sql": sql}
            if args:
                stmt["args"] = [self._arg(a) for a in args]
            reqs.append({"type": "execute", "stmt": stmt})
        reqs.append({"type": "close"})
        body = json.dumps({"requests": reqs}).encode("utf-8")
        status, data = self._post(body)
        if status in (401, 403):
            raise FatalError(
                f"Turso rejected the token (HTTP {status}). Create a new one with: "
                "turso db tokens create <db-name>"
            )
        if status != 200:
            raise RemoteError(f"HTTP {status}: {data[:300].decode('utf-8', 'replace')}")
        payload = json.loads(data)
        out = []
        for r in payload.get("results", [])[: len(statements)]:
            if r.get("type") == "error":
                raise RemoteError(r.get("error", {}).get("message", "remote error"))
            out.append(r["response"]["result"])
        return out

    def scalar(self, sql: str):
        rows = self.run([(sql, [])])[0].get("rows", [])
        return self._decode(rows[0][0]) if rows else None

    def transaction(self, statements) -> None:
        """Atomic batch: BEGIN … COMMIT (a failure mid-way rolls everything back)."""
        self.run([("BEGIN", [])] + list(statements) + [("COMMIT", [])])


# ─── Syncer ──────────────────────────────────────────────────────────────────

def upsert_sql(table: str) -> str:
    cols = COLS[table]
    sets = ", ".join(f"{c}=excluded.{c}" for c in cols if c != "id")
    ph = ",".join("?" * len(cols))
    return (
        f"INSERT INTO {table} ({','.join(cols)}) VALUES ({ph}) "
        f"ON CONFLICT(id) DO UPDATE SET {sets}"
    )


def insert_ignore_sql(table: str) -> str:
    cols = COLS[table]
    return f"INSERT OR IGNORE INTO {table} ({','.join(cols)}) VALUES ({','.join('?' * len(cols))})"


class Syncer:
    def __init__(self, remote: Remote, batch: int = BATCH) -> None:
        self.remote = remote
        self.batch = batch
        self.sent_rows: dict[str, dict[int, tuple]] = {"incidents": {}, "actions": {}}
        self.sent_links: dict[int, frozenset] = {}

    # -- schema ---------------------------------------------------------------
    def init_schema(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            "SELECT type, sql FROM sqlite_master WHERE sql IS NOT NULL "
            "AND name NOT LIKE 'sqlite_%' ORDER BY CASE type WHEN 'table' THEN 0 ELSE 1 END, name"
        ).fetchall()
        stmts = []
        for _type, sql in rows:
            stmts.append((CREATE_RE.sub(lambda m: f"CREATE {m.group(1)} IF NOT EXISTS ", sql, count=1), []))
        if stmts:
            self.remote.run(stmts)
        log.info("remote schema ready (%d objects)", len(stmts))

    # -- one cycle --------------------------------------------------------------
    def cycle(self, conn: sqlite3.Connection) -> dict[str, int]:
        sent = {k: 0 for k in ("events", "alerts", "alert_events", "incidents", "incident_alerts", "actions")}
        # One consistent snapshot of the engine DB for the whole cycle (WAL = snapshot isolation).
        conn.execute("BEGIN")
        try:
            l_ev = conn.execute("SELECT COALESCE(MAX(id),0) FROM events").fetchone()[0]
            l_al = conn.execute("SELECT COALESCE(MAX(id),0) FROM alerts").fetchone()[0]
            r_ev = self.remote.scalar("SELECT COALESCE(MAX(id),0) FROM events") or 0
            r_al = self.remote.scalar("SELECT COALESCE(MAX(id),0) FROM alerts") or 0

            if l_ev < r_ev or l_al < r_al:
                log.warning(
                    "local DB is behind the mirror (events %s<%s) — it was reset; rebuilding the mirror",
                    l_ev, r_ev,
                )
                self.remote.transaction(
                    [(f"DELETE FROM {t}", []) for t in
                     ("incident_alerts", "actions", "incidents", "alert_events", "alerts", "events")]
                )
                self.sent_rows = {"incidents": {}, "actions": {}}
                self.sent_links = {}
                r_ev = r_al = 0

            # events
            cursor = r_ev
            while cursor < l_ev:
                rows = conn.execute(
                    f"SELECT {','.join(COLS['events'])} FROM events WHERE id > ? ORDER BY id LIMIT ?",
                    (cursor, self.batch),
                ).fetchall()
                if not rows:
                    break
                self.remote.transaction([(insert_ignore_sql("events"), list(r)) for r in rows])
                cursor = rows[-1][0]
                sent["events"] += len(rows)

            # alerts (+ their evidence links, which the engine commits together)
            cursor = r_al
            while cursor < l_al:
                rows = conn.execute(
                    f"SELECT {','.join(COLS['alerts'])} FROM alerts WHERE id > ? ORDER BY id LIMIT ?",
                    (cursor, self.batch),
                ).fetchall()
                if not rows:
                    break
                lo, hi = rows[0][0], rows[-1][0]
                links = conn.execute(
                    "SELECT alert_id, event_id FROM alert_events WHERE alert_id BETWEEN ? AND ?",
                    (lo, hi),
                ).fetchall()
                stmts = [(insert_ignore_sql("alerts"), list(r)) for r in rows]
                stmts += [
                    ("INSERT OR IGNORE INTO alert_events (alert_id, event_id) VALUES (?,?)", [a, e])
                    for a, e in links
                ]
                self.remote.transaction(stmts)
                cursor = hi
                sent["alerts"] += len(rows)
                sent["alert_events"] += len(links)

            # incidents + actions are small and MUTABLE: upsert only what changed
            for table in ("incidents", "actions"):
                known = self.sent_rows[table]
                changed = []
                for r in conn.execute(f"SELECT {','.join(COLS[table])} FROM {table} ORDER BY id"):
                    row = tuple(r)
                    if known.get(row[0]) != row:
                        changed.append(row)
                for i in range(0, len(changed), self.batch):
                    chunk = changed[i : i + self.batch]
                    self.remote.transaction([(upsert_sql(table), list(r)) for r in chunk])
                    for r in chunk:
                        known[r[0]] = r
                    sent[table] += len(chunk)

            # incident -> alert links (only for incidents whose link set changed)
            by_incident: dict[int, set] = {}
            for inc, alert in conn.execute("SELECT incident_id, alert_id FROM incident_alerts"):
                by_incident.setdefault(inc, set()).add(alert)
            stmts = []
            fresh: dict[int, frozenset] = {}
            for inc, alerts in by_incident.items():
                cur = frozenset(alerts)
                old = self.sent_links.get(inc, frozenset())
                if cur != old:
                    for a in sorted(cur - old):
                        stmts.append(
                            ("INSERT OR IGNORE INTO incident_alerts (incident_id, alert_id) VALUES (?,?)", [inc, a])
                        )
                    fresh[inc] = cur
            for i in range(0, len(stmts), self.batch):
                self.remote.transaction(stmts[i : i + self.batch])
            self.sent_links.update(fresh)
            sent["incident_alerts"] += len(stmts)
        finally:
            conn.rollback()
        return sent


# ─── CLI ─────────────────────────────────────────────────────────────────────

def open_local(path: Path) -> sqlite3.Connection:
    if not path.exists():
        raise FileNotFoundError(path)
    # Read-only: the sync agent can never damage the engine's database.
    conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True, timeout=5, isolation_level=None)
    return conn


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Mirror the SENTRIX SQLite DB to Turso.")
    ap.add_argument("--db", default=os.environ.get("SENTRIX_DB_PATH", "data/sentrix.db"))
    ap.add_argument("--url", default=os.environ.get("TURSO_DATABASE_URL"))
    ap.add_argument("--token", default=os.environ.get("TURSO_AUTH_TOKEN"))
    ap.add_argument("--interval", type=float, default=10.0, help="seconds between syncs (default 10)")
    ap.add_argument("--once", action="store_true", help="sync once and exit")
    ap.add_argument("--no-init", action="store_true", help="do not create the remote tables")
    ap.add_argument("--verbose", "-v", action="store_true")
    args = ap.parse_args(argv)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)s sentrix_sync: %(message)s",
    )
    if not args.url or not args.token:
        log.error("Set TURSO_DATABASE_URL and TURSO_AUTH_TOKEN (or pass --url / --token).")
        return 2

    try:
        remote = Remote(args.url, args.token)
    except FatalError as e:
        log.error("%s", e)
        return 2
    syncer = Syncer(remote)
    db_path = Path(args.db).expanduser().resolve()
    initialised = args.no_init
    backoff = 2.0
    last_beat = 0.0

    while True:
        try:
            conn = open_local(db_path)
            try:
                if not initialised:
                    syncer.init_schema(conn)
                    initialised = True
                stats = syncer.cycle(conn)
            finally:
                conn.close()
            backoff = 2.0
            total = sum(stats.values())
            if total:
                log.info("synced %s", ", ".join(f"{k}={v}" for k, v in stats.items() if v))
            elif time.time() - last_beat > 60:
                log.info("up to date")
                last_beat = time.time()
        except FileNotFoundError:
            log.warning("engine database not found yet: %s", db_path)
        except FatalError as e:
            log.error("%s", e)
            return 2
        except (RemoteError, urllib.error.URLError, http.client.HTTPException,
                TimeoutError, OSError, sqlite3.Error) as e:
            log.warning("sync failed: %s — retrying in %.0fs", e, backoff)
            if args.once:
                return 1
            time.sleep(backoff)
            backoff = min(backoff * 2, 60.0)
            continue

        if args.once:
            return 0
        time.sleep(args.interval)


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print()
        sys.exit(0)
