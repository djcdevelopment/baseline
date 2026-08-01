"""Development-only bridge to the local Baseline Workbench API.

The bridge is deliberately thin: the Workbench registry remains the policy and
execution boundary.  MCP can inspect, start, cancel, and read jobs, but it never
receives a shell, Docker socket, repository write path, or gameplay command path.
Production profiles do not mount or start this provider.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import Request, urlopen


CAPABILITY_IDS = frozenset(
    {
        "explore.system.inspect",
        "explore.evidence.list",
        "build.mod.release",
        "build.rendered.c6-role-reversal",
        "operate.mod.check",
        "operate.mod.install",
        "operate.mod.rollback",
        "operate.transport.capture",
        "recover.snapshot.create",
        "recover.support.export",
        "recover.recreate.verify",
    }
)


def _base_url() -> str:
    value = os.environ.get("COMFY_WORKBENCH_URL", "http://companion:8080").rstrip("/")
    if not value.startswith(("http://", "https://")):
        raise ValueError("COMFY_WORKBENCH_URL must be an HTTP URL")
    return value


def _token() -> str:
    path = os.environ.get("COMFY_WORKBENCH_TOKEN_FILE", "/data/workbench/browser-token")
    token = Path(path).read_text(encoding="utf-8").strip()
    if not token:
        raise RuntimeError("Workbench browser token is empty")
    return token


def _request(path: str, method: str = "GET", payload: dict[str, Any] | None = None) -> dict[str, Any]:
    body = None if payload is None else json.dumps(payload, separators=(",", ":")).encode("utf-8")
    headers = {"Accept": "application/json", "X-Workbench-Token": _token()}
    if body is not None:
        headers["Content-Type"] = "application/json"
    request = Request(f"{_base_url()}{path}", method=method, data=body, headers=headers)
    try:
        with urlopen(request, timeout=20) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {"ok": True}
    except HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"workbench_http_{exc.code}: {detail[:500]}") from exc
    except URLError as exc:
        raise RuntimeError(f"workbench_unreachable: {exc.reason}") from exc


def get_tools() -> list:
    return [
        workbench_capabilities,
        workbench_start_job,
        workbench_job,
        workbench_cancel_job,
        workbench_receipt,
    ]


def workbench_capabilities() -> dict[str, Any]:
    """List the effective local Workbench capability registry and profile."""
    return _request("/api/v1/workbench/capabilities")


def workbench_start_job(capability_id: str, target: str = "local", inputs: dict[str, Any] | None = None) -> dict[str, Any]:
    """Start one registered Workbench job; execution stays in the host runner."""
    if capability_id not in CAPABILITY_IDS:
        raise ValueError("capability_id is not in the registered Workbench set")
    if len(target) > 40 or any(ch not in "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_" for ch in target):
        raise ValueError("target contains unsupported characters")
    if inputs is not None and not isinstance(inputs, dict):
        raise ValueError("inputs must be an object")
    return _request(
        f"/api/v1/workbench/capabilities/{quote(capability_id, safe='')}/jobs",
        method="POST",
        payload={"target": target, "inputs": inputs or {}},
    )


def workbench_job(job_id: str) -> dict[str, Any]:
    """Read a Workbench job and its durable event stream."""
    if not job_id.startswith("job-") or len(job_id) > 100:
        raise ValueError("invalid Workbench job id")
    job = _request(f"/api/v1/workbench/jobs/{quote(job_id, safe='')}")
    events = _request(f"/api/v1/workbench/jobs/{quote(job_id, safe='')}/events")
    return {"job": job, "events": events.get("events", [])}


def workbench_cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel a queued or leased Workbench job through the shared API."""
    if not job_id.startswith("job-") or len(job_id) > 100:
        raise ValueError("invalid Workbench job id")
    return _request(f"/api/v1/workbench/jobs/{quote(job_id, safe='')}/cancel", method="POST", payload={})


def workbench_receipt(job_id: str) -> dict[str, Any]:
    """Read a completed Workbench receipt; no raw player-bearing logs are added."""
    if not job_id.startswith("job-") or len(job_id) > 100:
        raise ValueError("invalid Workbench job id")
    return _request(f"/api/v1/workbench/jobs/{quote(job_id, safe='')}/receipt")
