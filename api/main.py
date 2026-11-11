"""Minimal read-only API for the SENTRIX React dashboard.

This module does not import or modify the detection, ingestion, correlation,
response, configuration, or schema layers. It reuses the existing read-only
query layer in dashboard/queries.py, which opens SQLite with mode=ro.

The API is built on Starlette (already available in the project environment)
rather than FastAPI. The routing surface is intentionally small and read-only.

Password values are intentionally never selected or returned by this API.
"""

from __future__ import annotations

import math
import os
from pathlib import Path
from typing import Any, Callable, Optional

import pandas as pd
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware.cors import CORSMiddleware
from starlette.requests import Request
from starlette.responses import FileResponse, JSONResponse, Response
from starlette.routing import Mount, Route
from starlette.staticfiles import StaticFiles

ROOT = Path(__file__).resolve().parent.parent

# Resolve the database before importing the existing query layer, because that
# module reads SENTRIX_DB_PATH at import time.
_db_env = os.environ.get("SENTRIX_DB_PATH")
if not _db_env:
    os.environ["SENTRIX_DB_PATH"] = str(ROOT / "data" / "sentrix.db")
elif not Path(_db_env).is_absolute():
    os.environ["SENTRIX_DB_PATH"] = str((ROOT / _db_env).resolve())

from dashboard import queries as q  # noqa: E402  (read-only SQLite access)

DB_PATH = Path(os.environ["SENTRIX_DB_PATH"])
FRONTEND_DIST = ROOT / "frontend" / "dist"


def _require_db() -> None:
    if not q.db_exists():
        raise HTTPException(
            status_code=503,
            detail=(
                "SENTRIX database not found. Start ingestion with "
                "`make replay` or `make run` before loading the dashboard."
            ),
        )


def _jsonable(value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, float) and math.isnan(value):
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        try:
            return value.item()
        except (AttributeError, ValueError):
            pass
    return value


def _records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    return [
        {str(key): _jsonable(value) for key, value in row.items()}
        for row in frame.to_dict(orient="records")
    ]


def _guard(handler: Callable[[], Any], operation: str) -> Any:
    """Run a read query and convert unexpected failures into a 500 response."""
    _require_db()
    try:
        return handler()
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - defensive boundary
        raise HTTPException(
            status_code=500, detail=f"Unable to {operation}: {exc}"
        ) from exc


def health(request: Request) -> JSONResponse:
    present = q.db_exists()
    payload: dict[str, Any] = {
        "status": "ok" if present else "unavailable",
        "database": DB_PATH.name,
        "read_only": True,
        "db_present": present,
    }
    if present:
        try:
            payload["counts"] = {k: int(v) for k, v in q.totals().items()}
        except Exception as exc:  # pragma: no cover - defensive boundary
            raise HTTPException(
                status_code=503, detail=f"Database unavailable: {exc}"
            ) from exc
    return JSONResponse(payload)


def overview(request: Request) -> JSONResponse:
    def read() -> dict[str, Any]:
        totals = {k: int(v) for k, v in q.totals().items()}
        return {
            "totals": totals,
            "severity_distribution": _records(q.alerts_per_severity()),
            "events_over_time": _records(q.events_over_time()),
            "top_sources": _records(q.top_sources()),
            "top_usernames": _records(q.top_usernames()),
            "recent_alerts": _records(q.alerts_filtered())[:8],
            "passwords_redacted": True,
        }

    return JSONResponse(_guard(read, "read overview"))


def alerts(request: Request) -> JSONResponse:
    severity = request.query_params.get("severity") or None
    rule_id = request.query_params.get("rule_id") or None
    src_ip = request.query_params.get("src_ip") or None
    since = request.query_params.get("since") or None

    def read() -> dict[str, Any]:
        items = _records(
            q.alerts_filtered(
                severity=severity,
                rule_id=rule_id,
                src_ip=src_ip,
                since=since,
            )
        )
        return {"items": items, "count": len(items)}

    return JSONResponse(_guard(read, "read alerts"))


def alert_filters(request: Request) -> JSONResponse:
    def read() -> dict[str, Any]:
        return {
            "severities": list(q.distinct_severities()),
            "rules": list(q.distinct_rules()),
        }

    return JSONResponse(_guard(read, "read filters"))


def alert_evidence(request: Request) -> JSONResponse:
    alert_id = int(request.path_params["alert_id"])

    def read() -> dict[str, Any]:
        items = _records(q.evidence_for_alert(alert_id))
        return {"items": items, "count": len(items)}

    return JSONResponse(_guard(read, "read evidence"))


def incidents(request: Request) -> JSONResponse:
    def read() -> dict[str, Any]:
        items = _records(q.incidents_list())
        return {"items": items, "count": len(items)}

    return JSONResponse(_guard(read, "read incidents"))


def incident(request: Request) -> JSONResponse:
    incident_id = int(request.path_params["incident_id"])

    def read() -> dict[str, Any]:
        header = q.incident_header(incident_id)
        if header is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        return {str(key): _jsonable(value) for key, value in header.items()}

    return JSONResponse(_guard(read, "read incident"))


def incident_timeline(request: Request) -> JSONResponse:
    incident_id = int(request.path_params["incident_id"])

    def read() -> dict[str, Any]:
        if q.incident_header(incident_id) is None:
            raise HTTPException(status_code=404, detail="Incident not found")
        items = _records(q.incident_timeline(incident_id))
        return {"items": items, "count": len(items)}

    return JSONResponse(_guard(read, "read timeline"))


async def http_exception(request: Request, exc: HTTPException) -> JSONResponse:
    return JSONResponse(
        {"detail": exc.detail}, status_code=exc.status_code
    )


routes: list[Route] = [
    Route("/api/health", health),
    Route("/api/overview", overview),
    Route("/api/alerts", alerts),
    Route("/api/alerts/filters", alert_filters),
    Route("/api/alerts/{alert_id:int}/evidence", alert_evidence),
    Route("/api/incidents", incidents),
    Route("/api/incidents/{incident_id:int}", incident),
    Route("/api/incidents/{incident_id:int}/timeline", incident_timeline),
]


def _spa(request: Request) -> Response:
    full_path = request.path_params.get("full_path", "")
    if full_path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    candidate = (FRONTEND_DIST / full_path).resolve()
    if candidate.is_file() and FRONTEND_DIST in candidate.parents:
        return FileResponse(candidate)
    if full_path.startswith("assets/"):
        raise HTTPException(status_code=404, detail="Asset not found")
    return FileResponse(FRONTEND_DIST / "index.html")


if FRONTEND_DIST.exists():
    assets_dir = FRONTEND_DIST / "assets"
    if assets_dir.exists():
        routes.append(Mount("/assets", app=StaticFiles(directory=assets_dir), name="assets"))
    routes.append(Route("/{full_path:path}", _spa))
else:

    def api_root(request: Request) -> JSONResponse:
        return JSONResponse(
            {
                "service": "SENTRIX API",
                "read_only": True,
                "frontend": "Run `npm install && npm run build` inside frontend/",
            }
        )

    routes.append(Route("/", api_root))


_origins = os.environ.get(
    "SENTRIX_CORS_ORIGINS",
    "http://localhost:5173,http://127.0.0.1:5173,"
    "http://localhost:4173,http://127.0.0.1:4173",
)

app = Starlette(
    debug=False,
    routes=routes,
    exception_handlers={HTTPException: http_exception},
)
app = CORSMiddleware(
    app,
    allow_origins=[origin.strip() for origin in _origins.split(",") if origin.strip()],
    allow_credentials=False,
    allow_methods=["GET"],
    allow_headers=["*"],
)
