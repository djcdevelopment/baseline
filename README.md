# Baseline

**A toolkit to build an entire community on, in Valheim** — with the things most
hobbyist servers never get to have: identity, telemetry, and testing as first-class
parts of the stack instead of afterthoughts.

The communities this is for already do this work — with mods, spreadsheets, Discord
bots, checklists, screenshots. Baseline doesn't replace any of that. It's meant to let
people spend less time on paperwork and tracking, and more time making things.

## Try something right now

**→ [The Community Workbench](https://am4.tail8e749c.ts.net/workbench)**

A catalog of tools you can download and run on your own machine tonight. Every card
says what the thing actually does today — not what it's going to do.

| Tool | What it is |
|---|---|
| **Quest Picker** | Turns a guild's real quest tracker into a page where a player checks off what they're chasing — and the game mod reads the result. |
| **ComfyStewardView** | Reads a Valheim world file and answers what stops being walkable once a server gets big: where is everyone building, and who owns this. |
| **Community Telemetry** | An aggregates-only telemetry API with privacy tests that fail if a player ID, name, or position ever shows up — plus the whole stack, runnable locally. |
| **Steam Self-Service Join** | An invite, a Steam sign-in, and a mod-pack zip with your credentials already in it. Invite-only right now — see below. |

Two more pieces are recoverable but not running, and reviving either one is a real
claim on it. They're listed in the catalog.

More detail, in plain language: **[docs/community/](docs/community/README.md)**.

## Come talk about it

**[Join the Discord](https://discord.gg/JCDaYQ68kN)** — every tool has its own thread.
Running one of these once and saying what happened, including that it broke, is a
complete contribution.

What to expect from a solo-operator project, written down honestly:
**[what alpha means here](docs/community/expectations.md)**.

## What is not open yet

The game server is not open. You can run every tool above on your own machine, but
this is not yet an invitation to come play on the live world — the volunteer platform
isn't ready, and saying otherwise would waste your evening. That work is tracked in
the open on the [roadmap](https://am4.tail8e749c.ts.net/roadmap).

## If you came to read the code

People are expected to read this code, and if you take pieces of it and use them
yourself, that's the highest compliment. Designed for extraction.

- **[docs/internal/START-HERE.md](docs/internal/START-HERE.md)** — which era each area
  belongs to, so you don't act on the wrong one. Read this before anything else.
- **[docs/internal/BUILDING.md](docs/internal/BUILDING.md)** — the two build
  environments, and the commit ceremony that will otherwise fail you.
- **[CONTRIBUTING.md](CONTRIBUTING.md)** — current posture. Honest about what isn't
  accepted yet.
- **[docs/baseline-vision-and-boundary.md](docs/baseline-vision-and-boundary.md)** —
  what this is for, and where its edges are.
- **[docs/internal/GLOSSARY.md](docs/internal/GLOSSARY.md)** — the terms, including the
  three different things called "workbench".

The four load-bearing areas:

- **[`Lumberjacks/`](Lumberjacks/README.md)** — the service stack: Gateway, eventlog,
  progression, operatorapi, plus the append-only roadmap journal.
- **[`network/mod/ComfyNetworkSense/`](network/mod/ComfyNetworkSense/README.md)** — the
  BepInEx plugin: ZDO redirect, handshake, telemetry, quest tracking.
- **[`fieldlab/`](fieldlab/NETCODE-MAP.md)** — the netcode-replacement R&D program and
  its ground truth.
- **[`infra/gcp/p7/`](infra/gcp/p7/README.md)** — release, deployment, and rollback.

⚠️ `main` is force-pushed by background automation. Long-lived branches and forks rot
fast — read [AGENTS.md](AGENTS.md) before you touch anything.

How this repo got its shape (the merge, and the July 2026 prune):
[docs/internal/repo-history.md](docs/internal/repo-history.md).

## License

Public source under the [Business Source License 1.1](LICENSE), with an automatic
Community Steward grant for small operators — up to 100 active members and USD 25,000
aggregate community revenue per rolling year, while publishing their complete deployed
source. Qualifying stewards keep the profit, no separate agreement, no royalty. Each
version converts to AGPL-3.0-only no later than the Change Date in `LICENSE`.

Plain-language scope: [docs/legal/LICENSING.md](docs/legal/LICENSING.md). Larger use:
[docs/legal/COMMERCIAL.md](docs/legal/COMMERCIAL.md). Operating principles:
[docs/legal/STEWARDSHIP.md](docs/legal/STEWARDSHIP.md). Attribution and exclusions:
[docs/legal/NOTICE.md](docs/legal/NOTICE.md) ·
[docs/legal/THIRD_PARTY_NOTICES.md](docs/legal/THIRD_PARTY_NOTICES.md).

*Not affiliated with or endorsed by Iron Gate AB or Coffee Stain Publishing.*
