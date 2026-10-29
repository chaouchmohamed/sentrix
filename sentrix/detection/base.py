"""Rule interface. Add a rule = add one file + register in engine.py (FR-24)."""
from __future__ import annotations
import sqlite3
from abc import ABC, abstractmethod
from typing import Optional

from ..models import Alert, Event


class Rule(ABC):
    rule_id: str = ""
    name: str = ""

    @abstractmethod
    def evaluate(self, conn: sqlite3.Connection, event: Event, config: dict) -> Optional[Alert]:
        """Return an Alert if the event (with recent context) triggers this rule, else None."""
        ...
