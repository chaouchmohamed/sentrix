"""R06 — Connection flood / scan: N connections from one IP in a window, no login. Low. T1046."""
from __future__ import annotations
from datetime import datetime, timedelta

from ..base import Rule
from ...models import Alert, Event


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class R06ConnectionFlood(Rule):
    rule_id = "R06"
    name = "Connection flood / scan"

    def evaluate(self, conn, event: Event, config: dict) -> Alert | None:
        if event.event_type != "session_connect" or not event.src_ip:
            return None
        cfg = config["detection"]["r06_connection_flood"]
        now = _ts(event.ts_utc)
        start = (now - timedelta(seconds=cfg["window_seconds"])).isoformat()
        rows = conn.execute(
            "SELECT id FROM events WHERE event_type='session_connect' AND src_ip=? "
            "AND ts_utc >= ? AND ts_utc <= ?",
            (event.src_ip, start, event.ts_utc),
        ).fetchall()
        if len(rows) < cfg["threshold"]:
            return None
        return Alert(
            ts_utc=event.ts_utc, rule_id=self.rule_id, severity=cfg["severity"],
            src_ip=event.src_ip, session=event.session,
            window_start=start, window_end=event.ts_utc,
            explanation=f"{len(rows)} connections from {event.src_ip} "
                        f"in {cfg['window_seconds']}s (threshold {cfg['threshold']})",
            technique="T1046",
            evidence_event_ids=[r["id"] for r in rows],
        )
