# Baseline — vision and product boundary

Recorded 2026-07-29 from Derek's own framing (lightly cleaned; treat this as the canonical
product statement until he revises it).

> **Repository-authority amendment — 2026-08-12.** “Baseline” below names the
> product thesis and fleet assembled in the monorepo era. The Baseline repository is
> now the knowledge, evidence, corpus, and discovery hub. Active implementation lives
> in the sovereign repositories indexed by [REPO-MAP.md](../REPO-MAP.md); this page
> does not grant the hub ownership of their code or runtime state.

## What the Baseline fleet is

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
- Community-facing automation must run without HEARTH. Workbench automation owned by
  `lumberjacks-platform` remains deterministic/LLM-free where a private model would
  otherwise become a requirement: the operator's fleet is an *accelerant*, never a
  dependency.
- The `network/mcp` Comfy gateway is a different thing: it is a project-local,
  containerized development surface owned and released by
  [`isolate`](https://github.com/djcdevelopment/isolate), not HEARTH and not the
  Baseline hub. Do not confuse the two.
- A loopback port is not a project identity. The released Isolate MCP must self-attest its
  source root, revision/hash, image, profile, provider set, caller registry, ledger,
  and selected port; a healthy listener from another checkout is a provenance failure.
  Its canonical Compose publication is `127.0.0.1:8722`. Port `8721` was the explicit
  pre-split Baseline Dev/Lab publication; the legacy `ComfyGatewayBoot` task was
  disabled without deletion and its retired `:8720` listener was stopped.
- **The rule runs in BOTH directions, and the inbound one is the easier to miss.**
  Everything above forbids HEARTH leaking *out* into Baseline. The reverse is equally
  forbidden: **fleet products must not report into, register with, or depend on HEARTH
  as a destination** — no product runtime telemetry, runner timings, job state, or ledger
  writes routed to `mcp__hearth__*`, a "Hearth Hub", or anything else on the operator's
  fleet. HEARTH is Derek's *cross-project* lab door, shared by every repo he works in;
  wiring one project's machinery into it makes a general-purpose tool carry a single
  project's concerns, and silently makes Baseline's behaviour depend on hardware no
  contributor has. If a product needs a hub, its owning repository ships one.
  (Added 2026-08-01: a proposal to route per-runner `Update` timings into "Hearth Hub"
  cleared every bullet above, because all of them were written outbound-only.)

## Why the design is the way it is (context for future agents)

Derek is a 20-year .NET developer and 10+ year Azure solution architect (global supply
chain, DSS, fin-tech, insurance, healthcare, IAM/CIAM; startups through Fortune 50).
Distributed telemetry spans, eventual consistency, and identity are the problems people
hired him to solve — almost always after they were already in production. The GCP spend
was deliberate practice at scale, not naivety. That's why identity, telemetry, and
testing verticals are the first-class citizens here: they are the professional-grade
substrate hobbyist communities never get — and they're the thing Baseline demonstrates.

## Related product decisions and operating model

- [PD-5 — The local Workbench is Baseline's ownership appliance](decisions/pd-5-local-workbench-ownership-appliance.md)
- [PD-6 — The Baseline Dev MCP is a development/lab-only control plane](decisions/pd-6-development-mcp-lifecycle.md)
- [PD-9 — Sovereign add-on repositories with Baseline as the hub](decisions/pd-9-repository-split.md)
- [Baseline Workbench operating model](workbench-operating-model.md)
- [2026-08-01 product and development-loop review](audit/2026-08-01-workbench-product-review.md)
