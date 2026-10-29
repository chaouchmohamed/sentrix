"""R03 — Login after failures: success within window after >=N failures. High. T1078."""
from __future__ import annotations
from datetime import datetime, timedelta

from ..base import Rule
from ...models import Alert, Event


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class R03LoginAfterFailures(Rule):
    rule_id = "R03"
    name = "Login after failures"

    def evaluate(self, conn, event: Event, config: dict) -> Alert | None:
        if event.event_type != "login_success" or not event.src_ip:
            return None
        cfg = config["detection"]["r03_login_after_failures"]
        now = _ts(event.ts_utc)
        start = (now - timedelta(seconds=cfg["window_seconds"])).isoformat()
        rows = conn.execute(
            "SELECT id FROM events WHERE event_type='login_failed' AND src_ip=? "
            "AND ts_utc >= ? AND ts_utc <= ?",
            (event.src_ip, start, event.ts_utc),
        ).fetchall()
        if len(rows) < cfg["min_prior_failures"]:
            return None
        ids = [r["id"] for r in rows]
        ids.append(event.id) if event.id else None
        return Alert(
            ts_utc=event.ts_utc, rule_id=self.rule_id, severity=cfg["severity"],
            src_ip=event.src_ip, session=event.session,
            window_start=start, window_end=event.ts_utc,
            explanation=f"Successful login from {event.src_ip} after {len(rows)} failures "
                        f"within {cfg['window_seconds']}s",
            technique="T1078",
            evidence_event_ids=ids,
        )
