# Project Decisions (PD) — the durable homes for "why"

Adopted 2026-07-29 (Derek). This directory holds the canonical rationale for
significant, long-lived project decisions. The technical netcode track keeps its own
ADRs (`fieldlab/docs/adr/`); PDs are the governance/product/posture track.

## The lifecycle

**Registers are queues, not archives.**

1. Open decision → a register entry (`DECISIONS-PENDING.md`, root or fieldlab).
2. Decision made → the entry becomes **one line + a link**.
3. Rationale with lasting value → graduates into a PD here.
4. The register links to the PD; the PD is the last word on *why*.

Resolved links age out of the queue after the immediate handoff window. Git history
and this index are the archive; the active register is not.

Promotion threshold: the rationale runs past ~5 lines, or a stranger would later ask
"why is it this way?" — then it deserves a PD. Otherwise the one-liner is enough.

## One decision, one home

Every significant decision has exactly **one** canonical document that answers *why*.
Everything else — register, handoffs, runbooks, READMEs, roadmap notes — links to it
and never restates it. Restated rationale forks and drifts; linked rationale doesn't.

## What does NOT belong in a decision register

| Species | Home |
|---|---|
| True decision (options, tradeoffs, an owner) | the register, then a PD |
| Execution of a decision already made | runbooks / checklists (e.g. `DEREK-BATCH-*.md`) |
| Plans and priority rankings | handoffs (they get superseded, not resolved) |
| Blocked work | the backlog / plans, with its unblock condition |

## Staged growth

Create a new PD only when you notice yourself linking to the same rationale
repeatedly. Do not pre-build the hierarchy; a directory of two well-used documents
beats a taxonomy of ten empty ones.

## Index

- [PD-1 — Governance & contributions](pd-1-governance-and-contributions.md)
- [PD-2 — Security posture & the First Stranger gate](pd-2-security-posture-first-stranger-gate.md)
- [PD-3 — Public community-data posture](pd-3-public-community-data.md)
- [PD-4 — What counts as proof: evidence paths and falsifiable guards](pd-4-evidence-standard.md)
- [PD-5 — The local Workbench is Baseline's ownership appliance](pd-5-local-workbench-ownership-appliance.md)
- [PD-6 — The Baseline Dev MCP is a development/lab-only control plane](pd-6-development-mcp-lifecycle.md)
- [PD-7 — Lab runtime provenance and canonical session boundary](pd-7-lab-runtime-provenance-and-session-boundary.md)
- [PD-8 — Isolated runtime and toolset repository architecture](pd-8-isolated-runtime-and-toolset-repository.md)
- [PD-9 — Sovereign add-on repositories with Baseline as the hub](pd-9-repository-split.md)
