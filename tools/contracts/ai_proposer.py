"""
AI Proposer Engine for Meta-Creator Pipeline.

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.

The AI Proposer has ZERO runtime authority:
  - It produces candidate Quest Source documents only.
  - It MUST route every candidate through compile_questpack().
  - It cannot install quests, mutate active runtime state, emit receipts,
    modify evidence, resolve world-space coordinates, or bypass contract validation.
"""

import hashlib
import json
import uuid
from typing import Any, Dict, List, Optional

from tools.contracts.meta_creator_contracts import ContractValidationError
from tools.contracts.quest_compiler import (
    add_node,
    add_spatial_anchor,
    compile_questpack,
    new_quest_source,
)


def _compute_source_hash(source: Dict[str, Any]) -> str:
    """Compute sha256 hash of canonical JSON string of a Quest Source."""
    canonical = json.dumps(source, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def propose_from_prompt(
    prompt: str,
    title: str,
    quest_id: str,
    spatial_anchors: Optional[List[Dict[str, Any]]] = None,
    requested_capabilities: Optional[List[str]] = None,
    requested_action_references: Optional[List[str]] = None,
    malformed_node_inject: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Mode A: Prompt-only Proposal.
    Converts creator natural language intent into a candidate Quest Source,
    compiles it through compile_questpack(), and records proposal provenance.
    """
    proposal_id = f"prop_{uuid.uuid4().hex[:16]}"
    
    # Construct candidate Quest Source (authoring representation)
    candidate_source = new_quest_source(
        quest_id=quest_id,
        title=title,
        narrative_intent=prompt,
        original_prompt=prompt,
        grimoire_prose="Proposer generated candidate lore.",
    )

    # Attach spatial anchors if supplied (must be local frame based)
    if spatial_anchors:
        for sa in spatial_anchors:
            candidate_source["spatial_anchors"].append(sa)
    else:
        # Default local-frame anchor if none supplied
        add_spatial_anchor(
            candidate_source,
            anchor_id="anchor_zone_01",
            frame="structure:village_01",
            center={"x": 0.0, "y": 0.0, "z": 0.0},
            radius_meters=10.0,
            reference="piece:hearth_root",
        )

    # Convert prompt intent to candidate nodes
    if malformed_node_inject is not None:
        # Allows testing malformed AI node output
        candidate_source["nodes"] = malformed_node_inject
    else:
        # Standard candidate nodes generated from prompt semantics
        add_node(
            candidate_source,
            node_id="enter_zone",
            node_type="event_trigger",
            exec_mode="single_tick",
            anchor_id=candidate_source["spatial_anchors"][0]["anchor_id"] if candidate_source["spatial_anchors"] else "anchor_zone_01",
            next_nodes=["action_announce_wave"],
        )
        add_node(
            candidate_source,
            node_id="action_announce_wave",
            node_type="action",
            exec_mode="single_tick",
            next_nodes=[],
        )

    candidate_source["required_capabilities"] = requested_capabilities or ["spawn_prefabs", "play_announcement"]
    candidate_source["action_references"] = requested_action_references or ["spawn_frost_jarl"]

    candidate_source_revision = _compute_source_hash(candidate_source)

    # Compiler Gate (Mandatory Validation)
    compile_result = "rejected"
    compiled_questpack = None
    compiled_quest_revision = None
    validation_errors = []

    try:
        compiled = compile_questpack(candidate_source, source_revision="0" * 40)
        compile_result = "success"
        compiled_questpack = compiled["questpack"]
        compiled_quest_revision = compiled["compiled_quest_revision"]
    except ContractValidationError as err:
        validation_errors.append(str(err))

    return {
        "proposal_id": proposal_id,
        "parent_source_revision": None,
        "evidence_ids": [],
        "candidate_source": candidate_source,
        "candidate_source_revision": candidate_source_revision,
        "compile_result": compile_result,
        "compiled_questpack": compiled_questpack,
        "compiled_quest_revision": compiled_quest_revision,
        "validation_errors": validation_errors,
        "proposal_explanation": {
            "what_changed": f"Generated new quest '{title}' from prompt intent.",
            "why_changed": f"Creator requested prompt-only synthesis: '{prompt}'.",
            "evidence_motivations": [],
        },
    }


def propose_revision(
    parent_source: Dict[str, Any],
    evidence_records: List[Dict[str, Any]],
    revision_instruction: str,
    proposed_anchor_adjustment: Optional[Dict[str, Any]] = None,
    malformed_node_inject: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Mode B: Evidence-informed Revision.
    Reasons over parent Quest Source and explicit ObservationEvidence/v1 records
    to propose a revised candidate Quest Source.
    
    Evidence is context, NEVER authority. Evidence IDs and producer provenance
    are preserved in the proposal provenance.
    """
    if not evidence_records:
        raise ValueError("propose_revision requires at least one ObservationEvidence record.")

    proposal_id = f"prop_{uuid.uuid4().hex[:16]}"
    parent_source_revision = _compute_source_hash(parent_source)

    evidence_ids = []
    evidence_motivations = []

    for ev in evidence_records:
        obs_id = ev.get("observation_id", "unknown_obs")
        evidence_ids.append(obs_id)
        producer = ev.get("producer", {})
        quality = ev.get("quality", {})
        evidence_motivations.append({
            "observation_id": obs_id,
            "producer_id": producer.get("id"),
            "producer_kind": producer.get("kind"),
            "quality_classification": quality.get("classification"),
            "motivation": f"Reasoned over observation '{obs_id}' from producer '{producer.get('id')}' to propose revision: {revision_instruction}",
        })

    # Deep copy parent source to create candidate source
    candidate_source = json.loads(json.dumps(parent_source))
    candidate_source["narrative_intent"] = f"{parent_source.get('narrative_intent', '')} | Revision: {revision_instruction}"

    # Apply proposed revisions to candidate source
    if malformed_node_inject is not None:
        candidate_source["nodes"] = malformed_node_inject
    elif proposed_anchor_adjustment and candidate_source.get("spatial_anchors"):
        # Adjust spatial anchor based on evidence
        anchor = candidate_source["spatial_anchors"][0]
        if "radius_meters" in proposed_anchor_adjustment:
            anchor["local_bounds"]["radius_meters"] = proposed_anchor_adjustment["radius_meters"]
        if "center" in proposed_anchor_adjustment:
            anchor["local_bounds"]["center"] = proposed_anchor_adjustment["center"]
        if "frame" in proposed_anchor_adjustment:
            anchor["frame"] = proposed_anchor_adjustment["frame"]

    candidate_source_revision = _compute_source_hash(candidate_source)

    # Compiler Gate (Mandatory Validation)
    compile_result = "rejected"
    compiled_questpack = None
    compiled_quest_revision = None
    validation_errors = []

    try:
        compiled = compile_questpack(candidate_source, source_revision="0" * 40)
        compile_result = "success"
        compiled_questpack = compiled["questpack"]
        compiled_quest_revision = compiled["compiled_quest_revision"]
    except ContractValidationError as err:
        validation_errors.append(str(err))

    return {
        "proposal_id": proposal_id,
        "parent_source_revision": parent_source_revision,
        "evidence_ids": evidence_ids,
        "candidate_source": candidate_source,
        "candidate_source_revision": candidate_source_revision,
        "compile_result": compile_result,
        "compiled_questpack": compiled_questpack,
        "compiled_quest_revision": compiled_quest_revision,
        "validation_errors": validation_errors,
        "proposal_explanation": {
            "what_changed": f"Applied evidence-informed revision: {revision_instruction}",
            "why_changed": f"Adjusted quest source based on {len(evidence_records)} evidence record(s).",
            "evidence_motivations": evidence_motivations,
        },
    }
