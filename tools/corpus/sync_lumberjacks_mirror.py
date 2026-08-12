#!/usr/bin/env python3
"""Refresh Baseline's Lumberjacks corpus mirror from one immutable revision."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
MIRROR_ROOT = ROOT / "corpus" / "mirrors" / "lumberjacks"
UPSTREAM = "djcdevelopment/lumberjacks-platform"
FILES = {
    "workbench.json": "Lumberjacks/docs/workbench/workbench.json",
    "commit-notes.jsonl": "Lumberjacks/docs/roadmap/commit-notes.jsonl",
}
REVISION_PATTERN = re.compile(r"^[0-9a-f]{40}$")


class SyncError(Exception):
    pass


def sha256(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def github_token() -> str | None:
    for name in ("GH_TOKEN", "GITHUB_TOKEN"):
        value = os.environ.get(name)
        if value:
            return value.strip()
    try:
        completed = subprocess.run(
            ["gh", "auth", "token"],
            check=True,
            capture_output=True,
            text=True,
        )
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None
    return completed.stdout.strip() or None


def fetch(revision: str, upstream_path: str, token: str | None) -> tuple[str, bytes]:
    url = f"https://raw.githubusercontent.com/{UPSTREAM}/{revision}/{upstream_path}"
    headers = {"User-Agent": "baseline-corpus-mirror/v1"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    request = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return url, response.read()
    except urllib.error.HTTPError as exc:
        if exc.code in {401, 403, 404} and not token:
            raise SyncError(
                f"cannot read {upstream_path} from the private upstream; run `gh auth login` "
                "or set GH_TOKEN"
            ) from exc
        raise SyncError(f"cannot fetch {url}: HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise SyncError(f"cannot fetch {url}: {exc.reason}") from exc


def atomic_write(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(dir=path.parent, prefix=f".{path.name}.", delete=False) as stream:
        stream.write(payload)
        temp_path = Path(stream.name)
    os.replace(temp_path, path)


def local_receipt(path: Path, upstream_path: str, url: str) -> dict[str, object]:
    payload = path.read_bytes()
    return {
        "upstream_path": upstream_path,
        "raw_url": url,
        "local_path": path.name,
        "sha256": sha256(payload),
        "bytes": len(payload),
    }


def check_mirror(expected_revision: str | None) -> None:
    provenance_path = MIRROR_ROOT / "provenance.json"
    if not provenance_path.is_file():
        raise SyncError("corpus/mirrors/lumberjacks/provenance.json is missing")
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    revision = provenance.get("revision")
    if expected_revision and revision != expected_revision:
        raise SyncError(f"mirror revision is {revision!r}, expected {expected_revision!r}")
    entries = provenance.get("files")
    if not isinstance(entries, list):
        raise SyncError("mirror provenance files must be an array")
    by_name = {entry.get("local_path"): entry for entry in entries if isinstance(entry, dict)}
    for local_name, upstream_path in FILES.items():
        path = MIRROR_ROOT / local_name
        if not path.is_file():
            raise SyncError(f"mirror file is missing: {local_name}")
        entry = by_name.get(local_name)
        if not entry or entry.get("upstream_path") != upstream_path:
            raise SyncError(f"mirror provenance path mismatch: {local_name}")
        payload = path.read_bytes()
        if entry.get("sha256") != sha256(payload) or entry.get("bytes") != len(payload):
            raise SyncError(f"mirror provenance does not match bytes: {local_name}")
    print(f"lumberjacks mirror matches provenance at {revision}")


def sync(revision: str) -> None:
    token = github_token()
    fetched: dict[str, tuple[str, bytes]] = {}
    for local_name, upstream_path in FILES.items():
        fetched[local_name] = fetch(revision, upstream_path, token)
    for local_name, (_, payload) in fetched.items():
        atomic_write(MIRROR_ROOT / local_name, payload)
    files = [
        local_receipt(MIRROR_ROOT / local_name, FILES[local_name], fetched[local_name][0])
        for local_name in sorted(FILES)
    ]
    provenance = {
        "schema": "baseline.corpus.mirror-provenance/v1",
        "upstream_repository": UPSTREAM,
        "revision": revision,
        "captured_at": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "files": files,
    }
    atomic_write(
        MIRROR_ROOT / "provenance.json",
        (json.dumps(provenance, indent=2, sort_keys=True) + "\n").encode("utf-8"),
    )
    check_mirror(revision)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--revision", help="exact 40-character upstream commit")
    parser.add_argument("--check", action="store_true", help="verify the committed mirror without fetching")
    args = parser.parse_args(argv)
    if args.revision and not REVISION_PATTERN.fullmatch(args.revision):
        parser.error("--revision must be a lowercase 40-character commit SHA")
    if not args.check and not args.revision:
        parser.error("--revision is required unless --check is used")
    try:
        if args.check:
            check_mirror(args.revision)
        else:
            sync(args.revision)
        return 0
    except (OSError, json.JSONDecodeError, SyncError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
