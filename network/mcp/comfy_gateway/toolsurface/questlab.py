"""Bounded local Quest Lab authoring tools.

This provider is intentionally narrower than a file browser: it accepts only Quest
Lab JSON documents, keeps writes below the configured quest root, and asks the
already-installed mod to reload through its fixed mailbox contract.  It never
executes a console command or accepts an arbitrary path.
"""

from __future__ import annotations

import base64
import json
import os
import re
import tempfile
import time
from pathlib import Path
from typing import Any

DEFAULT_VALHEIM_DIR = Path(os.environ.get(
    "COMFY_VALHEIM_DIR",
    r"C:\Program Files (x86)\Steam\steamapps\common\Valheim",
))
QUESTLAB_ROOT = Path(os.environ.get(
    "COMFY_QUESTLAB_DIR",
    str(DEFAULT_VALHEIM_DIR / "BepInEx" / "config" / "comfy-quest-lab"),
))
MAX_DOCUMENT_BYTES = 512 * 1024
MAX_REQUEST_BYTES = 768 * 1024
SAFE_NAME = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,95}\.json$")


def get_tools() -> list:
    return [questlab_write, questlab_reload, questlab_spell_encode,
            questlab_spell_decode, questlab_status]


def _quest_dir() -> Path:
    return (QUESTLAB_ROOT / "quests").resolve()


def _request_dir() -> Path:
    return (QUESTLAB_ROOT / "requests").resolve()


def _validate_document(document: Any) -> dict[str, Any]:
    if not isinstance(document, dict):
        raise ValueError("quest document must be a JSON object")
    if document.get("schema_version") != 1:
        raise ValueError("quest document schema_version must be 1")
    quests = document.get("quests")
    if not isinstance(quests, list):
        raise ValueError("quest document must contain a quests array")
    if len(quests) > 256:
        raise ValueError("quest document contains too many quests")
    seen: set[str] = set()
    for quest in quests:
        if not isinstance(quest, dict):
            raise ValueError("each quest must be an object")
        quest_id = quest.get("quest_id")
        if not isinstance(quest_id, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,96}", quest_id):
            raise ValueError("each quest_id must be a 1-96 character safe identifier")
        if quest_id.casefold() in seen:
            raise ValueError(f"duplicate quest_id: {quest_id}")
        seen.add(quest_id.casefold())
        if not isinstance(quest.get("name"), str) or not quest["name"].strip():
            raise ValueError(f"quest {quest_id} is missing name")
    encoded = json.dumps(document, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode()
    if len(encoded) > MAX_DOCUMENT_BYTES:
        raise ValueError(f"quest document exceeds {MAX_DOCUMENT_BYTES} bytes")
    return document


def _target(file_name: str) -> Path:
    if not isinstance(file_name, str) or not SAFE_NAME.fullmatch(file_name):
        raise ValueError("file_name must be a plain .json name with safe characters")
    root = _quest_dir()
    target = (root / file_name).resolve()
    if target.parent != root:
        raise ValueError("file_name must remain inside the Quest Lab quest root")
    return target


def _atomic_write(path: Path, payload: bytes, replace: bool) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and not replace:
        raise FileExistsError(f"{path.name} exists; pass replace=true explicitly")
    fd, temp_name = tempfile.mkstemp(prefix=f".{path.stem}.", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temp_name, path)
    finally:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass


def questlab_write(file_name: str, document: dict[str, Any], replace: bool = False,
                  trigger_reload: bool = True) -> dict[str, Any]:
    """Atomically write one validated Quest Lab JSON file and optionally queue reload."""
    validated = _validate_document(document)
    payload = json.dumps(validated, ensure_ascii=False, indent=2, sort_keys=True).encode("utf-8")
    if len(payload) > MAX_REQUEST_BYTES:
        raise ValueError("request exceeds the bounded Quest Lab payload size")
    target = _target(file_name)
    _atomic_write(target, payload, replace=replace)
    result: dict[str, Any] = {
        "ok": True,
        "schema": "comfy-questlab-bridge/v1",
        "file_name": file_name,
        "path": str(target),
        "sha256": __import__("hashlib").sha256(payload).hexdigest(),
        "quest_count": len(validated["quests"]),
    }
    if trigger_reload:
        result["reload"] = questlab_reload()
    return result


def questlab_reload() -> dict[str, Any]:
    """Queue the existing fixed Quest Lab batch mailbox; never invokes a console."""
    request_dir = _request_dir()
    request_dir.mkdir(parents=True, exist_ok=True)
    now = __import__("datetime").datetime.now(__import__("datetime").timezone.utc)
    request = {
        "schema": "comfy-questlab-batch-request/v1",
        "request_id": f"questlab-{int(time.time() * 1000)}",
        "operation": "reload",
        "created_utc": now.isoformat(),
        "expires_utc": (now + __import__("datetime").timedelta(minutes=5)).isoformat(),
    }
    payload = json.dumps(request, separators=(",", ":"), sort_keys=True).encode("utf-8")
    target = request_dir / "questlab-batch-request.json"
    _atomic_write(target, payload, replace=True)
    return {"queued": True, "request_id": request["request_id"], "path": str(target)}


def questlab_spell_encode(document: dict[str, Any]) -> dict[str, Any]:
    """Encode canonical schema-v1 quest JSON as a copy/paste Spell String."""
    validated = _validate_document(document)
    raw = json.dumps(validated, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return {"ok": True, "format": "comfy-questlab-spell/v1", "spell": "[Import: " + base64.b64encode(raw).decode("ascii") + "]", "bytes": len(raw)}


def questlab_spell_decode(spell: str) -> dict[str, Any]:
    """Decode and validate a Quest Lab Spell String without writing it."""
    if not isinstance(spell, str) or not spell.startswith("[Import: ") or not spell.endswith("]"):
        raise ValueError("spell must use the [Import: ...] format")
    encoded = spell[len("[Import: "):-1].strip()
    try:
        document = json.loads(base64.b64decode(encoded, validate=True).decode("utf-8"))
    except Exception as exc:
        raise ValueError("spell is not valid Base64 UTF-8 JSON") from exc
    validated = _validate_document(document)
    return {"ok": True, "format": "comfy-questlab-spell/v1", "document": validated}


def questlab_status() -> dict[str, Any]:
    """Return the local Quest Lab root and safe file counts."""
    root = _quest_dir()
    files = sorted(p.name for p in root.glob("*.json")) if root.exists() else []
    return {"schema": "comfy-questlab-bridge/v1", "quest_root": str(root), "files": files, "count": len(files)}
