"""Loads rules, runs them, applies cooldown per (rule, IP) (FR-23), writes alerts + evidence."""
from __future__ import annotations
import logging
import sqlite3
from datetime import datetime, timedelta

from .. import db
from ..models import Alert, Event
from .rules.r01_brute_force import R01BruteForce
from .rules.r02_password_spraying import R02PasswordSpraying
from .rules.r03_login_after_failures import R03LoginAfterFailures
from .rules.r04_suspicious_command import R04SuspiciousCommand
from .rules.r05_file_transfer import R05FileTransfer
from .rules.r06_connection_flood import R06ConnectionFlood

log = logging.getLogger("sentrix.engine")

# rule_id -> config key under detection.*
CONFIG_KEYS = {
    "R01": "r01_brute_force",
    "R02": "r02_password_spraying",
    "R03": "r03_login_after_failures",
    "R04": "r04_suspicious_command",
    "R05": "r05_file_transfer",
    "R06": "r06_connection_flood",
}

RULES = [R01BruteForce(), R02PasswordSpraying(), R03LoginAfterFailures(),
         R04SuspiciousCommand(), R05FileTransfer(), R06ConnectionFlood()]


def _cooldown(rule_id: str, config: dict) -> int:
    key = CONFIG_KEYS.get(rule_id)
    if not key:
        return 0
    return int(config.get("detection", {}).get(key, {}).get("cooldown_seconds", 0))


def _recently_fired(conn, rule_id: str, src_ip: str, now: str, cooldown: int) -> bool:
    start = (datetime.fromisoformat(now.replace("Z", "+00:00"))
             - timedelta(seconds=cooldown)).isoformat()
    row = conn.execute(
        "SELECT 1 FROM alerts WHERE rule_id=? AND src_ip=? AND ts_utc >= ? LIMIT 1",
        (rule_id, src_ip, start),
    ).fetchone()
    return row is not None


def run_rules(conn: sqlite3.Connection, event: Event, config: dict) -> list[Alert]:
    produced: list[Alert] = []
    for rule in RULES:
        try:
            alert = rule.evaluate(conn, event, config)
        except Exception as exc:
            log.exception("rule %s failed: %s", rule.rule_id, exc)
            continue
        if alert is None:
            continue
        cd = _cooldown(rule.rule_id, config)
        if alert.src_ip and cd and _recently_fired(conn, alert.rule_id, alert.src_ip, alert.ts_utc, cd):
            continue
        alert.id = db.insert_alert(conn, alert)
        produced.append(alert)
    return produced
