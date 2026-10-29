"""Groups alerts by source IP within idle gap (FR-30); sets severity (FR-32); writes incidents (FR-33)."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timedelta

from ..models import Alert, Incident
from .stages import stage_of, ordered

_SEV_ORDER = ["low", "medium", "high", "critical"]


def _bump(sev: str) -> str:
    i = _SEV_ORDER.index(sev)
    return _SEV_ORDER[min(i + 1, len(_SEV_ORDER) - 1)]


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


def ingest_alert(conn: sqlite3.Connection, alert: Alert, config: dict) -> int:
    """Attach alert to an open incident for its IP, or open a new one. Returns incident id."""
    idle = config["correlation"]["idle_gap_seconds"]
    esc = config["correlation"]["escalation_stages"]
    now = _ts(alert.ts_utc)

    row = conn.execute(
        "SELECT * FROM incidents WHERE src_ip=? AND status='open' "
        "ORDER BY last_seen DESC LIMIT 1", (alert.src_ip,)
    ).fetchone()

    if row and (now - _ts(row["last_seen"])).total_seconds() <= idle:
        stages = set(filter(None, row["stages"].split(",")))
        s = stage_of(alert.rule_id)
        if s:
            stages.add(s)
        if _SEV_ORDER.index(alert.severity) > _SEV_ORDER.index(row["severity"]):
            new_sev = alert.severity
        else:
            new_sev = row["severity"]
        if len(stages) >= esc:
            new_sev = _bump(new_sev)
        conn.execute(
            "UPDATE incidents SET last_seen=?, severity=?, stages=?, alert_count=alert_count+1 "
            "WHERE id=?",
            (alert.ts_utc, new_sev, ",".join(ordered(stages)), row["id"]),
        )
        conn.execute(
            "INSERT OR IGNORE INTO incident_alerts(incident_id,alert_id) VALUES(?,?)",
            (row["id"], alert.id),
        )
        return row["id"]

    stages = set()
    s = stage_of(alert.rule_id)
    if s:
        stages.add(s)
    sev = alert.severity
    if len(stages) >= esc:
        sev = _bump(sev)
    cur = conn.execute(
        "INSERT INTO incidents(src_ip,first_seen,last_seen,severity,status,stages,alert_count,session_count) "
        "VALUES(?,?,?,?, 'open', ?, 1, 1)",
        (alert.src_ip, alert.ts_utc, alert.ts_utc, sev, ",".join(ordered(stages))),
    )
    inc_id = cur.lastrowid
    conn.execute(
        "INSERT OR IGNORE INTO incident_alerts(incident_id,alert_id) VALUES(?,?)",
        (inc_id, alert.id),
    )
    return inc_id
