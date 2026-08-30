# PD-11 — Spatial authoring round trips cross as content-addressed files

Status: adopted 2026-08-30 (Derek). Canonical why for the ComfyStewardView ↔
Comfy Quest spatial-authoring seam.

## Decision

ComfyStewardView and Comfy Quest remain sovereign products. They exchange two strict,
bounded JSON documents rather than sharing source code, databases, or sibling-checkout paths:

- Steward produces a snapshot-backed 3D sphere anchor for Quest Studio.
- Quest Studio and Runtime return bounded spatial-observation evidence for Steward to overlay.

Comfy Quest owns the public exchange schemas and validation semantics. Steward owns selection
from world snapshots, server-side resolution of the selected ZDO, and its dedicated imported
evidence store. Baseline owns only this durable decision, evidence labels, and discovery links.

The first contract line is intentionally a breaking Runtime Experience v2 cutover. There is no
dual v1/v2 execution stack.

## Why this shape

The useful operator loop crosses three different kinds of authority:

1. Steward knows which immutable save and exact ZDO a map selection came from.
2. Studio knows how that selection becomes authored quest intent.
3. Runtime alone knows what position was actually observed and whether the 3D predicate passed.

A content-addressed file keeps each handoff visible, inspectable, replayable, and usable when
either application is offline. Snapshot id, world id, save SHA-256, ZDO index, prefab, producer
revision, and contract hash prevent a plausible-looking coordinate from losing its origin.
Runtime evidence carries the same snapshot/piece join back, so Steward never guesses by
timestamp or nearest point.

Both `world` and `binding_relative` modes are required. A world sphere centers on the selected
piece position. A binding-relative sphere centers on the quest Charm at execution time; v1 has
no hidden offset or rotation. In both cases Runtime evaluates Euclidean X/Y/Z distance. A
two-dimensional map may project the sphere onto X/Z only if it exposes the center Y, observed Y,
and true 3D distance rather than implying cylindrical semantics.

Evidence is stored in a separate append-only DuckDB file. Rebuilding or replacing Steward's
analytics cache must not delete it. Import is strict, size-bounded, content-hash verified,
idempotent, and protected by an operator token on the public deployment.

Runtime `world_uid` is retained as execution provenance but is not declared equivalent to a
Steward `world_id` in this version. The immutable snapshot provenance is the return join.

## Rejected predecessor

Baseline briefly contained a self-consistent Meta-Creator prototype introduced in commits
`cbb38fcc`, `e4b23a2e`, `0f00a498`, `274565bd`, and `16aa70fe`. Its spatial contract was one-way,
required invented local frames, rejected world coordinates, had no snapshot/file provenance or
content hash, and put compiler/Studio/deployment product code back in the hub.

Those commits remain the historical reconstruction path. Keeping their active implementation
would create a second authority that contradicts both [PD-9](pd-9-repository-split.md) and the
shipping sovereign repositories, so the prototype is removed after this rationale is retained.

## Consequences

- Contract changes begin in `comfy-quest` and cross by a released immutable artifact, byte
  count, and SHA-256; Steward does not read the Quest checkout.
- Steward exports only geometry it re-resolves from its own snapshot cache.
- Studio preserves source-anchor provenance while lowering the file into one first-class
  Experience v2 area.
- Runtime receipts, not browser claims, are the execution evidence.
- Cache rebuild tooling must treat the evidence database as non-rebuildable state.
- A future world-identity mapping, offsets/rotation, or another shape requires an explicit
  contract revision rather than an optional field silently changing v1.

## Evidence state

**VERIFIED locally (2026-08-30):** the two sovereign suites share exact anchor and evidence
SHA-256 fixtures; Quest validates both frame modes and true 3D distances; Steward validates
strict parsing, tamper rejection, idempotent dedicated persistence, and snapshot-filtered
overlays. The reproducible gates are the Quest .NET suites and Steward's Maven
`SpatialExchangeContractTest`.

**UNVERIFIED live:** no claim is made here that the current AM4 image or a live Valheim Runtime
has completed the new operator lap. That claim graduates only after a released Steward revision
exports an anchor from a disposable snapshot, Studio imports it, Runtime records a real
observation, and the returned evidence renders against the same snapshot in Steward.

## Authorities

- [Comfy Quest spatial contracts](https://github.com/djcdevelopment/comfy-quest/tree/main/contracts/spatial)
- [Comfy Quest Runtime and Studio](https://github.com/djcdevelopment/comfy-quest)
- [ComfyStewardView](https://github.com/djcdevelopment/ComfyStewardView)
- [PD-4 evidence standard](pd-4-evidence-standard.md)
- [PD-9 repository split](pd-9-repository-split.md)
