# Baseline — vision and product boundary

Recorded 2026-07-29 from Derek's own framing (lightly cleaned; treat this as the canonical
product statement until he revises it).

## What Baseline is

Think of the name: **Baseline is a toolkit to build an entire community on, in Valheim** —
with the things most hobbyists never get to have:

- **Identity support baked in** (the thing most hobbyists have no experience with)
- **Telemetry and monitoring as first-class citizens**
- **Vertical integration paths at every level:**
  Server → Gateway → Player → Mod → BepInEx → Harmony → Unity → transpiling
- **Tooling for headless testing, automated testing, MCP-driven testing and logging**

The communities it serves **already do this work** — with a wide variety of mods,
spreadsheets, Discord bots, checklists, screenshots. Baseline doesn't replace that;
it lets them do what they already do while spending **less time on paperwork and
tracking and more time being creative and creating experiences**.

## The operating model

- **Derek is the white-glove consultant** who onboards a community's *current*
  structure — the demonstration is "your existing thing, with less friction," never
  "throw yours away."
- **Demystify AI and give people a place to fail.** Then the turnkey docker
  "ez-button" startup walkthroughs.
- **People are expected to read the code.** Make that easier, not harder.
  **If they take pieces of it and use it themselves, that's the highest compliment** —
  design for extraction.
- The long arc: dial this into a **complete top-to-bottom turnkey community creative
  option**. That's a huge undertaking — participation and contribution along the way
  raise the odds of success. (This is what the Workbench ownership ladder exists to feed.)

## The hard boundary: HEARTH is NOT part of Baseline

**HEARTH is the local MCP for Mechnet** — Derek's personal AI lab and building fleet. It
provides Claude Code integration to leverage local LLMs/GPUs and Gemini flash/pro API
calls. It is **operator infrastructure, not product**.

**Rule for every agent working here: nothing HEARTH/Mechnet ships in a Baseline
package, page, zip, doc, or walkthrough intended for the community.** Concretely:

- No `mcp__hearth__*` dependencies, endpoints (`127.0.0.1:8710`), keys, or
  `C:\work\commandcenter` paths in anything community-facing. (The Workbench privacy
  scanner already flags commandcenter paths — that guard is now understood as a
  product-boundary guard, not just a privacy one.)
- Community-facing automation must run without HEARTH — which is why
  `tools/workbench/new_announcement_draft.py` and `distill_feedback.py` are
  deterministic/LLM-free with optional prompt-out files: the operator's fleet is an
  *accelerant*, never a *requirement*.
- The `network/mcp` Comfy gateway is a different thing — it's Baseline's own localhost
  mod-dev tool and stays in the toolkit; don't confuse the two.

## Why the design is the way it is (context for future agents)

Derek is a 20-year .NET developer and 10+ year Azure solution architect (global supply
chain, DSS, fin-tech, insurance, healthcare, IAM/CIAM; startups through Fortune 50).
Distributed telemetry spans, eventual consistency, and identity are the problems people
hired him to solve — almost always after they were already in production. The GCP spend
was deliberate practice at scale, not naivety. That's why identity, telemetry, and
testing verticals are the first-class citizens here: they are the professional-grade
substrate hobbyist communities never get — and they're the thing Baseline demonstrates.
