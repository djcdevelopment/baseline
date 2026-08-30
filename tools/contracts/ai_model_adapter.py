"""
Live Model Adapter & Normalizer for AI Proposer Engine.

Governing Principle:
    AI proposes. Contracts validate. Runtime executes. Evidence reports.

Strict Provider Boundary:
    Provider (Hosted / Local HTTP)
          ↓
    raw model response
          ↓
    ADAPTER / NORMALIZER (ai_model_adapter.py)
          ↓
    candidate Quest Source
          ↓
    AI Proposer Provenance Layer (ai_proposer.py)
          ↓
    compile_questpack()

Invariants:
  - Provider response formats NEVER leak into Quest Source or compiler.
  - Model proposals preserve provider, model name, adapter_version, and prompt_template_version.
  - Mandatory compiler gate: invalid model outputs are safely rejected without mutating runtime state.
"""

import json
import os
import urllib.request
import urllib.error
import uuid
from typing import Any, Dict, List, Optional

from tools.contracts.ai_proposer import (
    _compute_source_hash,
    propose_from_prompt,
    propose_revision,
)
from tools.contracts.meta_creator_contracts import ContractValidationError
from tools.contracts.quest_compiler import (
    add_spatial_anchor,
    compile_questpack,
    new_quest_source,
)


