# Quest Studio, Runtime, and Lab boundary

Authoring in the in-game Quest Lab is frozen. New authoring belongs in **Quest Studio**, a loopback
Workbench surface with durable editable state. **ComfyQuestRuntime** is the deliberately small game
consumer of published experience documents. **ComfyQuestLab** remains the private-world observation,
rehearsal, and learning surface. ComfyNetworkSense keeps telemetry and unchanged schema-1 compatibility;
it does not execute experience documents.

The primary handoff is an immutable `.questpack`. A pack may retain unchanged `quests/*.json` and adds
`experiences/*.json` using `comfy-quest-experience/v1`. Runtime ignores the legacy directory, checks only
on an explicit request, and activates only on an explicit load. MCP may automate those same operations
later but is neither the contract nor a required connection.

The Unity-free implementation lives in `network/mod/ComfyQuestContracts`. It owns bounds, stable-ID and
action-registry validation, deterministic trigger evaluation, cycle rejection, canonical content hashes,
semantic-version selection, collision refusal, and atomic `active/active-set.json` replacement.

The current vertical includes the structured Studio page, authenticated confined Companion publication,
immutable version history and diff, explicit Runtime check/load/rollback, Charm ownership and inscription,
machine-readable receipts, durable stages and timers, and the closed message/reward/spawn/marked-cleanup
action slice. OMEN solo and private-listen-host mutation plus i5 peer fail-closed authority are live-proven.
Rich graph authoring, replay/import, Arcane Sight, remaining action types, and the Lab migration remain partial
or planned and must not be described as shipped.

The complete vision, architecture, milestones, interfaces, diagrams, and current implementation status are
maintained in [`quest-studio-runtime-plan.md`](quest-studio-runtime-plan.md).
