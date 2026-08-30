"""
Canonical Meta-Creator Contract Validation Suite for Baseline.

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.

Enforces schemas, structural invariants, correlation spines, cycle safety,
spatial reference frames, and producer provenance across:
  - comfy-quest-experience/v1
  - SpatialAnchor/v1
  - InstallQuestPack/v1
  - QuestReceipt/v1
  - ObservationEvidence/v1
"""

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Set


SUPPORTED_SCHEMA_VERSIONS = {
    "comfy-quest-experience/v1",
    "SpatialAnchor/v1",
    "InstallQuestPack/v1",
    "QuestReceipt/v1",
    "ObservationEvidence/v1",
}

SCHEMAS_DIR = Path(__file__).resolve().parent.parent.parent / "docs" / "schemas"


class ContractValidationError(ValueError):
    """Raised when a contract document violates schema or structural invariants."""
    pass


def load_schema(schema_filename: str) -> Dict[str, Any]:
    """Loads a JSON schema from docs/schemas/."""
    schema_path = SCHEMAS_DIR / schema_filename
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema file not found: {schema_path}")
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def validate_spatial_anchor(anchor: Dict[str, Any]) -> None:
    """Validates SpatialAnchor/v1 structural and frame rules."""
    required = ["anchor_id", "frame", "local_bounds", "world_binding"]
    for field in required:
        if field not in anchor:
            raise ContractValidationError(f"SpatialAnchor missing required field: '{field}'")
    
    # Anchor ID validation
    if not re.match(r"^[a-zA-Z0-9_-]+$", anchor["anchor_id"]):
        raise ContractValidationError(f"Invalid anchor_id format: '{anchor['anchor_id']}'")
    
    # Frame validation (must be local/reference frame, e.g., 'structure:village_01' or 'local:room_a')
    frame = anchor["frame"]
    if not re.match(r"^[a-zA-Z0-9_-]+:[a-zA-Z0-9_-]+$", frame):
        raise ContractValidationError(f"Invalid frame format '{frame}'. Must be reference-frame based.")
    if frame.startswith("world:"):
        raise ContractValidationError("SpatialAnchor must not contain absolute world coordinates in frame.")
    
    # Local bounds validation
    bounds = anchor["local_bounds"]
    if "center" not in bounds or "radius_meters" not in bounds:
        raise ContractValidationError("SpatialAnchor local_bounds must contain 'center' and 'radius_meters'.")
    if bounds["radius_meters"] <= 0:
        raise ContractValidationError("SpatialAnchor radius_meters must be greater than 0.")
    
    # World binding validation
    binding = anchor["world_binding"]
    if binding.get("mode") not in ("resolved_at_install", "fixed_piece_anchor"):
        raise ContractValidationError(f"Invalid world_binding mode: '{binding.get('mode')}'")
    if not re.match(r"^piece:[a-zA-Z0-9_-]+$", binding.get("reference", "")):
        raise ContractValidationError(f"Invalid world_binding reference: '{binding.get('reference')}'")


def detect_illegal_synchronous_cycles(nodes: List[Dict[str, Any]]) -> None:
    """
    Analyzes execution graph nodes. Rejects illegal single-tick synchronous cycles.
    Allows valid state-machine feedback loops and timer-rearm transitions.
    """
    node_map = {node["node_id"]: node for node in nodes}
    
    # Build graph of single-tick synchronous edges only
    sync_graph: Dict[str, List[str]] = {}
    for node in nodes:
        node_id = node["node_id"]
        exec_mode = node.get("exec_mode", "single_tick")
        next_nodes = node.get("next_nodes", [])
        
        if exec_mode == "single_tick":
            sync_graph[node_id] = next_nodes
        else:
            # Bounded state machines and timer rearms break single-tick synchronous execution
            sync_graph[node_id] = []

    # Cycle detection via Tarjan's / DFS traversal on synchronous graph
    visited: Set[str] = set()
    rec_stack: Set[str] = set()

    def dfs(node_id: str, path: List[str]) -> None:
        visited.add(node_id)
        rec_stack.add(node_id)
        path.append(node_id)

        for neighbor in sync_graph.get(node_id, []):
            if neighbor not in node_map:
                raise ContractValidationError(f"Node '{node_id}' references non-existent next_node '{neighbor}'")
            if neighbor in rec_stack:
                cycle_str = " -> ".join(path[path.index(neighbor):] + [neighbor])
                raise ContractValidationError(f"Illegal synchronous execution cycle detected: {cycle_str}")
            if neighbor not in visited:
                dfs(neighbor, path)

        rec_stack.remove(node_id)
        path.pop()

    for node_id in node_map:
        if node_id not in visited:
            dfs(node_id, [])


