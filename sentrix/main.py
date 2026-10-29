"""Runner: tailer -> parser -> DB -> engine -> correlator -> responder.
Usage:
  python -m sentrix.main --replay data/sample/cowrie_sample.json
  python -m sentrix.main --live honeypot/logs/cowrie.json
"""
from __future__ import annotations
import argparse
import logging
import os
import time

from . import db
from .config import load_config
from .ingestion.parser import parse_line, stats
from .ingestion.tailer import Tailer
from .detection.engine import run_rules
from .correlation.correlator import ingest_alert
from .response.responder import maybe_respond

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
log = logging.getLogger("sentrix.main")


def _process(conn, line: str, config: dict) -> None:
    ev = parse_line(line)
    if ev is None:
        return
    ev_id = db.insert_event(conn, ev)
    if ev_id is None:            # duplicate (UNIQUE) — idempotent (playbook)
        return
    ev.id = ev_id
    alerts = run_rules(conn, ev, config)   # run_rules now sets a.id itself
    for a in alerts:
        inc_id = ingest_alert(conn, a, config)
        maybe_respond(conn, inc_id, a.src_ip, a.severity, config, alert_ts=a.ts_utc)
    conn.commit()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--replay", help="Replay a saved sample log (FR-15)")
    ap.add_argument("--live", help="Follow a live cowrie.json")
    ap.add_argument("--db", default=os.environ.get("SENTRIX_DB_PATH", "data/sentrix.db"))
    args = ap.parse_args()

    config = load_config()
    db.init_db(args.db)
    conn = db.connect(args.db)

    if args.replay:
        log.info("replay mode: %s", args.replay)
        for line in Tailer(conn, args.db).replay(args.replay):
            _process(conn, line, config)
        log.info("replay done. parser stats=%s", stats())
        return

    if args.live:
        log.info("live mode: %s", args.live)
        for line in Tailer(conn, args.live).follow():
            _process(conn, line, config)
        return

    ap.error("choose --replay FILE or --live FILE")


if __name__ == "__main__":
    main()
