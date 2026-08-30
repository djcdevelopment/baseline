"""
Deterministic Grimoire Presentation Renderer for Meta-Creator Pipeline.

Translates canonical executable questpack nodes (comfy-quest-experience/v1)
into human-readable Norse lore presentation prose using versioned grammar specifications
(grimoire-grammar/v1).

Properties:
  - 100% Deterministic: Same input nodes + same grammar = identical prose output.
  - Zero Execution Semantics: Pure presentation layer; cannot alter runtime behavior.
  - Reversible: Every rendered section correlates directly back to node_id, anchor_id, and semantic_id.
  - Fail-safe: Unknown semantics fall back to safe generic templates without breaking.
"""

import json
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_GRAMMAR_FILE = Path(__file__).resolve().parent.parent.parent / "docs" / "schemas" / "grimoire-grammar-v1-default.json"


def load_grimoire_grammar(grammar_path: Optional[Path] = None) -> Dict[str, Any]:
    """Loads a grimoire-grammar/v1 file."""
    path = grammar_path or DEFAULT_GRAMMAR_FILE
    if not path.exists():
        raise FileNotFoundError(f"Grimoire grammar file not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _resolve_semantic_id(node: Dict[str, Any]) -> str:
    """Maps an executable node to its canonical semantic ID."""
    node_type = node.get("node_type", "unknown")
    node_id = node.get("node_id", "")
    
    # Specific semantic mappings based on node_id or node_type
    if "enter" in node_id or node_type == "event_trigger":
        return "Player.EnterZone"
    elif "death" in node_id or "kill" in node_id:
        return "Character.OnDeath"
    elif "place" in node_id or "piece" in node_id:
        return "Player.PlacePiece"
    elif "take" in node_id or "chest" in node_id:
        return "Container.TakeAll"
    elif "spawn" in node_id or node_type == "action":
        return "SpawnWave"
    elif "status" in node_id or "buff" in node_id:
        return "ApplyStatus"
    elif "announce" in node_id or "speak" in node_id:
        return "Announce"
    
    return f"Generic.{node_type}"


def render_grimoire(
    questpack: Dict[str, Any],
    grammar: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Renders a deterministic Grimoire presentation document from a comfy-quest-experience/v1 questpack.
    
    Returns a dict with:
        schema_version: 'grimoire-presentation/v1'
        quest_id: quest ID
        title: quest title
        rendered_sections: list of section dicts (node_id, anchor_id, semantic_id, category, prose)
        content_sha256: sha256 of canonical rendered output for snapshot stability
    """
    if grammar is None:
        grammar = load_grimoire_grammar()

    templates = grammar.get("templates", {})
    nodes = questpack.get("nodes", [])

    rendered_sections: List[Dict[str, Any]] = []

    for node in nodes:
        node_id = node.get("node_id", "unknown_node")
        anchor_id = node.get("anchor_id", "hearth_zone")
        semantic_id = _resolve_semantic_id(node)

        template_info = templates.get(semantic_id)

        if template_info:
            category = template_info.get("category", "Generic")
            prose_fmt = template_info.get("prose_template", "The runes observe node {node_id}...")
            prose = prose_fmt.format(node_id=node_id, anchor_id=anchor_id)
        else:
            # Fallback for unknown semantics
            category = "Generic"
            prose = f"Upon the realm at {anchor_id}, the invocation {node_id} triggers under rune authority."

        rendered_sections.append({
            "node_id": node_id,
            "anchor_id": anchor_id,
            "semantic_id": semantic_id,
            "category": category,
            "prose": prose,
        })

    presentation = {
        "schema_version": "grimoire-presentation/v1",
        "quest_id": questpack.get("quest_id", "unknown_quest"),
        "title": questpack.get("title", "Untitled Quest"),
        "grammar_version": grammar.get("schema_version", "grimoire-grammar/v1"),
        "rendered_sections": rendered_sections,
    }

    # Deterministic SHA-256 for snapshot stability check
    canonical = json.dumps(presentation, sort_keys=True, separators=(",", ":"))
    import hashlib
    presentation["presentation_sha256"] = hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    return presentation
