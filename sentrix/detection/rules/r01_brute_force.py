"""R01 — SSH brute force: N failures from one IP in a window. Medium, High above high_threshold. T1110."""
from __future__ import annotations
import sqlite3
from datetime import datetime, timedelta, timezone

from ..base import Rule
from ...models import Alert, Event


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class R01BruteForce(Rule):
    rule_id = "R01"
    name = "SSH brute force"

    def evaluate(self, conn, event: Event, config: dict) -> Alert | None:
        if event.event_type != "login_failed" or not event.src_ip:
            return None
        cfg = config["detection"]["r01_brute_force"]
        now = _ts(event.ts_utc)
        start = (now - timedelta(seconds=cfg["window_seconds"])).isoformat()
        rows = conn.execute(
            "SELECT id FROM events WHERE event_type='login_failed' AND src_ip=? "
            "AND ts_utc >= ? AND ts_utc <= ?",
            (event.src_ip, start, event.ts_utc),
        ).fetchall()
        n = len(rows)
        if n < cfg["threshold"]:
            return None
        sev = cfg["severity_high"] if n >= cfg["high_threshold"] else cfg["severity"]
        return Alert(
            ts_utc=event.ts_utc, rule_id=self.rule_id, severity=sev,
            src_ip=event.src_ip, session=event.session,
            window_start=start, window_end=event.ts_utc,
            explanation=f"{n} failed logins from {event.src_ip} in {cfg['window_seconds']}s "
                        f"(threshold {cfg['threshold']})",
            technique="T1110",
            evidence_event_ids=[r["id"] for r in rows],
        )

