"""Optional responder. Dry-run by default (FR-61). Real mode adds an expiring iptables rule (FR-62)."""
from __future__ import annotations
import logging
import sqlite3
import subprocess
from datetime import datetime, timedelta, timezone

log = logging.getLogger("sentrix.responder")


def _now_utc(alert_ts: str | None) -> datetime:
    if alert_ts:
        return datetime.fromisoformat(alert_ts.replace("Z", "+00:00"))
    return datetime.now(timezone.utc)


def maybe_respond(conn: sqlite3.Connection, incident_id: int, src_ip: str,
                  severity: str, config: dict, alert_ts: str | None = None) -> None:
    cfg = config.get("response", {})
    if severity not in ("high", "critical"):
        return
    if src_ip in config.get("allowlist", {}).get("ips", []):
        return
    mode = cfg.get("mode", "dry_run")
    now = _now_utc(alert_ts)
    expires = (now + timedelta(minutes=cfg.get("block_minutes", 15))).isoformat()
    conn.execute(
        "INSERT INTO actions(ts_utc,src_ip,action,mode,expires_at,incident_id) "
        "VALUES(?,?,?,?,?,?)",
        (now.isoformat(), src_ip, "block", mode, expires, incident_id),
    )
    if mode == "real":
        try:
            subprocess.run(["sudo", "iptables", "-I", "INPUT", "-s", src_ip, "-j", "DROP"],
                           check=True)
            log.warning("BLOCKED %s until %s", src_ip, expires)
        except Exception as exc:
            log.exception("real block failed for %s: %s", src_ip, exc)
    else:
        log.info("DRY-RUN would block %s until %s", src_ip, expires)
