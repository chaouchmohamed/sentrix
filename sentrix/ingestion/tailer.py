from __future__ import annotations
import os
import sqlite3
import time
from pathlib import Path
from typing import Iterator

from .. import db


class Tailer:
    META_KEY = "cowrie_offset"

    def __init__(self, conn: sqlite3.Connection, log_path: str):
        self.conn = conn
        self.path = Path(log_path)
        self.offset = int(db.get_meta(conn, self.META_KEY, 0) or 0)

    def _handle_rotation(self) -> None:
        try:
            size = self.path.stat().st_size
        except FileNotFoundError:
            self.offset = 0
            return
        if size < self.offset:       # truncated / renamed -> new file
            self.offset = 0

    def follow(self, poll: float = 0.5) -> Iterator[str]:
        """Yield new raw lines forever. Uses readline() because Python forbids fh.tell() after next()."""
        while True:
            self._handle_rotation()
            if not self.path.exists():
                time.sleep(poll)
                continue
            with self.path.open("r", encoding="utf-8", errors="replace") as fh:
                fh.seek(self.offset)
                while True:
                    line = fh.readline()
                    if not line:
                        break
                    self.offset = fh.tell()
                    db.set_meta(self.conn, self.META_KEY, str(self.offset))
                    self.conn.commit()
                    yield line
            time.sleep(poll)

    def replay(self, sample_path: str) -> Iterator[str]:
        """Replay a saved sample (FR-15). Does not move the live offset."""
        with open(sample_path, "r", encoding="utf-8", errors="replace") as fh:
            for line in fh:
                yield line
