# Meta-Creator v1 Canonical Contracts

> **AI proposes. Contracts validate. Runtime executes. Evidence reports.**

These schemas define the v1 contract shapes for the Quest OS meta-creator
pipeline.  Every producer and consumer targets these exact structures.
The [frozen fixtures](../../tests/fixtures/contracts_v1/) are the canonical
instances — if a schema change breaks a fixture, the change must be deliberate.

## Contracts

| Contract | Schema | Frozen fixture | Owner |
|---|---|---|---|
| **SpatialAnchor/v1** | [spatial-anchor-v1.json](spatial-anchor-v1.json) | [fixture](../../tests/fixtures/contracts_v1/spatial-anchor-v1.json) | `ComfyStewardView` produces; `comfy-quest` compiler consumes |
| **comfy-quest-experience/v1** | [comfy-quest-experience-v1.json](comfy-quest-experience-v1.json) | [fixture](../../tests/fixtures/contracts_v1/comfy-quest-experience-v1.json) | `baseline` compiler produces; `ComfyQuestRuntime` consumes |
| **InstallQuestPack/v1** | [install-quest-pack-v1.json](install-quest-pack-v1.json) | [fixture](../../tests/fixtures/contracts_v1/install-quest-pack-v1.json) | Studio/MCP/mailbox transport produces; runtime consumes |
| **QuestReceipt/v1** | [quest-receipt-v1.json](quest-receipt-v1.json) | [fixture](../../tests/fixtures/contracts_v1/quest-receipt-v1.json) | `ComfyQuestRuntime` produces (sole authority) |
| **ObservationEvidence/v1** | [observation-evidence-v1.json](observation-evidence-v1.json) | [fixture](../../tests/fixtures/contracts_v1/observation-evidence-v1.json) | Any evidence producer (runtime, Arcane Sight, NetworkSense, human) |

## Provenance correlation spine

Every relevant receipt and evidence record makes this chain traversable
without timestamps, filenames, or heuristic correlation:

```
source_revision
  └─> compiled_quest_revision (sha256)
        └─> install_request_id
              └─> active_runtime_revision
                    └─> anchor_id
                          └─> event_node_id
                                └─> observation_evidence_receipt
```

## Authority boundaries

| Layer | Authority | Notes |
|---|---|---|
| StewardView | **Design authority** | Produces SpatialAnchor/v1 in local reference frames only |
| Quest compiler | **Contract validation** | Strips authoring provenance; produces deterministic `.questpack` |
| Transport (MCP / mailbox) | **Delivery only** | Neither modifies execution semantics |
| ComfyQuestRuntime | **Sole execution authority** | Validates, admits, activates, rolls back, signs receipts |
| Evidence producers | **Observation only** | Carry explicit producer identity and quality classification |
| AI | **Proposer only** | Zero runtime authority |

## StewardView integration

StewardView's contract boundary is intentionally narrow:

```
CAD / WebGL design geometry
    ↓
local reference frame (e.g. structure:village_01)
    ↓
SpatialAnchor/v1 JSON  (target: frozen fixture shape)
    ↓
baseline quest compiler  (compile_questpack)
```

StewardView does not need to understand deployment, runtime admission,
evidence, receipts, or Valheim world coordinates.  It produces
`SpatialAnchor/v1` documents in local frames.  The existing compiler
handles everything downstream.

## Validation and tests

```powershell
# Contract schema validation + cycle safety + fixture integrity
python -m unittest tests.test_meta_creator_contracts -v
python -m unittest tests.test_frozen_contract_fixtures -v

# Full vertical-slice pipeline (compiler → install → admit → evidence → spine)
python -m unittest tests.test_quest_vertical_slice -v
```

## Files

- Schemas: `docs/schemas/*.json`
- Validators: [`tools/contracts/meta_creator_contracts.py`](../../tools/contracts/meta_creator_contracts.py)
- Compiler & pipeline: [`tools/contracts/quest_compiler.py`](../../tools/contracts/quest_compiler.py)
- Frozen fixtures: [`tests/fixtures/contracts_v1/`](../../tests/fixtures/contracts_v1/)
- Fixture tests: [`tests/test_frozen_contract_fixtures.py`](../../tests/test_frozen_contract_fixtures.py)
