#!/usr/bin/env python3
"""Render the public Baseline fleet status from intent plus live GitHub facts.

The renderer deliberately has no third-party dependencies.  It reads other repositories
only through GitHub's API at explicit revisions; it never discovers or opens sibling
checkouts.  Remote failures become public UNKNOWN rows, while invalid local intent fails
closed before a Pages artifact is replaced.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any, Mapping


API_ROOT = "https://api.github.com"
INTENT_SCHEMA = "baseline-fleet-intent/v1"
STATUS_SCHEMA = "baseline-fleet-status/v1"
CLAIM_STATES = {"VERIFIED", "INFERRED", "BLOCKED", "UNVERIFIED"}
VISIBILITY_MODES = {"full", "sanitized"}
SEAM_KINDS = {"revision_lock", "package_version"}
SHA40 = re.compile(r"^[0-9a-f]{40}$")
REPOSITORY = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")
SAFE_ID = re.compile(r"^[a-z0-9][a-z0-9-]*$")
FORBIDDEN_PUBLIC = re.compile(
    r"(?i)(?:https?://[^\s]*\.ts\.net|\btailnet\b|[A-Za-z]:\\|/home/|"
    r"(?:password|secret|token|api[_-]?key)\s*[:=])"
)


class ConfigError(ValueError):
    """The tracked intent contract is invalid and must not be published."""


class RemoteError(RuntimeError):
    """A live GitHub fact could not be read."""

    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


def parse_datetime(value: str) -> dt.datetime:
    parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def utc_now() -> dt.datetime:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0)


def days_since(value: dt.date, today: dt.date) -> int:
    return max(0, (today - value).days)


def activity_label(days: int) -> str:
    if days == 0:
        return "today"
    if days == 1:
        return "1 day ago"
    return f"{days} days ago"


def _safe_repo_path(value: Any, field: str) -> str:
    if not isinstance(value, str) or not value:
        raise ConfigError(f"{field} must be a non-empty repository-relative path")
    normalized = value.replace("\\", "/")
    if normalized.startswith("/") or ":" in normalized or ".." in normalized.split("/"):
        raise ConfigError(f"{field} must stay inside its owning repository")
    return normalized


def _public_text(value: Any, field: str, *, nullable: bool = False) -> str | None:
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not value.strip():
        raise ConfigError(f"{field} must be non-empty text")
    clean = " ".join(value.split())
    if len(clean) > 600:
        raise ConfigError(f"{field} exceeds 600 characters")
    if FORBIDDEN_PUBLIC.search(clean):
        raise ConfigError(f"{field} contains a private path, endpoint, or secret-shaped value")
    return clean


def validate_intent(data: Any, *, today: dt.date | None = None) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ConfigError("intent root must be an object")
    if data.get("schema") != INTENT_SCHEMA:
        raise ConfigError(f"schema must be {INTENT_SCHEMA}")
    _public_text(data.get("title"), "title")
    review_days = data.get("review_after_days")
    if not isinstance(review_days, int) or not 1 <= review_days <= 365:
        raise ConfigError("review_after_days must be an integer from 1 through 365")

    repositories = data.get("repositories")
    if not isinstance(repositories, list) or not repositories:
        raise ConfigError("repositories must be a non-empty array")
    ids: set[str] = set()
    github_names: set[str] = set()
    check_day = today or utc_now().date()
    for index, repo in enumerate(repositories):
        prefix = f"repositories[{index}]"
        if not isinstance(repo, dict):
            raise ConfigError(f"{prefix} must be an object")
        repo_id = repo.get("id")
        if not isinstance(repo_id, str) or not SAFE_ID.fullmatch(repo_id):
            raise ConfigError(f"{prefix}.id must be a lowercase stable identifier")
        if repo_id in ids:
            raise ConfigError(f"duplicate repository id: {repo_id}")
        ids.add(repo_id)
        github = repo.get("github")
        if not isinstance(github, str) or not REPOSITORY.fullmatch(github):
            raise ConfigError(f"{prefix}.github must be owner/repository")
        if github.lower() in github_names:
            raise ConfigError(f"duplicate GitHub repository: {github}")
        github_names.add(github.lower())
        branch = repo.get("branch")
        if not isinstance(branch, str) or not branch or any(c in branch for c in " \t\\"):
            raise ConfigError(f"{prefix}.branch is invalid")
        workflow = repo.get("workflow")
        if not isinstance(workflow, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+\.ya?ml", workflow):
            raise ConfigError(f"{prefix}.workflow must be a workflow filename")
        if repo.get("visibility") not in VISIBILITY_MODES:
            raise ConfigError(f"{prefix}.visibility must be full or sanitized")
        if repo.get("claim_state") not in CLAIM_STATES:
            raise ConfigError(f"{prefix}.claim_state must follow PD-4")
        for field in (
            "name",
            "purpose",
            "current_focus",
            "next_outcome",
            "done_when",
        ):
            _public_text(repo.get(field), f"{prefix}.{field}")
        _public_text(repo.get("blocker"), f"{prefix}.blocker", nullable=True)
        try:
            intent_day = dt.date.fromisoformat(repo.get("intent_as_of", ""))
        except (TypeError, ValueError) as exc:
            raise ConfigError(f"{prefix}.intent_as_of must be YYYY-MM-DD") from exc
        if intent_day > check_day:
            raise ConfigError(f"{prefix}.intent_as_of cannot be in the future")

    seams = data.get("seams")
    if not isinstance(seams, list):
        raise ConfigError("seams must be an array")
    seam_ids: set[str] = set()
    for index, seam in enumerate(seams):
        prefix = f"seams[{index}]"
        if not isinstance(seam, dict):
            raise ConfigError(f"{prefix} must be an object")
        seam_id = seam.get("id")
        if not isinstance(seam_id, str) or not SAFE_ID.fullmatch(seam_id):
            raise ConfigError(f"{prefix}.id must be a lowercase stable identifier")
        if seam_id in seam_ids:
            raise ConfigError(f"duplicate seam id: {seam_id}")
        seam_ids.add(seam_id)
        if seam.get("kind") not in SEAM_KINDS:
            raise ConfigError(f"{prefix}.kind is unsupported")
        if seam.get("producer") not in ids or seam.get("consumer") not in ids:
            raise ConfigError(f"{prefix} refers to an unknown repository")
        _public_text(seam.get("label"), f"{prefix}.label")
        _public_text(seam.get("artifact"), f"{prefix}.artifact")
        if seam["kind"] == "revision_lock":
            _safe_repo_path(seam.get("consumer_path"), f"{prefix}.consumer_path")
            if not isinstance(seam.get("revision_field"), str) or not seam["revision_field"]:
                raise ConfigError(f"{prefix}.revision_field is required")
            label_field = seam.get("label_field")
            if label_field is not None and not isinstance(label_field, str):
                raise ConfigError(f"{prefix}.label_field must be text")
        else:
            for side in ("producer_value", "consumer_value"):
                spec = seam.get(side)
                if not isinstance(spec, dict):
                    raise ConfigError(f"{prefix}.{side} must be an object")
                _safe_repo_path(spec.get("path"), f"{prefix}.{side}.path")
                if spec.get("format") not in {"xml_text", "xml_attribute"}:
                    raise ConfigError(f"{prefix}.{side}.format is unsupported")
                if not isinstance(spec.get("selector"), str) or not spec["selector"]:
                    raise ConfigError(f"{prefix}.{side}.selector is required")
                if spec["format"] == "xml_attribute" and not isinstance(spec.get("attribute"), str):
                    raise ConfigError(f"{prefix}.{side}.attribute is required")
    return data


def load_intent(path: Path, *, today: dt.date | None = None) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ConfigError(f"cannot read intent: {exc}") from exc
    return validate_intent(data, today=today)


class GitHubClient:
    def __init__(self, token: str | None = None, *, timeout: int = 15):
        self.token = token or ""
        self.timeout = timeout

    def _get_json(self, path: str) -> Any:
        request = urllib.request.Request(
            API_ROOT + path,
            headers={
                "Accept": "application/vnd.github+json",
                "X-GitHub-Api-Version": "2022-11-28",
                "User-Agent": "baseline-fleet-status/1",
                **({"Authorization": f"Bearer {self.token}"} if self.token else {}),
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                return json.loads(response.read().decode("utf-8"))
        except urllib.error.HTTPError as exc:
            if exc.code == 404:
                raise RemoteError("NOT_FOUND") from exc
            if exc.code in {403, 429}:
                raise RemoteError("RATE_LIMITED") from exc
            if exc.code in {401}:
                raise RemoteError("UNAUTHORIZED") from exc
            raise RemoteError("HTTP_ERROR") from exc
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError):
            raise RemoteError("API_UNAVAILABLE")

    def commit(self, repository: str, branch: str) -> dict[str, Any]:
        encoded = urllib.parse.quote(branch, safe="")
        data = self._get_json(f"/repos/{repository}/commits/{encoded}")
        commit = data.get("commit", {})
        author = commit.get("committer") or commit.get("author") or {}
        message = str(commit.get("message") or "").splitlines()[0]
        return {
            "sha": str(data["sha"]),
            "date": str(author["date"]),
            "subject": message,
            "url": str(data.get("html_url") or f"https://github.com/{repository}/commit/{data['sha']}"),
        }

    def workflow_runs(self, repository: str, workflow: str, branch: str) -> list[dict[str, Any]]:
        workflow_name = urllib.parse.quote(workflow, safe="")
        query = urllib.parse.urlencode({"branch": branch, "per_page": 20})
        data = self._get_json(
            f"/repos/{repository}/actions/workflows/{workflow_name}/runs?{query}"
        )
        runs = data.get("workflow_runs")
        if not isinstance(runs, list):
            raise RemoteError("MALFORMED_RESPONSE")
        return runs

    def file_text(self, repository: str, revision: str, path: str) -> str:
        encoded_path = urllib.parse.quote(path, safe="/")
        query = urllib.parse.urlencode({"ref": revision})
        data = self._get_json(f"/repos/{repository}/contents/{encoded_path}?{query}")
        if data.get("encoding") != "base64" or not isinstance(data.get("content"), str):
            raise RemoteError("MALFORMED_RESPONSE")
        try:
            return base64.b64decode(data["content"], validate=False).decode("utf-8")
        except (ValueError, UnicodeDecodeError) as exc:
            raise RemoteError("MALFORMED_RESPONSE") from exc

    def compare(self, repository: str, base: str, head: str) -> str:
        base_ref = urllib.parse.quote(base, safe="")
        head_ref = urllib.parse.quote(head, safe="")
        data = self._get_json(f"/repos/{repository}/compare/{base_ref}...{head_ref}")
        status = data.get("status")
        if status not in {"ahead", "behind", "diverged", "identical"}:
            raise RemoteError("MALFORMED_RESPONSE")
        return str(status)


class FixtureClient:
    """Small deterministic GitHub stand-in used by tests and offline previews."""

    def __init__(self, fixture: Mapping[str, Any]):
        self.fixture = fixture

    @classmethod
    def from_path(cls, path: Path) -> "FixtureClient":
        return cls(json.loads(path.read_text(encoding="utf-8")))

    def _repo(self, repository: str) -> Mapping[str, Any]:
        try:
            value = self.fixture["repositories"][repository]
        except KeyError as exc:
            raise RemoteError("NOT_FOUND") from exc
        error = value.get("error")
        if error:
            raise RemoteError(str(error))
        return value

    def commit(self, repository: str, branch: str) -> dict[str, Any]:
        del branch
        return dict(self._repo(repository)["commit"])

    def workflow_runs(self, repository: str, workflow: str, branch: str) -> list[dict[str, Any]]:
        del branch
        repo = self._repo(repository)
        try:
            value = repo["workflows"][workflow]
        except KeyError as exc:
            raise RemoteError("NOT_FOUND") from exc
        if isinstance(value, dict) and value.get("error"):
            raise RemoteError(str(value["error"]))
        return [dict(run) for run in value]

    def file_text(self, repository: str, revision: str, path: str) -> str:
        del revision
        repo = self._repo(repository)
        try:
            value = repo["files"][path]
        except KeyError as exc:
            raise RemoteError("NOT_FOUND") from exc
        if isinstance(value, dict) and value.get("error"):
            raise RemoteError(str(value["error"]))
        return str(value)

    def compare(self, repository: str, base: str, head: str) -> str:
        repo = self._repo(repository)
        try:
            value = repo["compares"][f"{base}...{head}"]
        except KeyError as exc:
            raise RemoteError("NOT_FOUND") from exc
        if isinstance(value, dict) and value.get("error"):
            raise RemoteError(str(value["error"]))
        return str(value)


def _ci_state(runs: list[dict[str, Any]], head_sha: str) -> tuple[str, str | None]:
    run = next((item for item in runs if item.get("head_sha") == head_sha), None)
    if run is None:
        return "UNVERIFIED", None
    status = str(run.get("status") or "")
    if status != "completed":
        return "RUNNING", str(run.get("html_url") or "") or None
    conclusion = str(run.get("conclusion") or "").lower()
    if conclusion == "success":
        return "PASS", str(run.get("html_url") or "") or None
    return "FAIL", str(run.get("html_url") or "") or None


def _warning(warnings: list[dict[str, str]], scope: str, code: str) -> None:
    warnings.append({"scope": scope, "code": code})


def _extract_xml_value(text: str, spec: Mapping[str, Any]) -> str:
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        raise RemoteError("MALFORMED_CONTRACT") from exc
    node = root.find(str(spec["selector"]))
    if node is None:
        raise RemoteError("MISSING_CONTRACT_VALUE")
    if spec["format"] == "xml_attribute":
        value = node.get(str(spec["attribute"]))
    else:
        value = node.text
    if value is None or not value.strip():
        raise RemoteError("MISSING_CONTRACT_VALUE")
    return value.strip()


def _exact_package(value: str) -> tuple[bool, str]:
    raw = value.strip()
    if raw.startswith("[") and raw.endswith("]") and "," not in raw:
        raw = raw[1:-1].strip()
    elif any(character in raw for character in "[](),*"):
        return False, raw
    if not re.fullmatch(r"[0-9A-Za-z][0-9A-Za-z.+-]*", raw):
        return False, raw
    return True, raw


def collect_status(
    intent: Mapping[str, Any], client: GitHubClient | FixtureClient, *, now: dt.datetime
) -> dict[str, Any]:
    now = now.astimezone(dt.timezone.utc).replace(microsecond=0)
    today = now.date()
    warnings: list[dict[str, str]] = []
    rows: list[dict[str, Any]] = []
    internal: dict[str, dict[str, Any]] = {}
    degraded = False

    for config in intent["repositories"]:
        repo_id = config["id"]
        intent_day = dt.date.fromisoformat(config["intent_as_of"])
        intent_age = days_since(intent_day, today)
        stale_intent = intent_age > int(intent["review_after_days"])
        row: dict[str, Any] = {
            "id": repo_id,
            "name": config["name"],
            "purpose": config["purpose"],
            "current_focus": config["current_focus"],
            "next_outcome": config["next_outcome"],
            "done_when": config["done_when"],
            "blocker": config["blocker"],
            "claim_state": config["claim_state"],
            "intent_as_of": config["intent_as_of"],
            "intent_age_days": intent_age,
            "intent_state": "STALE" if stale_intent else "CURRENT",
            "ci_state": "UNKNOWN",
            "visibility": config["visibility"],
        }
        if stale_intent:
            _warning(warnings, repo_id, "STALE_INTENT")
        try:
            commit = client.commit(config["github"], config["branch"])
            if not isinstance(commit, Mapping):
                raise RemoteError("MALFORMED_RESPONSE")
            sha = commit.get("sha")
            commit_date = commit.get("date")
            subject = commit.get("subject")
            commit_url = commit.get("url")
            if (
                not isinstance(sha, str)
                or not SHA40.fullmatch(sha)
                or not isinstance(commit_date, str)
                or not isinstance(subject, str)
                or not isinstance(commit_url, str)
            ):
                raise RemoteError("MALFORMED_RESPONSE")
            try:
                commit_time = parse_datetime(commit_date)
            except (TypeError, ValueError) as exc:
                raise RemoteError("MALFORMED_RESPONSE") from exc
            internal[repo_id] = {"config": config, "head": sha}
            try:
                runs = client.workflow_runs(config["github"], config["workflow"], config["branch"])
                if not isinstance(runs, list) or not all(isinstance(run, dict) for run in runs):
                    raise RemoteError("MALFORMED_RESPONSE")
                ci_state, ci_url = _ci_state(runs, sha)
            except RemoteError as exc:
                ci_state, ci_url = "UNKNOWN", None
                degraded = True
                _warning(warnings, repo_id, f"CI_{exc.code}")
            if ci_state == "FAIL":
                degraded = True
                _warning(warnings, repo_id, "CI_FAILED")
            elif ci_state == "UNVERIFIED":
                degraded = True
                _warning(warnings, repo_id, "NO_CI_FOR_HEAD")
            row["ci_state"] = ci_state
            if config["visibility"] == "full":
                row.update(
                    {
                        "repository_url": f"https://github.com/{config['github']}",
                        "head_sha": sha,
                        "head_url": commit_url,
                        "latest_change": subject,
                        "updated_at": commit_time.isoformat().replace("+00:00", "Z"),
                        "activity_days": days_since(commit_time.date(), today),
                        "ci_url": ci_url,
                    }
                )
            else:
                row["private_detail"] = "Private repository details withheld"
        except RemoteError as exc:
            degraded = True
            internal[repo_id] = {"config": config, "head": None}
            _warning(warnings, repo_id, f"REPOSITORY_{exc.code}")
            if config["visibility"] == "full":
                row["repository_url"] = f"https://github.com/{config['github']}"
                row["latest_change"] = "Unavailable"
            else:
                row["private_detail"] = "Private repository details withheld"
        rows.append(row)

    seams: list[dict[str, Any]] = []
    names = {repo["id"]: repo["name"] for repo in intent["repositories"]}
    for config in intent["seams"]:
        seam = {
            "id": config["id"],
            "label": config["label"],
            "artifact": config["artifact"],
            "producer": names[config["producer"]],
            "consumer": names[config["consumer"]],
            "state": "UNKNOWN",
            "producer_value": "unknown",
            "consumer_value": "unknown",
        }
        producer = internal.get(config["producer"], {})
        consumer = internal.get(config["consumer"], {})
        producer_head = producer.get("head")
        consumer_head = consumer.get("head")
        if not producer_head or not consumer_head:
            degraded = True
            _warning(warnings, config["id"], "SEAM_SOURCE_UNAVAILABLE")
            seams.append(seam)
            continue
        try:
            if config["kind"] == "revision_lock":
                text = client.file_text(
                    consumer["config"]["github"], consumer_head, config["consumer_path"]
                )
                if not isinstance(text, str):
                    raise RemoteError("MALFORMED_RESPONSE")
                try:
                    lock = json.loads(text)
                except json.JSONDecodeError as exc:
                    raise RemoteError("MALFORMED_CONTRACT") from exc
                pinned = lock.get(config["revision_field"])
                if not isinstance(pinned, str) or not SHA40.fullmatch(pinned):
                    raise RemoteError("MALFORMED_CONTRACT")
                label = lock.get(config.get("label_field")) if config.get("label_field") else None
                seam["producer_value"] = producer_head[:12]
                seam["consumer_value"] = f"{label} · {pinned[:12]}" if label else pinned[:12]
                if pinned == producer_head:
                    seam["state"] = "CURRENT"
                else:
                    comparison = client.compare(producer["config"]["github"], pinned, producer_head)
                    if comparison not in {"ahead", "behind", "diverged", "identical"}:
                        raise RemoteError("MALFORMED_RESPONSE")
                    seam["state"] = "PINNED_BEHIND" if comparison == "ahead" else "DIVERGED"
            else:
                producer_text = client.file_text(
                    producer["config"]["github"], producer_head, config["producer_value"]["path"]
                )
                consumer_text = client.file_text(
                    consumer["config"]["github"], consumer_head, config["consumer_value"]["path"]
                )
                if not isinstance(producer_text, str) or not isinstance(consumer_text, str):
                    raise RemoteError("MALFORMED_RESPONSE")
                producer_value = _extract_xml_value(producer_text, config["producer_value"])
                consumer_value = _extract_xml_value(consumer_text, config["consumer_value"])
                producer_exact, normalized_producer = _exact_package(producer_value)
                consumer_exact, normalized_consumer = _exact_package(consumer_value)
                seam["producer_value"] = producer_value
                seam["consumer_value"] = consumer_value
                if not producer_exact or not consumer_exact:
                    seam["state"] = "BROKEN"
                elif normalized_consumer == normalized_producer:
                    seam["state"] = "CURRENT"
                else:
                    seam["state"] = "PINNED_DIFFERENT"
        except RemoteError as exc:
            seam["state"] = "UNKNOWN" if exc.code in {
                "API_UNAVAILABLE",
                "RATE_LIMITED",
                "UNAUTHORIZED",
                "HTTP_ERROR",
                "MALFORMED_RESPONSE",
            } else "BROKEN"
            _warning(warnings, config["id"], f"SEAM_{exc.code}")
        if seam["state"] in {"UNKNOWN", "BROKEN", "DIVERGED"}:
            degraded = True
        seams.append(seam)

    overall = "ATTENTION" if degraded else ("REVIEW" if any(r["intent_state"] == "STALE" for r in rows) else "HEALTHY")
    return {
        "schema": STATUS_SCHEMA,
        "title": intent["title"],
        "generated_at": now.isoformat().replace("+00:00", "Z"),
        "overall": overall,
        "degraded": degraded,
        "review_after_days": intent["review_after_days"],
        "repositories": rows,
        "seams": seams,
        "warnings": warnings,
    }


def _md(value: Any) -> str:
    if value is None or value == "":
        return "—"
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def _link(label: str, url: str | None) -> str:
    escaped = html.escape(label)
    if not url:
        return escaped
    return f'<a href="{html.escape(url, quote=True)}">{escaped}</a>'


def _badge(value: str) -> str:
    css = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return f'<span class="badge {css}">{html.escape(value)}</span>'


def render_html(model: Mapping[str, Any]) -> str:
    current_rows: list[str] = []
    direction_rows: list[str] = []
    seam_rows: list[str] = []
    for repo in model["repositories"]:
        project = _link(repo["name"], repo.get("repository_url"))
        if repo["visibility"] == "sanitized":
            change = html.escape(repo["private_detail"])
            activity = "Withheld"
            ci = _badge(repo["ci_state"])
        else:
            sha = str(repo.get("head_sha") or "")[:8]
            subject = repo.get("latest_change") or "Unavailable"
            change = _link(f"{sha} · {subject}" if sha else subject, repo.get("head_url"))
            activity = activity_label(int(repo.get("activity_days") or 0)) if repo.get("updated_at") else "Unknown"
            ci = _link(repo["ci_state"], repo.get("ci_url")) if repo.get("ci_url") else _badge(repo["ci_state"])
        current_rows.append(
            "<tr>"
            f"<th scope=\"row\">{project}</th>"
            f"<td><span class=\"purpose\">{html.escape(repo['purpose'])}</span>{html.escape(repo['current_focus'])}</td>"
            f"<td>{change}</td><td>{ci}</td><td>{html.escape(activity)}</td>"
            f"<td>{_badge(repo['claim_state'])}</td></tr>"
        )
        reviewed = f"{repo['intent_as_of']} · {repo['intent_age_days']}d"
        if repo["intent_state"] == "STALE":
            reviewed += " · STALE"
        direction_rows.append(
            "<tr>"
            f"<th scope=\"row\">{html.escape(repo['name'])}</th>"
            f"<td>{html.escape(repo['next_outcome'])}</td>"
            f"<td>{html.escape(repo['done_when'])}</td>"
            f"<td>{html.escape(repo['blocker'] or '—')}</td>"
            f"<td>{_badge(repo['intent_state'])}<br><span class=\"small\">{html.escape(reviewed)}</span></td>"
            "</tr>"
        )
    for seam in model["seams"]:
        seam_rows.append(
            "<tr>"
            f"<th scope=\"row\">{html.escape(seam['label'])}</th>"
            f"<td>{html.escape(seam['artifact'])}</td>"
            f"<td>{html.escape(seam['producer'])}<br><code>{html.escape(seam['producer_value'])}</code></td>"
            f"<td>{html.escape(seam['consumer'])}<br><code>{html.escape(seam['consumer_value'])}</code></td>"
            f"<td>{_badge(seam['state'])}</td></tr>"
        )
    generated = html.escape(model["generated_at"])
    title = html.escape(model["title"])
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{title}</title>
<meta name="description" content="Live repository health, intended outcomes, and integration pins for the Comfy Valheim project fleet.">
<link rel="canonical" href="https://djcdevelopment.github.io/baseline/status/">
<style>
:root{{--bg:#0e1412;--panel:#151e1a;--ink:#edf4ef;--muted:#9eb0a5;--line:#314038;--accent:#84d3a1;--warn:#f0c36a;--bad:#ee8b83;--mono:ui-monospace,SFMono-Regular,Consolas,monospace}}
*{{box-sizing:border-box}} body{{margin:0;background:var(--bg);color:var(--ink);font:16px/1.5 system-ui,sans-serif}}
main{{max-width:1180px;margin:auto;padding:2rem 1rem 4rem}} a{{color:var(--accent)}} h1{{font-size:clamp(2rem,5vw,3.5rem);margin:.3rem 0}} h2{{margin:2.5rem 0 .7rem}}
.lede,.small,.purpose{{color:var(--muted)}} .purpose{{display:block;font-size:.86rem;margin-bottom:.35rem}} .small{{font-size:.78rem}} .links{{display:flex;gap:1rem;flex-wrap:wrap}}
.summary{{background:var(--panel);border:1px solid var(--line);border-radius:.6rem;padding:1rem;margin:1.2rem 0}}
.table-wrap{{overflow-x:auto;border:1px solid var(--line);border-radius:.6rem}} table{{width:100%;border-collapse:collapse;background:var(--panel);min-width:820px}}
th,td{{text-align:left;vertical-align:top;padding:.75rem;border-bottom:1px solid var(--line)}} thead th{{font-size:.75rem;text-transform:uppercase;letter-spacing:.06em;color:var(--muted)}} tbody tr:last-child>*{{border-bottom:0}}
code{{font-family:var(--mono);font-size:.78rem}} .badge{{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:.12rem .48rem;font:700 .72rem/1.4 var(--mono)}}
.pass,.healthy,.current,.verified{{border-color:var(--accent);color:var(--accent)}} .fail,.attention,.broken,.diverged,.unknown,.unverified{{border-color:var(--bad);color:var(--bad)}} .running,.review,.stale,.blocked,.pinned-behind,.pinned-different,.inferred{{border-color:var(--warn);color:var(--warn)}}
footer{{margin-top:3rem;color:var(--muted);font-size:.85rem}}
</style>
</head>
<body><main>
<nav class="links"><a href="../">Baseline home</a><a href="status.md">Markdown</a><a href="status.json">JSON</a></nav>
<p class="small">Living fleet projection</p><h1>{title}</h1>
<p class="lede">One public view of what is moving, what comes next, and whether the immutable handoffs between repositories still say what we think they say.</p>
<div class="summary">Overall {_badge(model['overall'])} <span class="small">Generated {generated}. Intent is marked stale after {model['review_after_days']} days.</span></div>
<h2>Fleet now</h2><div class="table-wrap"><table><thead><tr><th>Project</th><th>Purpose and current focus</th><th>Latest change</th><th>CI</th><th>Activity</th><th>Evidence</th></tr></thead><tbody>{''.join(current_rows)}</tbody></table></div>
<h2>Where we are going</h2><div class="table-wrap"><table><thead><tr><th>Project</th><th>Next user-visible outcome</th><th>Done when</th><th>Blocker</th><th>Reviewed</th></tr></thead><tbody>{''.join(direction_rows)}</tbody></table></div>
<h2>Integration seams</h2><div class="table-wrap"><table><thead><tr><th>Boundary</th><th>Artifact or contract</th><th>Producer</th><th>Consumer pin</th><th>State</th></tr></thead><tbody>{''.join(seam_rows)}</tbody></table></div>
<footer>Observed state comes from GitHub at page-build time. Intended direction comes from Baseline's reviewed fleet intent contract. A green run counts only when it belongs to the repository's current main HEAD.</footer>
</main></body></html>
"""


