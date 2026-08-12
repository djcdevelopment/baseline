# Baseline → Sovereign Repos Split

## Context

The unified `baseline` repo proved out the verticals (telemetry mod, transport platform, quest product). Per `sovereign-logical-architecture-guide.md` and Derek's direction, it's time to isolate them into sovereign repos — each with documented rules to maintain its integrity — plus an index home for architecture questions so future sessions don't scan every repo to understand the system.

Facts that shape the plan (all verified in-repo):
- **Sovereign-Shards has zero existing code** — every named artifact (shard_manager.py, ComfyPortalRouter, armory daemon, !party bot, JWT) is absent. That repo is a charter + scaffold, not a migration.
- **The seams don't fall where the guide draws them**: ~6,800 LOC of Lumberjacks client transport lives inside the ComfyNetworkSense assembly; `Game.Companion.csproj:13` hard-references `ComfyQuestContracts`; the quest contract glue (6 files) lives inside ComfyNetworkSense and is link-compiled into ComfyQuestLab; `tools/`, `tests/`, `fieldlab/` and the roadmap journal each span every seam.
- **History warns us**: the July unification happened because the two-repo split caused ownership fights and the stale-checkout-root hazard (commit `8cd4917b`: 30 commands + 4 scripts silently succeeding against retired roots; `deploy-gateway.ps1` nearly shipped stale code with a passing hash). PD-8/isolate is the measured precedent for a "decorative" boundary (byte-identical compose that would adopt the live lab's state; `/identity` that can't distinguish repos; a contract file nothing reads). Every guard in this plan is designed to be able to fail (ADR 0019).

**Operator decisions (locked):** baseline becomes the index repo · Quest gets its own sovereign repo · shared contracts travel as NuGet packages · history moves via git-filter-repo (with secret-scrub mitigations).

## Target topology (5 repos)

