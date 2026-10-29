"""Shared dataclasses: Event, Alert, Incident. Every module speaks these (see README dependency rule)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Event:
    ts_utc: str
    event_type: str
    src_ip: Optional[str]
    session: Optional[str]
    username: Optional[str] = None
    password: Optional[str] = None
    command: Optional[str] = None
    raw_json: str = ""
    raw_hash: str = ""
    id: Optional[int] = None


@dataclass
class Alert:
    ts_utc: str
    rule_id: str
    severity: str            # low | medium | high | critical
    src_ip: Optional[str]
    session: Optional[str]
    window_start: str
    window_end: str
    explanation: str
    technique: str = ""
    evidence_event_ids: list[int] = field(default_factory=list)
    id: Optional[int] = None


@dataclass
class Incident:
    src_ip: str
    first_seen: str
    last_seen: str
    severity: str
    stages: list[str] = field(default_factory=list)
    alert_count: int = 0
    session_count: int = 0
    status: str = "open"
    id: Optional[int] = None
