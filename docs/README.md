# Documentation map

Most of what lived here — the core thesis, positioning, governance and adoption
essays, the persona and perspective lenses, the method playbook and its source
transcript, and a generated repo-map snapshot — was removed in the July 2026
prune. It described community strategy for a repo whose live purpose is now the
Valheim server, its release pipeline, and the mod. That material is recoverable
from git history and from `C:\work\comfy`.

What remains is the cross-boundary architecture and dataset notes:

- **Product boundary:** [`baseline-vision-and-boundary.md`](baseline-vision-and-boundary.md).
- **Workbench operating model:** [`workbench-operating-model.md`](workbench-operating-model.md),
  implementing [PD-5 and PD-6](decisions/README.md).
- **Dated product review:**
  [`audit/2026-08-01-workbench-product-review.md`](audit/2026-08-01-workbench-product-review.md),
  preserving the conversation, historical lineage, classifications, and source audit
  behind the Workbench decisions.
- **Quest Lab expansion retrospective:**
  [`retrospectives/2026-08-09-quest-lab-expansion-retrospective.md`](retrospectives/2026-08-09-quest-lab-expansion-retrospective.md),
  recording the r24 event archive, parser/Sheets handoff, Gallery v2 rebuild, live evidence,
  visual acceptance, and remaining optional evidence gaps.
- **Quest Studio → Runtime plan:**
  [`quest-studio-runtime-plan.md`](quest-studio-runtime-plan.md), with the product boundary,
  shared contract, milestones, diagrams, current implementation state, and native host/peer evidence.
- **MCP endpoint provenance:**
  [`audit/2026-08-01-mcp-endpoint-provenance-audit.md`](audit/2026-08-01-mcp-endpoint-provenance-audit.md),
  recording the retired `:8720` task collision, split ledgers, and the identity-first
  replan.
- **Built quest slice:** [`quest-vertical-slice-architecture.md`](quest-vertical-slice-architecture.md).
  Note that it describes source under `handoffs/comfy-control-surface/`, which
  the prune removed; read it as a record of how that slice worked, not as a map
  of this repo.
- **Era-save plan:** [`lumberjacks-native-runtime-era-save-plan.md`](lumberjacks-native-runtime-era-save-plan.md).
- **Datasets:** [`datasets/weapon-choices.md`](datasets/weapon-choices.md) and
  [`datasets/weapons-economy-balance.md`](datasets/weapons-economy-balance.md).

## What belongs here

Explanations and decisions that cross implementation boundaries. Project-level
governance/product/posture decisions live in [`decisions/`](decisions/README.md).
Runnable code,
operator commands, raw evidence and generated data belong in the area they serve
— `infra/`, `network/`, `Lumberjacks/`, or `fieldlab/`.

Technical netcode decisions stay with their system as ADRs under
[`../fieldlab/docs/adr/`](../fieldlab/docs/adr/). Release manifests, receipts, and
the append-only implementation journal stay under
[`../Lumberjacks/docs/roadmap/`](../Lumberjacks/docs/roadmap/README.md). The separation
keeps one decision in one canonical home while allowing plans and runbooks to link it.
