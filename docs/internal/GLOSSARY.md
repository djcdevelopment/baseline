# Glossary

One-line definitions for terms used across Baseline's docs, alphabetized.
Each entry was checked against the repo doc(s) named in parentheses.

**Admitted mod release** — The `ComfyNetworkSense` build a given Gateway
image is configured to accept; a separate identity from both the Gateway
image release id and the public client-pull pointer (below). P7 currently
admits `m30-rolecontrol-20260723-r1`. (`Lumberjacks/docs/decision-release-reproducibility-risk-12.md`,
`fieldlab/PINNED-networking-lane-2026-07.md`)

**AoI** — Area of Interest: which world objects/updates a given peer is
relevant enough to receive. Native Valheim still owns this "candidate
relevance" judgment today. (`Lumberjacks/docs/network/area-of-interest-findings.md`,
`fieldlab/docs/adr/0011-aoi-lives-on-the-producer.md`)

**A-track (adoption)** — The A1-A7 roadmap track for community-adoption
work (Discord, the Workbench catalog, onboarding), numbered separately from
the M-milestones below. (`DECISIONS-PENDING.md`, `fieldlab/PINNED-networking-lane-2026-07.md`)

**Baseline** — This repository: the merged toolkit combining the former
`comfy` repo/mods with the Lumberjacks network services, for running a
Valheim community with identity, telemetry, and testing built in as
first-class citizens. (`README.md`, `docs/baseline-vision-and-boundary.md`)

**BepInEx** — The third-party Unity/.NET plugin-loader framework Valheim
mods run under; `ComfyNetworkSense` is pinned to BepInEx 5.4.2202. (`network/mod/ComfyNetworkSense/README.md`,
`fieldlab/docs/harmony-patch-policy.md`)

**Client-pull pointer** — The release id the public modpack-download
endpoint currently serves to players. It can move independently of the
Gateway's admitted mod release but must reference the same underlying mod
identity — e.g. P7's client-pull pointer is `m31-motionphase-20260724-r1`
against admitted release `m30-rolecontrol-20260723-r1`. (`fieldlab/PINNED-networking-lane-2026-07.md`,
`fieldlab/docs/runbook-companion-client-pull.md`)

**Comfy** — Two senses, disambiguate by context: (1) the retired archive
repo (`C:\work\comfy`, github.com/djcdevelopment/comfy) whose content was
merged into this repo's root and is now read-only history; (2) the
community/product display name still used in running surfaces, such as the
Community Workbench page's own title. (`README.md`, `Lumberjacks/docs/workbench/workbench.json`)

**ComfyNetworkSense** — The live BepInEx Valheim mod at
`network/mod/ComfyNetworkSense/`: client/server telemetry, the ZDO
redirect/handshake adapter, and the in-game HUD/debug panel. (`README.md`,
`network/mod/ComfyNetworkSense/README.md`)

**ComfyStewardView** — A separate, standalone public repo (Java, its own
build, nothing to do with the mod or Gateway) that parses a Valheim world
`.db` save file and serves a local map/ownership/economy dashboard. License
is proprietary, not BSL 1.1. (`Lumberjacks/docs/workbench/tools/steward-view.md`,
`HANDOFF-2026-07-29.md`)

**Community Workbench** — The public `/workbench` catalog served by the
Gateway: a stage-ladder listing of community tools generated from
`Lumberjacks/docs/workbench/workbench.json`. Not the Companion workbench
panel or the i5 workbench (see both below). (`HANDOFF-2026-07-29.md`)

**Companion workbench panel** — The operator-facing hub inside the local
Docker "Companion" app (`127.0.0.1:8080`): local readiness, release
identity, live trace, milestone position, and retained evidence for
whoever is running that Companion instance. Not the public Community
Workbench. (`plans/companion-workbench-reconstruction-strategy.md`)

**CRE-Exx** — Numbered creative-runtime experiments under
`fieldlab/experiments/creative-runtime/` (e.g. `cre-e08-adaptive-presentation-replay`)
testing whether Lumberjacks can make mod/presentation work observable,
budgeted, and reversible without prematurely changing Valheim authority.
(`fieldlab/experiments/creative-runtime/README.md`)

