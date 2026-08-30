"""
Quest Studio Workbench Bridge & Authoring Surface.

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.

Quest Studio receives SpatialAnchor/v1 contract objects from StewardView or other design tools.
It populates anchor slots, binds anchors to event graph nodes (e.g. Player.EnterZone),
and invokes compile_questpack() to produce validated executable .questpack artifacts.

Invariants:
  - Consumes SpatialAnchor/v1 strictly as a contract object (no internal CAD/WebGL parsing).
  - One-way spatial intake: StewardView -> Quest Studio.
  - Modifying Studio event nodes does NOT mutate StewardView spatial geometry.
  - Spatial anchors remain local/reference-frame based; no absolute world coordinates appear in compiled output.
  - Malformed or unsupported anchor versions fail visibly with ContractValidationError.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.contracts.meta_creator_contracts import (
    ContractValidationError,
    validate_spatial_anchor,
    validate_contract,
)
from tools.contracts.quest_compiler import (
    new_quest_source,
    add_node,
    add_spatial_anchor,
    compile_questpack,
)


class QuestStudioSession:
    """
    In-memory Quest Studio authoring session managing candidate Quest Source ASTs,
    imported spatial anchor slots, and event bindings.
    """

    def __init__(self, quest_id: str, title: str):
        self.quest_id = quest_id
        self.title = title
        self.source = new_quest_source(
            quest_id=quest_id,
            title=title,
            narrative_intent="Authoring session created in Quest Studio",
            grimoire_prose="Studio authoring session initialized.",
        )
        self.imported_anchors: Dict[str, Dict[str, Any]] = {}

    def import_spatial_anchor(self, anchor_data: Dict[str, Any]) -> str:
        """
        Imports a SpatialAnchor/v1 document (e.g., from StewardView /api/v1/spatial-anchors/export).
        Validates the anchor strictly against SpatialAnchor/v1 schema.
        
        Raises ContractValidationError if malformed or containing absolute world coordinates.
        Returns the anchor_id on success.
        """
        # Validate anchor as pure contract object
        validate_spatial_anchor(anchor_data)

        anchor_id = anchor_data["anchor_id"]
        # Store deep copy to ensure modifying Studio events does not mutate origin anchor object
        anchor_copy = json.loads(json.dumps(anchor_data))
        
        self.imported_anchors[anchor_id] = anchor_copy

        # Check if already present in source, replace or append
        existing_anchors = self.source.get("spatial_anchors", [])
        updated = False
        for i, a in enumerate(existing_anchors):
            if a["anchor_id"] == anchor_id:
                existing_anchors[i] = anchor_copy
                updated = True
                break
        if not updated:
            existing_anchors.append(anchor_copy)

        self.source["spatial_anchors"] = existing_anchors
        return anchor_id

    def bind_event_node(
        self,
        node_id: str,
        node_type: str,
        anchor_id: str,
        exec_mode: str = "single_tick",
        next_nodes: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Binds an event node (e.g., Player.EnterZone) to an imported SpatialAnchor slot.
        Raises ValueError if anchor_id has not been imported.
        """
        if anchor_id not in self.imported_anchors:
            raise ValueError(f"Anchor '{anchor_id}' has not been imported into Quest Studio session.")

        # Update or append node
        nodes = self.source.get("nodes", [])
        new_node = {
            "node_id": node_id,
            "node_type": node_type,
            "exec_mode": exec_mode,
            "anchor_id": anchor_id,
            "next_nodes": next_nodes or [],
        }

        updated = False
        for i, n in enumerate(nodes):
            if n["node_id"] == node_id:
                nodes[i] = new_node
                updated = True
                break
        if not updated:
            nodes.append(new_node)

        self.source["nodes"] = nodes
        return new_node

    def compile(self, source_revision: str = "0" * 40) -> Dict[str, Any]:
        """
        Compiles the current Studio session into a validated comfy-quest-experience/v1 .questpack.
        
        Raises ContractValidationError if compilation or cycle check fails.
        """
        return compile_questpack(self.source, source_revision=source_revision)


def import_stewardview_export(
    export_json_or_dict: Any,
    session: QuestStudioSession,
) -> str:
    """
    Bridge helper: Consumes raw JSON or dict from StewardView /api/v1/spatial-anchors/export,
    validates it, and imports it into the QuestStudioSession.
    """
    if isinstance(export_json_or_dict, (str, bytes)):
        anchor_data = json.loads(export_json_or_dict)
    else:
        anchor_data = export_json_or_dict

    return session.import_spatial_anchor(anchor_data)
