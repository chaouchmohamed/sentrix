-- SENTRIX storage contract — CONTRACT #2 (frozen day 1)
-- All timestamps UTC (ISO 8601). Dashboard opens read-only.

PRAGMA journal_mode = WAL;
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS events (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc      TEXT    NOT NULL,
    event_type  TEXT    NOT NULL,
    src_ip      TEXT,
    session     TEXT,
    username    TEXT,
    password    TEXT,
    command     TEXT,
    raw_json    TEXT    NOT NULL,
    raw_hash    TEXT    NOT NULL,
    UNIQUE(session, ts_utc, event_type, raw_hash)
);
CREATE INDEX IF NOT EXISTS idx_events_ts        ON events(ts_utc);
CREATE INDEX IF NOT EXISTS idx_events_src       ON events(src_ip, ts_utc);
CREATE INDEX IF NOT EXISTS idx_events_type      ON events(event_type);

CREATE TABLE IF NOT EXISTS alerts (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc       TEXT NOT NULL,
    rule_id      TEXT NOT NULL,
    severity     TEXT NOT NULL,
    src_ip       TEXT,
    session      TEXT,
    window_start TEXT,
    window_end   TEXT,
    explanation  TEXT NOT NULL,
    technique    TEXT
);
CREATE INDEX IF NOT EXISTS idx_alerts_ts   ON alerts(ts_utc);
CREATE INDEX IF NOT EXISTS idx_alerts_src  ON alerts(src_ip, ts_utc);
CREATE INDEX IF NOT EXISTS idx_alerts_rule ON alerts(rule_id);

CREATE TABLE IF NOT EXISTS alert_events (
    alert_id INTEGER NOT NULL REFERENCES alerts(id) ON DELETE CASCADE,
    event_id INTEGER NOT NULL REFERENCES events(id) ON DELETE CASCADE,
    PRIMARY KEY (alert_id, event_id)
);

CREATE TABLE IF NOT EXISTS incidents (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    src_ip        TEXT NOT NULL,
    first_seen    TEXT NOT NULL,
    last_seen     TEXT NOT NULL,
    severity      TEXT NOT NULL,
    status        TEXT NOT NULL DEFAULT 'open',
    stages        TEXT NOT NULL DEFAULT '',
    alert_count   INTEGER NOT NULL DEFAULT 0,
    session_count INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_inc_src  ON incidents(src_ip, last_seen);
CREATE INDEX IF NOT EXISTS idx_inc_sev  ON incidents(severity, last_seen);

CREATE TABLE IF NOT EXISTS incident_alerts (
    incident_id INTEGER NOT NULL REFERENCES incidents(id) ON DELETE CASCADE,
    alert_id    INTEGER NOT NULL REFERENCES alerts(id)    ON DELETE CASCADE,
    PRIMARY KEY (incident_id, alert_id)
);

CREATE TABLE IF NOT EXISTS actions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    ts_utc      TEXT NOT NULL,
    src_ip      TEXT NOT NULL,
    action      TEXT NOT NULL,
    mode        TEXT NOT NULL,
    expires_at  TEXT,
    incident_id INTEGER REFERENCES incidents(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
