"""The ONLY module that talks to SQLite. WAL mode; dashboard opens read-only."""
from __future__ import annotations
import json
import sqlite3
from pathlib import Path
from typing import Iterable, Optional

from .models import Alert, Event

SCHEMA = Path(__file__).resolve().parent / "schema.sql"


def connect(db_path: str, read_only: bool = False) -> sqlite3.Connection:
    if read_only:
        uri = f"file:{db_path}?mode=ro"
        conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    else:
        conn = sqlite3.connect(db_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db(db_path: str) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)
    conn = connect(db_path)
    with conn:
        conn.executescript(SCHEMA.read_text(encoding="utf-8"))
        conn.execute(
            "INSERT OR IGNORE INTO meta(key,value) VALUES('schema_version','1')"
        )
    conn.close()


def insert_event(conn: sqlite3.Connection, ev: Event) -> Optional[int]:
    """Returns new event id, or None if it already existed (UNIQUE constraint)."""
    cur = conn.execute(
        """INSERT OR IGNORE INTO events
           (ts_utc,event_type,src_ip,session,username,password,command,raw_json,raw_hash)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (ev.ts_utc, ev.event_type, ev.src_ip, ev.session, ev.username,
         ev.password, ev.command, ev.raw_json, ev.raw_hash),
    )
    return cur.lastrowid if cur.rowcount else None


def recent_events(conn: sqlite3.Connection, since_ts: str,
                  src_ip: str | None = None) -> list[sqlite3.Row]:
    if src_ip:
        return conn.execute(
            "SELECT * FROM events WHERE ts_utc >= ? AND src_ip = ? ORDER BY ts_utc",
            (since_ts, src_ip),
        ).fetchall()
    return conn.execute(
        "SELECT * FROM events WHERE ts_utc >= ? ORDER BY ts_utc", (since_ts,)
    ).fetchall()


def insert_alert(conn: sqlite3.Connection, alert: Alert) -> int:
    cur = conn.execute(
        """INSERT INTO alerts
           (ts_utc,rule_id,severity,src_ip,session,window_start,window_end,explanation,technique)
           VALUES (?,?,?,?,?,?,?,?,?)""",
        (alert.ts_utc, alert.rule_id, alert.severity, alert.src_ip, alert.session,
         alert.window_start, alert.window_end, alert.explanation, alert.technique),
    )
    alert_id = cur.lastrowid
    for ev_id in alert.evidence_event_ids:
        conn.execute(
            "INSERT OR IGNORE INTO alert_events(alert_id,event_id) VALUES(?,?)",
            (alert_id, ev_id),
        )
    return alert_id


def set_meta(conn: sqlite3.Connection, key: str, value: str) -> None:
    conn.execute(
        "INSERT INTO meta(key,value) VALUES(?,?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def get_meta(conn: sqlite3.Connection, key: str, default=None):
    row = conn.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default
