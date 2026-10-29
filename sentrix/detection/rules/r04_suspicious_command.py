"""R04 — Suspicious command: match a config pattern category. Low..High. T1059/T1082/T1033/T1053."""
from __future__ import annotations
import re

from ..base import Rule
from ...models import Alert, Event


class R04SuspiciousCommand(Rule):
    rule_id = "R04"
    name = "Suspicious command"

    def evaluate(self, conn, event: Event, config: dict) -> Alert | None:
        if event.event_type != "command" or not event.command:
            return None
        cfg = config["detection"]["r04_suspicious_command"]
        cmd = event.command
        for category, spec in cfg["patterns"].items():
            for pat in spec["regex"]:
                if re.search(pat, cmd):
                    ev_ids = [event.id] if event.id else []
                    return Alert(
                        ts_utc=event.ts_utc, rule_id=self.rule_id,
                        severity=spec["severity"], src_ip=event.src_ip,
                        session=event.session,
                        window_start=event.ts_utc, window_end=event.ts_utc,
                        explanation=f"Command matched '{category}': {cmd[:120]!r}",
                        technique="T1059",
                        evidence_event_ids=ev_ids,
                    )
        return None