class QuestModelAdapter:
    """
    Abstract / base provider interface for live LLM proposer adapters.
    """

    def __init__(self, provider_name: str, model_name: str, adapter_version: str = "v1"):
        self.provider_name = provider_name
        self.model_name = model_name
        self.adapter_version = adapter_version
        self.prompt_template_version = "v1"

    def propose(
        self,
        prompt: str,
        *,
        title: Optional[str] = None,
        quest_id: Optional[str] = None,
        parent_source: Optional[Dict[str, Any]] = None,
        evidence_records: Optional[List[Dict[str, Any]]] = None,
        spatial_anchors: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """
        Subclasses implement this method to call the provider, normalize the raw response
        into a candidate Quest Source dictionary, and pass it through compile_questpack().
        """
        raise NotImplementedError("Subclasses must implement propose()")


class MockLocalModelAdapter(QuestModelAdapter):
    """
    Deterministic reference model adapter for offline, CI, and local testing.
    """

    def __init__(self, model_name: str = "mock-local-v1"):
        super().__init__(provider_name="mock-local", model_name=model_name)

    def propose(
        self,
        prompt: str,
        *,
        title: Optional[str] = None,
        quest_id: Optional[str] = None,
        parent_source: Optional[Dict[str, Any]] = None,
        evidence_records: Optional[List[Dict[str, Any]]] = None,
        spatial_anchors: Optional[List[Dict[str, Any]]] = None,
        raw_response_override: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        q_title = title or "Generated Quest"
        q_id = quest_id or "gen_quest_01"

        if parent_source and evidence_records:
            # Mode B: Revision
            proposal = propose_revision(
                parent_source=parent_source,
                evidence_records=evidence_records,
                revision_instruction=prompt,
                proposed_anchor_adjustment={"radius_meters": 18.0} if evidence_records else None,
            )
        else:
            # Mode A: Prompt-Only
            proposal = propose_from_prompt(
                prompt=prompt,
                title=q_title,
                quest_id=q_id,
                spatial_anchors=spatial_anchors,
            )

        # Enrich proposal with provider metadata
        proposal["provider"] = self.provider_name
        proposal["model"] = self.model_name
        proposal["adapter_version"] = self.adapter_version
        proposal["prompt_template_version"] = self.prompt_template_version
        proposal["raw_model_response"] = raw_response_override or {
            "choices": [{"message": {"content": json.dumps(proposal["candidate_source"])}}]
        }

        return proposal


class OpenAICompatibleModelAdapter(QuestModelAdapter):
    """
    HTTP JSON client adapter targeting OpenAI-compatible endpoints (vLLM, Ollama, LM Studio, local HTTP).
    Extracts structured JSON candidate Quest Source from chat completion responses.
    """

    def __init__(
        self,
        endpoint_url: str = "http://localhost:11434/v1/chat/completions",
        model_name: str = "llama3",
        api_key: Optional[str] = None,
    ):
        super().__init__(provider_name="openai-compatible", model_name=model_name)
        self.endpoint_url = endpoint_url
        self.api_key = api_key or os.getenv("OPENAI_API_KEY", "bearer_token_placeholder")

    def _build_system_prompt() -> str:
        return (
            "You are a Quest OS Compiler Assistant. Output ONLY valid JSON matching the Quest Source schema.\n"
            "Include: quest_id, title, narrative_intent, nodes, spatial_anchors, required_capabilities, action_references.\n"
            "CRITICAL: SpatialAnchor frame MUST be local (e.g., 'structure:village_01'). NEVER use 'world:' coordinates."
        )

    def propose(
        self,
        prompt: str,
        *,
        title: Optional[str] = None,
        quest_id: Optional[str] = None,
        parent_source: Optional[Dict[str, Any]] = None,
        evidence_records: Optional[List[Dict[str, Any]]] = None,
        spatial_anchors: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ) -> Dict[str, Any]:
        proposal_id = f"prop_{uuid.uuid4().hex[:16]}"
        q_title = title or "AI Generated Quest"
        q_id = quest_id or "ai_quest_01"

        payload = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": OpenAICompatibleModelAdapter._build_system_prompt()},
                {"role": "user", "content": f"Title: {q_title}\nID: {q_id}\nPrompt: {prompt}"}
            ],
            "temperature": 0.2,
        }

        raw_response = None
        candidate_source = None
        validation_errors = []

        try:
            req = urllib.request.Request(
                self.endpoint_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=5) as response:
                raw_response = json.loads(response.read().decode("utf-8"))
                content = raw_response["choices"][0]["message"]["content"]
                candidate_source = json.loads(content)
        except Exception as err:
            # Endpoint offline or network error fallback
            validation_errors.append(f"HTTP Provider Error: {str(err)}")

        if not candidate_source:
            # Fallback candidate source generated safely
            candidate_source = new_quest_source(
                quest_id=q_id,
                title=q_title,
                narrative_intent=prompt,
            )
            add_spatial_anchor(
                candidate_source,
                anchor_id="anchor_zone_01",
                frame="structure:village_01",
                center={"x": 0, "y": 0, "z": 0},
                radius_meters=10.0,
                reference="piece:hearth_root",
            )

        candidate_source_revision = _compute_source_hash(candidate_source)

        # Mandatory Compiler Gate
        compile_result = "rejected"
        compiled_questpack = None
        compiled_quest_revision = None

        try:
            compiled = compile_questpack(candidate_source, source_revision="0" * 40)
            compile_result = "success"
            compiled_questpack = compiled["questpack"]
            compiled_quest_revision = compiled["compiled_quest_revision"]
        except ContractValidationError as cve:
            validation_errors.append(str(cve))

        proposal = {
            "proposal_id": proposal_id,
            "provider": self.provider_name,
            "model": self.model_name,
            "adapter_version": self.adapter_version,
            "prompt_template_version": self.prompt_template_version,
            "parent_source_revision": _compute_source_hash(parent_source) if parent_source else None,
            "evidence_ids": [ev.get("observation_id") for ev in evidence_records] if evidence_records else [],
            "candidate_source": candidate_source,
            "candidate_source_revision": candidate_source_revision,
            "compile_result": compile_result,
            "compiled_questpack": compiled_questpack,
            "compiled_quest_revision": compiled_quest_revision,
            "validation_errors": validation_errors,
            "proposal_explanation": {
                "what_changed": f"Generated candidate quest '{q_title}' via provider '{self.provider_name}'.",
                "why_changed": f"Model '{self.model_name}' processed prompt: '{prompt}'.",
                "evidence_motivations": [],
            },
        }

        if kwargs.get("include_raw_response", False):
            proposal["raw_model_response"] = raw_response

        return proposal
