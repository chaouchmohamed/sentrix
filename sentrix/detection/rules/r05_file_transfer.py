"""R05 — File transfer: download/upload event or download command. High. T1105."""
from __future__ import annotations
import re

from ..base import Rule
from ...models import Alert, Event

_DL = re.compile(r"\b(wget|curl|tftp)\b", re.IGNORECASE)


class R05FileTransfer(Rule):
    rule_id = "R05"
    name = "File transfer"

    def evaluate(self, conn, event: Event, config: dict) -> Alert | None:
        cfg = config["detection"]["r05_file_transfer"]
        hit = event.event_type in ("file_download", "file_upload") or (
            event.event_type == "command" and event.command and _DL.search(event.command)
        )
        if not hit:
            return None
        ids = [event.id] if event.id else []
        return Alert(
            ts_utc=event.ts_utc, rule_id=self.rule_id, severity=cfg["severity"],
            src_ip=event.src_ip, session=event.session,
            window_start=event.ts_utc, window_end=event.ts_utc,
            explanation=f"File transfer detected: {event.event_type}"
                        + (f" ({event.command})" if event.command else ""),
            technique="T1105",
            evidence_event_ids=ids,
        )
