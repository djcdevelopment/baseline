"""
Quest Compiler: Source → validated .questpack (comfy-quest-experience/v1).

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.

The compiler transforms authoring-layer Quest Source definitions (narrative
intent, spatial references, editor metadata, provenance) into a deterministic
executable artifact.  Original prompts, Grimoire prose, and editor state are
authoring provenance — they do not enter the executable graph.

The compiled .questpack is reusable across translations, rotations, terrain
elevations, reloads, and multiple instances.  World coordinates are never
compiled in; SpatialAnchors carry local reference-frame geometry with binding
rules resolved by ComfyQuestRuntime at install time.
"""

import base64
import hashlib
import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from tools.contracts.meta_creator_contracts import (
    ContractValidationError,
    detect_illegal_synchronous_cycles,
    validate_comfy_quest_experience,
    validate_spatial_anchor,
)


# ---------------------------------------------------------------------------
# Quest Source model  (authoring layer — NOT executable truth)
# ---------------------------------------------------------------------------

def new_quest_source(
    quest_id: str,
    title: str,
    narrative_intent: str = "",
    original_prompt: str = "",
    grimoire_prose: str = "",
    editor_metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Create a Quest Source document.  This is authoring provenance, not runtime."""
    return {
        "quest_id": quest_id,
        "title": title,
        "narrative_intent": narrative_intent,
        "original_prompt": original_prompt,
        "grimoire_prose": grimoire_prose,
        "editor_metadata": editor_metadata or {},
        "nodes": [],
        "spatial_anchors": [],
        "required_capabilities": [],
        "action_references": [],
    }


def add_node(
    source: Dict[str, Any],
    node_id: str,
    node_type: str,
    exec_mode: str = "single_tick",
    anchor_id: str = "",
    next_nodes: Optional[List[str]] = None,
    max_tick_depth: Optional[int] = None,
) -> Dict[str, Any]:
    """Append an executable node to the quest source."""
    node: Dict[str, Any] = {
        "node_id": node_id,
        "node_type": node_type,
        "exec_mode": exec_mode,
    }
    if anchor_id:
        node["anchor_id"] = anchor_id
    node["next_nodes"] = next_nodes or []
    if max_tick_depth is not None:
        node["max_tick_depth"] = max_tick_depth
    source["nodes"].append(node)
    return source


def add_spatial_anchor(
    source: Dict[str, Any],
    anchor_id: str,
    frame: str,
    center: Dict[str, float],
    radius_meters: float,
    binding_mode: str = "resolved_at_install",
    reference: str = "piece:hearth_root",
) -> Dict[str, Any]:
    """Attach a SpatialAnchor to the quest source (local frame only)."""
    source["spatial_anchors"].append({
        "anchor_id": anchor_id,
        "frame": frame,
        "local_bounds": {
            "center": center,
            "radius_meters": radius_meters,
        },
        "world_binding": {
            "mode": binding_mode,
            "reference": reference,
        },
    })
    return source


# ---------------------------------------------------------------------------
# Compiler
# ---------------------------------------------------------------------------

def _content_hash(payload: Dict[str, Any]) -> str:
    """Deterministic SHA-256 of the canonical JSON representation."""
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def compile_questpack(
    source: Dict[str, Any],
    source_revision: str = "0" * 40,
) -> Dict[str, Any]:
    """
    Compile a Quest Source into a validated comfy-quest-experience/v1 questpack.

    Returns a dict with:
        questpack  – the executable contract (comfy-quest-experience/v1)
        source_revision      – 40-char hex commit SHA (or placeholder)
        compiled_quest_revision – sha256:<hex> of the compiled content
        questpack_payload_sha256 – same hash, without prefix

    Raises ContractValidationError on invalid input.
    """

    # --- strip authoring provenance (NOT part of the executable) ---
    executable_nodes = []
    for node in source.get("nodes", []):
        exe = {
            "node_id": node["node_id"],
            "node_type": node["node_type"],
            "exec_mode": node.get("exec_mode", "single_tick"),
        }
        if node.get("anchor_id"):
            exe["anchor_id"] = node["anchor_id"]
        exe["next_nodes"] = node.get("next_nodes", [])
        if "max_tick_depth" in node:
            exe["max_tick_depth"] = node["max_tick_depth"]
        executable_nodes.append(exe)

    # --- validate spatial anchors ---
    for anchor in source.get("spatial_anchors", []):
        validate_spatial_anchor(anchor)

    # --- cycle safety ---
    detect_illegal_synchronous_cycles(executable_nodes)

    # --- build questpack payload (checksum placeholder first) ---
    questpack: Dict[str, Any] = {
        "schema_version": "comfy-quest-experience/v1",
        "quest_id": source["quest_id"],
        "title": source["title"],
        "nodes": executable_nodes,
        "spatial_anchors": source.get("spatial_anchors", []),
        "required_capabilities": source.get("required_capabilities", []),
        "action_references": source.get("action_references", []),
        "checksum_sha256": "0" * 64,  # placeholder
    }

    # --- compute content hash over everything except the checksum itself ---
    hashable = dict(questpack)
    del hashable["checksum_sha256"]
    content_hash = _content_hash(hashable)
    questpack["checksum_sha256"] = content_hash

    # --- final structural validation ---
    validate_comfy_quest_experience(questpack)

    return {
        "questpack": questpack,
        "source_revision": source_revision,
        "compiled_quest_revision": f"sha256:{content_hash}",
        "questpack_payload_sha256": content_hash,
    }


# ---------------------------------------------------------------------------
# InstallQuestPack request builder
# ---------------------------------------------------------------------------

def build_install_request(
    compiled: Dict[str, Any],
    requested_by: str = "quest_studio",
) -> Dict[str, Any]:
    """
    Build an InstallQuestPack/v1 request from a compiled questpack result or AI proposal result.
    Correlates source_revision → compiled_quest_revision → request_id cleanly.
    """
    source_rev = compiled.get("source_revision") or compiled.get("candidate_source_revision") or ("0" * 40)
    compiled_rev = compiled.get("compiled_quest_revision", "")
    payload_hash = compiled.get("questpack_payload_sha256") or compiled_rev.replace("sha256:", "")

    return {
        "schema_version": "InstallQuestPack/v1",
        "request_id": f"req_{uuid.uuid4().hex[:16]}",
        "source_revision": source_rev,
        "compiled_quest_revision": compiled_rev,
        "questpack_payload_sha256": payload_hash,
        "requested_by": requested_by,
    }


# ---------------------------------------------------------------------------
# Runtime admission simulator  (ComfyQuestRuntime authority)
# ---------------------------------------------------------------------------

def _base64_signature(payload: Dict[str, Any]) -> str:
    """Produce a simple base64 tag from the payload digest.  R&D placeholder."""
    digest = _content_hash(payload)
    return base64.b64encode(digest.encode("utf-8")).hexdigest() if hasattr(base64.b64encode(digest.encode("utf-8")), "hexdigest") else base64.b64encode(digest.encode("utf-8")).decode("utf-8")


def admit_questpack(
    install_request: Dict[str, Any],
    questpack: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Simulate ComfyQuestRuntime admission.

    1. Validates the questpack against comfy-quest-experience/v1.
    2. Verifies the payload SHA-256 matches the install request.
    3. Performs atomic "swap" (here: returns the active revision).
    4. Emits a QuestReceipt/v1 with a base64 runtime_signature.

    Returns the QuestReceipt/v1 on success.
    Raises ContractValidationError on rejection.
    """
    # --- validate the questpack itself ---
    validate_comfy_quest_experience(questpack)

    # --- verify payload integrity ---
    if questpack["checksum_sha256"] != install_request["questpack_payload_sha256"]:
        return {
            "schema_version": "QuestReceipt/v1",
            "request_id": install_request["request_id"],
            "source_revision": install_request["source_revision"],
            "compiled_quest_revision": install_request["compiled_quest_revision"],
            "active_runtime_revision": "",
            "status": "rejected",
            "installed_at": datetime.now(timezone.utc).isoformat(),
            "runtime_signature": "",
        }

    # --- atomic swap (simulated) ---
    active_revision = install_request["compiled_quest_revision"]

    receipt = {
        "schema_version": "QuestReceipt/v1",
        "request_id": install_request["request_id"],
        "source_revision": install_request["source_revision"],
        "compiled_quest_revision": install_request["compiled_quest_revision"],
        "active_runtime_revision": active_revision,
        "status": "admitted",
        "installed_at": datetime.now(timezone.utc).isoformat(),
        "runtime_signature": _base64_signature(questpack),
    }
    return receipt


# ---------------------------------------------------------------------------
# Evidence pipeline
# ---------------------------------------------------------------------------

def emit_observation(
    receipt: Dict[str, Any],
    anchor_id: str,
    event_node_id: str,
    producer_id: str = "comfy-quest-runtime",
    producer_kind: str = "runtime_observer",
    evidence_kind: str = "event_execution",
    classification: str = "observed",
    extra: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Emit an ObservationEvidence/v1 record with full correlation spine
    and explicit producer provenance.

    Evidence is created locally and does not depend on Studio or Isolate.
    """
    observation_id = f"obs_{uuid.uuid4().hex[:16]}"
    now = datetime.now(timezone.utc).isoformat()

    evidence: Dict[str, Any] = {
        "schema_version": "ObservationEvidence/v1",
        "observation_id": observation_id,
        "producer": {
            "id": producer_id,
            "kind": producer_kind,
        },
        "evidence_kind": evidence_kind,
        "subject": {
            "quest_revision": receipt["compiled_quest_revision"],
            "node_id": event_node_id,
            "anchor_id": anchor_id,
        },
        "provenance": {
            "session_id": f"sess_{uuid.uuid4().hex[:12]}",
            "observed_at": now,
        },
        "quality": {
            "classification": classification,
        },
        "correlation_spine": {
            "source_revision": receipt["source_revision"],
            "compiled_quest_revision": receipt["compiled_quest_revision"],
            "install_request_id": receipt["request_id"],
            "active_runtime_revision": receipt["active_runtime_revision"],
            "anchor_id": anchor_id,
            "event_node_id": event_node_id,
        },
    }
    if extra:
        evidence["extra"] = extra
    return evidence


# ---------------------------------------------------------------------------
# Durable local evidence log
# ---------------------------------------------------------------------------

def write_evidence_log(evidence: Dict[str, Any], log_path: str) -> str:
    """
    Append a single evidence record as a JSON line to a local durable log.
    Returns the observation_id written.

    Evidence creation must not depend on Studio or Isolate availability.
    """
    from pathlib import Path
    log = Path(log_path)
    log.parent.mkdir(parents=True, exist_ok=True)
    with open(log, "a", encoding="utf-8") as f:
        f.write(json.dumps(evidence, separators=(",", ":")) + "\n")
    return evidence["observation_id"]


def read_evidence_log(log_path: str) -> List[Dict[str, Any]]:
    """Read all evidence records from a JSON-lines log file."""
    from pathlib import Path
    log = Path(log_path)
    if not log.exists():
        return []
    records = []
    with open(log, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records
