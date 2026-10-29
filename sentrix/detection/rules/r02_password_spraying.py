"""R02 — Password spraying: N distinct usernames from one IP in a window. Medium. T1110.003."""
from __future__ import annotations
from datetime import datetime, timedelta

from ..base import Rule
from ...models import Alert, Event


def _ts(s: str) -> datetime:
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


class R02PasswordSpraying(Rule):
    rule_id = "R02"
    name = "Password spraying"

    def evaluate(self, conn, event: Event, config: dict) -> Alert | None:
        if event.event_type != "login_failed" or not event.src_ip:
            return None
        cfg = config["detection"]["r02_password_spraying"]
        now = _ts(event.ts_utc)
        start = (now - timedelta(seconds=cfg["window_seconds"])).isoformat()
        rows = conn.execute(
            "SELECT id, username FROM events WHERE event_type='login_failed' "
            "AND src_ip=? AND ts_utc >= ? AND ts_utc <= ?",
            (event.src_ip, start, event.ts_utc),
        ).fetchall()
        users = {r["username"] for r in rows if r["username"]}
        if len(users) < cfg["distinct_usernames"]:
            return None
        return Alert(
            ts_utc=event.ts_utc, rule_id=self.rule_id, severity=cfg["severity"],
            src_ip=event.src_ip, session=event.session,
            window_start=start, window_end=event.ts_utc,
            explanation=f"{len(users)} distinct usernames from {event.src_ip} "
                        f"in {cfg['window_seconds']}s (threshold {cfg['distinct_usernames']})",
            technique="T1110.003",
            evidence_event_ids=[r["id"] for r in rows],
        )