def render_markdown(model: Mapping[str, Any]) -> str:
    lines = [
        f"# {model['title']}",
        "",
        f"Generated `{model['generated_at']}` · overall **{model['overall']}** · intent warning after {model['review_after_days']} days.",
        "",
        "## Fleet now",
        "",
        "| Project | Purpose and current focus | Latest change | CI | Activity | Evidence |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for repo in model["repositories"]:
        if repo["visibility"] == "sanitized":
            project = repo["name"]
            change = repo["private_detail"]
            activity = "Withheld"
        else:
            project = f"[{repo['name']}]({repo['repository_url']})"
            sha = str(repo.get("head_sha") or "")[:8]
            subject = repo.get("latest_change") or "Unavailable"
            change = f"[{sha} · {subject}]({repo['head_url']})" if sha else subject
            activity = activity_label(int(repo.get("activity_days") or 0)) if repo.get("updated_at") else "Unknown"
        lines.append(
            "| " + " | ".join(
                _md(value)
                for value in (
                    project,
                    f"{repo['purpose']} {repo['current_focus']}",
                    change,
                    repo["ci_state"],
                    activity,
                    repo["claim_state"],
                )
            ) + " |"
        )
    lines.extend(
        [
            "",
            "## Where we are going",
            "",
            "| Project | Next user-visible outcome | Done when | Blocker | Reviewed |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for repo in model["repositories"]:
        reviewed = f"{repo['intent_as_of']} · {repo['intent_age_days']}d · {repo['intent_state']}"
        lines.append(
            "| " + " | ".join(
                _md(value)
                for value in (
                    repo["name"],
                    repo["next_outcome"],
                    repo["done_when"],
                    repo["blocker"],
                    reviewed,
                )
            ) + " |"
        )
    lines.extend(
        [
            "",
            "## Integration seams",
            "",
            "| Boundary | Artifact or contract | Producer | Consumer pin | State |",
            "| --- | --- | --- | --- | --- |",
        ]
    )
    for seam in model["seams"]:
        lines.append(
            "| " + " | ".join(
                _md(value)
                for value in (
                    seam["label"],
                    seam["artifact"],
                    f"{seam['producer']} · {seam['producer_value']}",
                    f"{seam['consumer']} · {seam['consumer_value']}",
                    seam["state"],
                )
            ) + " |"
        )
    lines.extend(
        [
            "",
            "Observed state comes from GitHub at page-build time. Intended direction comes from Baseline's reviewed fleet intent contract.",
            "",
        ]
    )
    return "\n".join(lines)


def write_outputs(model: Mapping[str, Any], output: Path) -> None:
    output.mkdir(parents=True, exist_ok=True)
    (output / "index.html").write_text(render_html(model), encoding="utf-8", newline="\n")
    (output / "status.md").write_text(render_markdown(model), encoding="utf-8", newline="\n")
    (output / "status.json").write_text(
        json.dumps(model, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n"
    )


def _write_actions_output(model: Mapping[str, Any]) -> None:
    output = os.environ.get("GITHUB_OUTPUT")
    if not output:
        return
    with open(output, "a", encoding="utf-8", newline="\n") as stream:
        stream.write(f"degraded={'true' if model['degraded'] else 'false'}\n")
        stream.write(f"warning_count={len(model['warnings'])}\n")
        stream.write(f"overall={model['overall']}\n")


def main(argv: list[str] | None = None) -> int:
    root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--intent", type=Path, default=root / "fleet" / "intent.json")
    parser.add_argument("--output", type=Path, default=root / "site" / "status")
    parser.add_argument("--fixture", type=Path, help="deterministic GitHub fixture for offline rendering")
    parser.add_argument("--now", help="override current UTC time for deterministic output")
    parser.add_argument("--check-config", action="store_true", help="validate tracked intent without network access")
    args = parser.parse_args(argv)
    now = parse_datetime(args.now) if args.now else utc_now()
    try:
        intent = load_intent(args.intent, today=now.date())
        if args.check_config:
            print(f"Fleet intent OK: {len(intent['repositories'])} repositories, {len(intent['seams'])} seams")
            return 0
        if args.fixture:
            client: GitHubClient | FixtureClient = FixtureClient.from_path(args.fixture)
        else:
            token = os.environ.get("FLEET_READ_TOKEN") or os.environ.get("GITHUB_TOKEN")
            client = GitHubClient(token)
        model = collect_status(intent, client, now=now)
        write_outputs(model, args.output)
        _write_actions_output(model)
        print(
            f"Fleet status {model['overall']}: {len(model['repositories'])} repositories, "
            f"{len(model['seams'])} seams, {len(model['warnings'])} warning(s)"
        )
        for warning in model["warnings"]:
            print(f"Fleet warning: {warning['scope']} {warning['code']}")
        return 0
    except ConfigError as exc:
        print(f"fleet status configuration error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