| Repo | Contents | Integrity anchor |
|---|---|---|
| **baseline** (existing, public, keeps URL + full history) | INDEX: architecture guides, REPO-MAP.md, PORTS.md, PD register, corpus/site/data, handoffs/plans/retros, fieldlab **evidence archive** | `test_entrypoint_links.py`, corpus `--check`, Pages |
| **networksense** (new) | `network/mod/ComfyNetworkSense{,.Tests}`, `network/{docs,contracts,design_mocks,tools}`, tuning ledgers, `tools/{i5(mod lanes),am4,modpack,synthetic-baseline-extractor}` | byte-deterministic DLL releases (`mod-v*` tags), 277 xunit tests |
| **lumberjacks-platform** (new; `Lumberjacks` name is taken by the retired archive) | `Lumberjacks/` (minus oldimages), `infra/gcp/p7`, fieldlab **live harness**, `tools/{p7,wave0,workbench,authority-lab,guest-package}`, `.githooks` + roadmap journal/ceremony | Game.sln container verify, roadmap:check, p7 artifact-hash gate |
| **comfy-quest** (new) | `network/mod/{ComfyQuestLab,ComfyQuestRuntime,ComfyQuestContracts}`, new `ComfyQuestLab.Tests`, `Quest.Studio` (carved from Game.Companion), `tools/{component-packets,questlab-*,quest-packs,quest-bridge,quest-runtime,blueprints}`, `recipes/quest-catalogs`, 17 quest py tests | contracts package publish, questpack round-trip tests |
| **sovereign-shards** (new, greenfield) | Corrected guide as founding doc, charter, port claim **:8730** (guide's :8721 collides with PD-6 Dev MCP), roadmap of the absent components labeled per PD-4 (`UNVERIFIED`/planned) | boundary charter + CI scaffold before any code |

`network/mcp` gets **no new repo** — reconcile with the existing `C:\work\isolate` (github.com/djcdevelopment/isolate, PD-8), then remove from baseline. `Lumberjacks/network/mcp` (second mcp tree) travels with lumberjacks-platform into the same reconciliation.

Default assignments (veto anytime): `data/`, `captures/`, `artifacts/`, `erasave/`, remaining `recipes/`, `tools/{selfie-stick,dispatches,site,corpus,am4-gallery}` stay in baseline-index.

## Shared contracts (the seam-cutting mechanism)

Two **source-only NuGet packages** (netstandard2.0, contentFiles `buildAction=Compile`) — source packages because the mods must keep compiling identical contract source into single BepInEx DLLs (the doctrine written into the csprojs), and byte-deterministic DLL identity must survive:

1. **`Comfy.Quest.Contracts`** (home: comfy-quest) — existing `ComfyQuestContracts` + the 6 glue files moved from `ComfyNetworkSense/Core/` into `ComfyQuestContracts/ModGlue/`: `TrackedQuest.cs`, `QuestEvent.cs`, `QuestViewLoader.cs`, `QuestTriggerEvaluator.cs`, `QuestEventCatalog.g.cs`, `QuestAuthoring.cs`. Consumers: ComfyNetworkSense (contentFiles), ComfyQuestLab (contentFiles), Game.Companion (compiled asm, `ExcludeAssets="contentFiles"`), ComfyQuestRuntime.
2. **`Comfy.Transport.Contracts`** (home: lumberjacks-platform) — `ValheimRoutedRpcAdmissions.cs` (verified ns2.0-clean) + 4 policy files moved to `Game.Contracts/Policies/`: `ZdoIntegrationContract`, `ZdoBandPolicy`, `ZdoFanoutPolicy`, `VehicleSnapshotRelevanceSet`. Consumers: ComfyNetworkSense, its Tests, authority-lab.
3. **`Comfy.Quest.Studio`** (home: comfy-quest) — net9.0 library carved from Game.Companion: `QuestStudioService.cs` (198), `QuestStudioPage.cs` (35), `QuestPackPublisher.cs` (79), endpoint maps from `WorkbenchKernel.cs:771-835` → exposed as `QuestStudioEndpoints.Map(app, IQuestStudioHost)`. Companion stays the host (per `docs/quest-studio-runtime-boundary.md`); `.questpack` files remain the runtime handoff. Bonus: fixes the latently broken Companion container build.

Publish via GitHub Actions on `nuget-v*` tags → **NuGet.org** (public toolkit; GitHub Packages needs a PAT to read — rejected). Semver from 0.1.0. Packages are for **cross-repo** consumption only; in-repo consumers keep ProjectReference. Add `PathMap` to mod csprojs so SHA-verified DLL lanes stay byte-deterministic — **assert byte-identical DLL before/after every contract switch**.

Cross-repo integration beyond contracts = **files as handoff, never source reach-ins** (house pattern): mod DLL releases with manifest+sha256, `questlab.html` as a published artifact vendored by `Lumberjacks/tools/Update-QuestLabHtml.ps1` (pinned repo/tag/hash), corpus mirrors under `corpus/mirrors/lumberjacks/` (pattern already exists for Discord mirrors).

## Phase 0 — Pre-flight (baseline, no surgery yet)

1. **Locate + disarm the force-pusher** before any history work. Verified NOT it: Windows scheduled tasks, HEARTH `git.py` (plain push, no baseline grant). Check: `gh api 'repos/djcdevelopment/baseline/activity' -f activity_type=force_push` (names the actor), `C:\work\omen-perception\cycle.sh`, HEARTH `etc/operations.toml` lanes. Disable; require 48h quiet before extraction.
2. **Correct the guide** and commit it (currently untracked): (a) drop/redraw the missing PNG reference; (b) F6 HUD → console commands (`network_sense_hud`), no keybinding exists; (c) "10% movement+stamina buff" → documented design is "+5% stamina regen" ("Low Impact"), no FarmMode code shipped — label aspirational; (d) Shard Manager port :8721 → **:8730** (PD-6 owns :8721, live today); (e) armory_snapshot/OnEquipmentChange flow → "planned, not shipped" (Runtime has only input/kill patches); (f) delete the stray byte-identical copy at `tests/sovereign-logical-architecture-guide.md`; (g) reframe "three repository verticals" to this five-repo topology.
3. **Tag + archive**: tag `pre-split-20260811`; `git clone --mirror` → `C:\work\_archive\baseline.git`.
4. **Retire stale roots loudly**: move `C:\work\comfy`, `C:\work\Lumberjacks` → `C:\work\_retired\` (they hold gitignored artifacts — move, never delete). Stale paths must FAIL, not quietly succeed.
5. **Names + accounts**: create the 4 GitHub repos; reserve 3 NuGet IDs; add `NUGET_API_KEY` secrets. Naming default: `lumberjacks-platform` (rename at will).
6. **`docs/PORTS.md`** in baseline: 8710 HEARTH / 8721 Dev MCP / 8722 provenance / 8730 Shard Manager (reserved).

## Phase 1 — Decouple in place (still one repo; everything verifiable before any repo exists)

Local NuGet feed rehearsal: `artifacts/nuget/` + root `nuget.config`.

1. Pack `Comfy.Quest.Contracts` with the ModGlue move; update `generate_seam_catalog.py` output path (it then writes into comfy-quest's tree; networksense receives the catalog via the package — no more cross-seam generator writes).
2. Retarget consumers (ComfyNetworkSense.csproj drops quest source; ComfyQuestLab.csproj drops lines 94-99; Game.Companion.csproj:13 → PackageReference). **Gate: byte-identical mod DLLs.**
3. Pack `Comfy.Transport.Contracts`; mod drops its `..\..\..\Lumberjacks\...\ValheimRoutedRpcAdmissions.cs` link (csproj:71); authority-lab repoints. **Gate: byte-identical again.**
4. Split the fused test project: new `network/mod/ComfyQuestLab.Tests/` (net8) takes the 17 quest links + LiveTest manifests; `ComfyNetworkSense.Tests` keeps transport/policy/codec tests + `synthetic_baseline_v2.json`.
5. Quest Studio carve → `Lumberjacks/src/Quest.Studio/` + local-feed `Comfy.Quest.Studio`; Companion adapts via `IQuestStudioHost` (WorkbenchStore/ValheimLocator/auth/Json.Options adapters).
6. Script retargets: `tools/i5` split by lane (mod scripts stay; `Sync-I5Companion.ps1`/`Start-I5Companion.ps1` → `Lumberjacks/tools/companion/`; `Invoke-I5QuestLabBatch.ps1` + its test → quest set); `New-WorkbenchZip.ps1` split by `-Tool` branch, blob URLs parameterized `-RepoBlobBase`; `Invoke-HeadlessValheimLab.ps1:102` → `-ModDll` artifact param; p7 scripts gain `-ModArtifact` (hash-verified) replacing source-tree pins; `render_quest_lab.py --out`.
7. **Full green gate** (all builds + all test suites + roadmap:check) → tag **`split-base-20260811`** — the SHA every PROVENANCE.md records.

## Phase 2 — Extraction (per repo: filter → scrub → scaffold → push)

Fresh clone → `git filter-repo` with explicit `--path` lists (paths preserved, no renames — every `$PSScriptRoot\..\..` hop keeps working). Lumberjacks pass adds `--invert-paths` for `Lumberjacks/oldimages` + `--strip-blobs-bigger-than 5M`.

**Scrub before first push (mandatory, per origin push-protection precedent):** gitleaks over full filtered history → `--replace-text` rewrites for fixture credentials (never allow-this-secret URLs) → PD-3 spot-check (no other-people's-data blobs in slices; `data/` stays in baseline anyway) → commit-map committed to `docs/provenance/` → `PROVENANCE.md` ("extracted from baseline@split-base-20260811", filter invocation).

**Scaffold in each repo:** `AGENTS.md` (landing protocol adapted; the four-blockers list minus roadmap ceremony except lumberjacks-platform), `CLAUDE.md` pointer, `LICENSE` (BSL 1.1, PD-1 rights per repo), `SECURITY.md`, `BOUNDARY.md` (owns / does_not_own — reuse the roadmap milestone vocabulary), `tools/Assert-RepoIdentity.ps1` (git-remote assert; entry scripts call it — the tested control for the stale-root hazard), `ci.yml` (build + tests + guards). Roadmap journal + pre-commit ceremony port **only** to lumberjacks-platform (its hook paths are all `Lumberjacks/...` — works unchanged). sovereign-shards is born from the corrected guide + PORT-CLAIM :8730 + charter; no code.

## Phase 3 — Retarget + publish

`publish-nuget.yml` on `nuget-v*` → NuGet.org. Mod releases on `mod-v*` (DLL + manifest.json + sha256). comfy-quest artifact releases (questlab.html, workbench zips recorded by sha256+bytes in workbench.json access blocks). Consumers pin exact versions — **this is the rollback commitment point**: before it, everything still runs from baseline; after it, rollback = repin. p7 smoke test against a real published mod release.

## Phase 4 — Baseline slims into the index repo

- `git rm -r` moved trees (ordinary commits — baseline history is never rewritten; it remains the browsable archive).
- Write **`REPO-MAP.md`** — the "ask questions here" surface: surface → repo → path → artifact contract → owning guard. Rewrite `README.md` doors, `docs/internal/START-HERE.md` (cross-repo era map), `GLOSSARY.md`; banner stale area docs.
- **PD-9: repository split** in `docs/decisions/` (rationale, the reintroduced ownership questions — production compose and env-template now explicitly owned by lumberjacks-platform — and the PD-8 lessons applied). Amend PD-8 (isolate has a remote now; reconciliation done here).
- Corpus: add `corpus/mirrors/lumberjacks/{workbench.json,commit-notes.jsonl}` + provenance.json; repoint `corpus/sources.json:11,16`; drop `Lumberjacks/**` triggers from `pages.yml`. Pages stays green.
- Reconcile + remove `network/mcp` (→ isolate); drop `.githooks` from baseline; repoint the disarmed pusher (non-force only) or retire it.

## Phase 5 — Verification matrix

Per-repo: networksense `dotnet build` net48 (host dotnet 8, PluginOutputPath guard) + `dotnet test` (net8, 277 cases); lumberjacks-platform container `dotnet test Game.sln` verify stage + `npm run roadmap:test` + compose up; comfy-quest mod builds + ComfyQuestLab.Tests + 17-module unittest suite + questpack round-trip; baseline `python -m unittest discover -s tests` (remaining) + `tools/corpus/build.py --check`; sovereign-shards CI scaffold green.

Integration lanes: **I1** mod release artifact → p7 hash gate matches; **I2** Studio publish → `.questpack` → Runtime Check/Load on OMEN; **I3** questlab.html vendor script hash-verifies; **I4** corpus mirror → Pages build; **I5** headless lab boots with the released DLL and `/identity` names the right repo.

Named guards, each with a checked-in bad fixture proving it CAN fail (ADR 0019): **G1** no-reach-in grep (no `..\..\..\network`-style cross-repo hops, no `C:\work\` absolutes); **G2** Assert-RepoIdentity; **G3** compose project-name uniqueness (the PD-8 state-adoption failure); **G4** `/identity` distinguishes repos; **G5** clean-clone package-only build; **G6** p7 artifact-hash gate; **G7** generated-file drift `--check`; **G8** corpus snapshot provenance.

## Execution notes

- Order: Phase 1 is the de-risking heart — every coupling is cut and verified **while still in one repo**. Extraction only proceeds from a green `split-base` tag.
- Offload per house rules: gitleaks triage summaries, README/charter first drafts, commit-map audits → HEARTH (`gcp-gemini`); frontier context reserved for the csproj surgery, carve adapters, and filter-repo path lists.
- Roadmap-note ceremony applies to the Phase 1 commits (they touch `network/` + `Lumberjacks/`): one note per landing round, not per file.
- Risks: (1) filtered history re-triggering push protection → scrub step is mandatory, rewrite-not-allow; (2) DLL identity drift from NuGet paths → PathMap + byte-identity gates; (3) live P7/AM4 lanes mid-cutover → p7 `-ModArtifact` keeps old `-Path` form working until Phase 3 repin; (4) the force-pusher racing the migration → Phase 0 gate, 48h quiet.
