"""JSON line -> normalised Event. Counts and skips bad lines; never crashes (FR-11, FR-14)."""
from __future__ import annotations
import hashlib
import json
from typing import Optional

from ..models import Event

# Cowrie eventid -> internal event_type (input contract, SRS 7.1)
TYPE_MAP = {
    "cowrie.session.connect":       "session_connect",
    "cowrie.client.version":        "client_version",
    "cowrie.login.failed":          "login_failed",
    "cowrie.login.success":         "login_success",
    "cowrie.command.input":         "command",
    "cowrie.session.file_download": "file_download",
    "cowrie.session.file_upload":   "file_upload",
    "cowrie.session.closed":        "session_closed",
}

_skip = 0
_bad = 0


def stats() -> dict:
    return {"skipped": _skip, "bad": _bad}


def parse_line(line: str) -> Optional[Event]:
    global _skip, _bad
    line = line.strip()
    if not line:
        _skip += 1
        return None
    try:
        obj = json.loads(line)
    except json.JSONDecodeError:
        _bad += 1
        return None
    if not isinstance(obj, dict):
        _bad += 1
        return None
    eventid = obj.get("eventid", "")
    etype = TYPE_MAP.get(eventid)
    if not etype:
        _skip += 1
        return None
    ts = obj.get("timestamp")
    if not ts:
        _bad += 1
        return None
    raw_hash = hashlib.sha256(line.encode("utf-8")).hexdigest()
    return Event(
        ts_utc=ts,
        event_type=etype,
        src_ip=obj.get("src_ip"),
        session=obj.get("session"),
        username=obj.get("username"),
        password=obj.get("password"),
        command=obj.get("input") or obj.get("command"),
        raw_json=line,
        raw_hash=raw_hash,
    )
