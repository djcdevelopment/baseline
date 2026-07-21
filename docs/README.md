# Documentation map

Most of what lived here — the core thesis, positioning, governance and adoption
essays, the persona and perspective lenses, the method playbook and its source
transcript, and a generated repo-map snapshot — was removed in the July 2026
prune. It described community strategy for a repo whose live purpose is now the
Valheim server, its release pipeline, and the mod. That material is recoverable
from git history and from `C:\work\comfy`.

What remains is the cross-boundary architecture and dataset notes:

- **Built quest slice:** [`quest-vertical-slice-architecture.md`](quest-vertical-slice-architecture.md).
  Note that it describes source under `handoffs/comfy-control-surface/`, which
  the prune removed; read it as a record of how that slice worked, not as a map
  of this repo.
- **Era-save plan:** [`lumberjacks-native-runtime-era-save-plan.md`](lumberjacks-native-runtime-era-save-plan.md).
- **Datasets:** [`datasets/weapon-choices.md`](datasets/weapon-choices.md) and
  [`datasets/weapons-economy-balance.md`](datasets/weapons-economy-balance.md).

## What belongs here

Explanations and decisions that cross implementation boundaries. Runnable code,
operator commands, raw evidence and generated data belong in the area they serve
— `infra/`, `network/`, `Lumberjacks/`, or `fieldlab/`.

Durable decision records for the live systems do **not** live here. They live
with their system: ADRs under [`../fieldlab/docs/adr/`](../fieldlab/docs/adr/),
and release manifests, receipts and the append-only journal under
[`../Lumberjacks/docs/roadmap/`](../Lumberjacks/docs/roadmap/README.md).