**FieldLab** — The experiment workspace at `fieldlab/`: current netcode
research, source-grounded decompilation maps, ADRs, and evidence for the
Valheim netcode-replacement program. (`README.md`, `fieldlab/NETCODE-MAP.md`)

**Golden proof** — Common shorthand for what the repo's own evidence calls
the P7 "gold run" (2026-07-16): the validated, hash-recorded single-client
session in which all 83,220 eligible ZDO revisions were durably received and
acknowledged through Lumberjacks, with zero native fallback. (`fieldlab/evidence/p7-gold-run-20260716-011112-authoritative-priority-cutover/PUBLICATION.md`,
`infra/gcp/p7/README.md`)

**Harmony** — The IL runtime-patching library (HarmonyX 2.10.x) that
`ComfyNetworkSense` uses to hook Valheim methods; patches apply
unconditionally in `Awake` and are feature-gated at runtime inside each
patch body. (`fieldlab/docs/harmony-patch-policy.md`)

**HEARTH / mechnet** — Derek's personal local-AI/build fleet and its MCP
gateway. Operator infrastructure only, explicitly **not part of Baseline**:
nothing HEARTH-related may ship in a community-facing package, page, or doc.
(`docs/baseline-vision-and-boundary.md`)

**i5** — The second Valheim test client machine, a roaming laptop reachable
over the tailnet; also runs its own local Companion instance (informally
"the i5 workbench" in session history). (`AGENTS.md`, `tools/i5/README.md`)

**I-ladder** — The historic I0-I7 integration rungs that preceded the
M-milestones below; superseded as the active schema but preserved as
history. (`Lumberjacks/docs/roadmap/README.md`, `fieldlab/docs/adr/0011-aoi-lives-on-the-producer.md`)

**The journal** — `Lumberjacks/docs/roadmap/commit-notes.jsonl`, the
append-only implementation log with one record per non-merge commit; source
material for the generated `roadmap.html`. (`Lumberjacks/docs/roadmap/README.md`)

**Lumberjacks** — The gateway/services subsystem under `Lumberjacks/`:
Gateway, EventLog, Progression, and OperatorApi, plus the roadmap/journal
tooling. (`README.md`)

**M-milestones** — The active M0...M7 milestone ladder in the living
roadmap (`Lumberjacks/docs/roadmap/valheim-volunteer-roadmap.json`), the
current schema for tracking the Lumberjacks cutover. (`Lumberjacks/docs/roadmap/valheim-volunteer-roadmap.json`)

**OMEN** — Derek's primary machine: the rendered Valheim client and
operator workstation. (`infra/gcp/p7/README.md`)

**P7** — The GCP deployment, VM `comfy-lumberjacks-p7`: a real Valheim world
plus five digest-pinned Lumberjacks services, at comfy-p7.duckdns.org. **The
VM has been terminated since 2026-07-25**, so the hostname does not resolve to
a running service; the public community origin is `am4.tail8e749c.ts.net`.
(`infra/gcp/p7/README.md`, `docs/internal/START-HERE.md`)

**Public source (BSL 1.1)** — The mandated description of Baseline's
license: source is publicly visible under Business Source License 1.1
(converting to AGPL-3.0-only at its Change Date), which is not an
OSI-approved license — so "open source" is banned wording, enforced by a
`roadmap.mjs` lint. (`README.md`, `Lumberjacks/docs/roadmap/valheim-volunteer-roadmap.json`)

**Wave 0** — The non-human-gate command suite under `tools/wave0/` that
reduces live two-client Valheim testing down to the observations only a
human can still provide. (`tools/wave0/README.md`, `fieldlab/PINNED-networking-lane-2026-07.md`)

**ZDO** — Zone Data Object: Valheim's persistent networked world-state
record for an object such as a structure piece, item, creature, or
environmental object. (`Lumberjacks/docs/roadmap/valheim-volunteer-roadmap.json`,
`README.md`)
