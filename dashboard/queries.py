"""All SQL reads for the dashboard. Opens the DB READ-ONLY (FR-41). No engine imports (dependency rule)."""
from __future__ import annotations
import os
import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

_DB = Path(os.environ.get("SENTRIX_DB_PATH", "data/sentrix.db"))


def _conn() -> sqlite3.Connection:
    uri = f"file:{_DB}?mode=ro"
    conn = sqlite3.connect(uri, uri=True, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def db_exists() -> bool:
    return _DB.exists()


# ---------- Overview (FR-50) ----------

def totals() -> dict:
    with _conn() as c:
        return {
            "events":    c.execute("SELECT COUNT(*) FROM events").fetchone()[0],
            "alerts":    c.execute("SELECT COUNT(*) FROM alerts").fetchone()[0],
            "incidents": c.execute("SELECT COUNT(*) FROM incidents").fetchone()[0],
        }


def alerts_per_severity() -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT severity, COUNT(*) AS n FROM alerts GROUP BY severity "
            "ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 "
            "WHEN 'medium' THEN 2 ELSE 3 END", c)


def events_over_time(bucket_minutes: int = 1) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            f"""SELECT strftime('%Y-%m-%dT%H:%M:00', ts_utc) AS bucket, COUNT(*) AS n
                FROM events GROUP BY bucket ORDER BY bucket""", c)


def top_sources(limit: int = 10) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT src_ip, COUNT(*) AS n FROM events WHERE src_ip IS NOT NULL "
            "GROUP BY src_ip ORDER BY n DESC LIMIT ?", c, params=(limit,))


def top_usernames(limit: int = 10) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT username, COUNT(*) AS n FROM events WHERE username IS NOT NULL "
            "AND username != '' GROUP BY username ORDER BY n DESC LIMIT ?", c, params=(limit,))


def top_passwords(limit: int = 10) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT password, COUNT(*) AS n FROM events WHERE password IS NOT NULL "
            "AND password != '' GROUP BY password ORDER BY n DESC LIMIT ?", c, params=(limit,))


# ---------- Alerts (FR-51) ----------

def alerts_filtered(severity: Optional[str] = None, rule_id: Optional[str] = None,
                    src_ip: Optional[str] = None,
                    since: Optional[str] = None) -> pd.DataFrame:
    q = "SELECT id, ts_utc, rule_id, severity, src_ip, session, explanation, technique FROM alerts WHERE 1=1"
    params: list = []
    if severity:
        q += " AND severity = ?"; params.append(severity)
    if rule_id:
        q += " AND rule_id = ?"; params.append(rule_id)
    if src_ip:
        q += " AND src_ip LIKE ?"; params.append(f"%{src_ip}%")
    if since:
        q += " AND ts_utc >= ?"; params.append(since)
    q += " ORDER BY id DESC"
    with _conn() as c:
        return pd.read_sql_query(q, c, params=params)


def distinct_severities() -> list[str]:
    with _conn() as c:
        return [r[0] for r in c.execute(
            "SELECT DISTINCT severity FROM alerts ORDER BY severity").fetchall()]


def distinct_rules() -> list[str]:
    with _conn() as c:
        return [r[0] for r in c.execute(
            "SELECT DISTINCT rule_id FROM alerts ORDER BY rule_id").fetchall()]


def evidence_for_alert(alert_id: int) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT e.id, e.ts_utc, e.event_type, e.username, e.command "
            "FROM events e JOIN alert_events ae ON ae.event_id = e.id "
            "WHERE ae.alert_id = ? ORDER BY e.ts_utc", c, params=(alert_id,))


# ---------- Incidents (FR-52, FR-53) ----------

def incidents_list() -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT id, src_ip, first_seen, last_seen, severity, status, "
            "stages, alert_count, session_count FROM incidents "
            "ORDER BY CASE severity WHEN 'critical' THEN 0 WHEN 'high' THEN 1 "
            "WHEN 'medium' THEN 2 ELSE 3 END, last_seen DESC", c)


def incident_header(incident_id: int) -> Optional[dict]:
    with _conn() as c:
        row = c.execute(
            "SELECT * FROM incidents WHERE id = ?", (incident_id,)).fetchone()
    return dict(row) if row else None


def incident_alerts(incident_id: int) -> pd.DataFrame:
    with _conn() as c:
        return pd.read_sql_query(
            "SELECT a.id, a.ts_utc, a.rule_id, a.severity, a.explanation, a.technique "
            "FROM alerts a JOIN incident_alerts ia ON ia.alert_id = a.id "
            "WHERE ia.incident_id = ? ORDER BY a.ts_utc", c, params=(incident_id,))


def incident_timeline(incident_id: int) -> pd.DataFrame:
    """Ordered stages with evidence events (FR-53)."""
    with _conn() as c:
        return pd.read_sql_query(
            """SELECT a.rule_id, a.ts_utc, a.severity, a.explanation,
                      e.id AS event_id, e.event_type, e.command
               FROM alerts a
               JOIN incident_alerts ia ON ia.alert_id = a.id
               LEFT JOIN alert_events ae ON ae.alert_id = a.id
               LEFT JOIN events e ON e.id = ae.event_id
               WHERE ia.incident_id = ?
               ORDER BY a.ts_utc, e.ts_utc""", c, params=(incident_id,))