def validate_comfy_quest_experience(payload: Dict[str, Any]) -> None:
    """Validates comfy-quest-experience/v1 contract payload."""
    if payload.get("schema_version") != "comfy-quest-experience/v1":
        raise ContractValidationError(f"Unsupported or missing schema_version: '{payload.get('schema_version')}'")
    
    required = ["quest_id", "title", "nodes", "spatial_anchors", "required_capabilities", "action_references", "checksum_sha256"]
    for field in required:
        if field not in payload:
            raise ContractValidationError(f"Experience contract missing required field: '{field}'")
    
    # Checksum format
    if not re.match(r"^[a-f0-9]{64}$", payload["checksum_sha256"]):
        raise ContractValidationError("checksum_sha256 must be a 64-character lowercase hex string.")
    
    # Spatial anchors check
    for anchor in payload["spatial_anchors"]:
        validate_spatial_anchor(anchor)
    
    # Cycle detection check
    detect_illegal_synchronous_cycles(payload["nodes"])


def validate_install_quest_pack(payload: Dict[str, Any]) -> None:
    """Validates InstallQuestPack/v1 payload."""
    if payload.get("schema_version") != "InstallQuestPack/v1":
        raise ContractValidationError(f"Unsupported or missing schema_version: '{payload.get('schema_version')}'")
    
    required = ["request_id", "source_revision", "compiled_quest_revision", "questpack_payload_sha256", "requested_by"]
    for field in required:
        if field not in payload:
            raise ContractValidationError(f"InstallQuestPack missing required field: '{field}'")

    if not re.match(r"^(sha256:[a-f0-9]{64}|[a-f0-9]{40,64})$", payload["source_revision"]):
        raise ContractValidationError("source_revision must be a 40-64 char hex string or sha256:<hex>.")
    if not re.match(r"^sha256:[a-f0-9]{64}$", payload["compiled_quest_revision"]):
        raise ContractValidationError("compiled_quest_revision must match format 'sha256:<64-hex>'.")


def validate_quest_receipt(payload: Dict[str, Any]) -> None:
    """Validates QuestReceipt/v1 payload."""
    if payload.get("schema_version") != "QuestReceipt/v1":
        raise ContractValidationError(f"Unsupported or missing schema_version: '{payload.get('schema_version')}'")

    required = ["request_id", "source_revision", "compiled_quest_revision", "active_runtime_revision", "status", "installed_at", "runtime_signature"]
    for field in required:
        if field not in payload:
            raise ContractValidationError(f"QuestReceipt missing required field: '{field}'")
    
    if payload["status"] not in ("admitted", "rejected", "rolled_back"):
        raise ContractValidationError(f"Invalid receipt status: '{payload['status']}'")


def validate_observation_evidence(payload: Dict[str, Any]) -> None:
    """Validates ObservationEvidence/v1 payload and provenance correlation spine."""
    if payload.get("schema_version") != "ObservationEvidence/v1":
        raise ContractValidationError(f"Unsupported or missing schema_version: '{payload.get('schema_version')}'")

    required = ["observation_id", "producer", "evidence_kind", "subject", "provenance", "quality", "correlation_spine"]
    for field in required:
        if field not in payload:
            raise ContractValidationError(f"ObservationEvidence missing required field: '{field}'")

    # Producer check
    producer = payload["producer"]
    if "id" not in producer or "kind" not in producer:
        raise ContractValidationError("ObservationEvidence producer must contain 'id' and 'kind'.")
    valid_kinds = {"runtime_observer", "arcane_sight", "network_sense", "steward_view", "human_feedback"}
    if producer["kind"] not in valid_kinds:
        raise ContractValidationError(f"Invalid producer kind: '{producer['kind']}'")

    # Correlation spine check
    spine = payload["correlation_spine"]
    spine_fields = ["source_revision", "compiled_quest_revision", "install_request_id", "active_runtime_revision", "anchor_id", "event_node_id"]
    for sf in spine_fields:
        if sf not in spine or not spine[sf]:
            raise ContractValidationError(f"ObservationEvidence correlation_spine missing or empty field: '{sf}'")


def validate_contract(payload: Dict[str, Any]) -> bool:
    """
    Main entrypoint for validating any Meta-Creator contract payload.
    Returns True if valid; raises ContractValidationError otherwise.
    """
    if not isinstance(payload, dict):
        raise ContractValidationError("Contract payload must be a JSON dictionary.")

    version = payload.get("schema_version")
    if not version:
        raise ContractValidationError("Contract payload missing 'schema_version'.")
    if version not in SUPPORTED_SCHEMA_VERSIONS:
        raise ContractValidationError(f"Unsupported contract schema version: '{version}'")

    if version == "comfy-quest-experience/v1":
        validate_comfy_quest_experience(payload)
    elif version == "SpatialAnchor/v1":
        validate_spatial_anchor(payload)
    elif version == "InstallQuestPack/v1":
        validate_install_quest_pack(payload)
    elif version == "QuestReceipt/v1":
        validate_quest_receipt(payload)
    elif version == "ObservationEvidence/v1":
        validate_observation_evidence(payload)
    else:
        raise ContractValidationError(f"Unrecognized schema version handler: '{version}'")

    return True
