# Start Building

You know *what* you want to change. This page tells you *where*. Find your intent in
the left column of the table below, open that repo at the listed path, run the listed
command, and satisfy the listed gate — that is the whole answer for the large majority
of changes. Cross-repo work is the exception, not the norm: if your change genuinely
needs two repos (you're editing a shared contract type, or shipping a built artifact
another repo consumes), skip to ["It crosses a boundary"](#it-crosses-a-boundary)
below, which gives you the ordered recipe and the guard that fires if you skip a step.

This page is task-oriented. For the surface-oriented view (surface → repo → path →
artifact → guard, one row per owned thing rather than per intent), see
[`REPO-MAP.md`](REPO-MAP.md). For runtime port ownership, see
[`docs/PORTS.md`](docs/PORTS.md).

All five product repos live as sibling checkouts under `C:\work\`: `networksense`,
`lumberjacks-platform`, `comfy-quest`, `sovereign-shards`, `isolate`. Baseline
(this repo) never regains implementation as a convenience copy — it indexes.

## The routing table

| I want to… | Repo | Start in | Build/test command | Gate you must pass |
|---|---|---|---|---|
| Add/change a client HUD panel, telemetry metric, or Owner Score input | `networksense` | `network/mod/ComfyNetworkSense/Core/Services/` (`NetworkSensePanel.cs`, `HudRenderer.cs`, `ScoreCalculator.cs`) | `dotnet test network/mod/ComfyNetworkSense.Tests/ComfyNetworkSense.Tests.csproj -c Release -p:ComfyDependencyProfile=interim` — must report exactly 166/166 | CI `tests` job's exact-count assert (166 total/passed/0 failed) + `tools/Test-BoundaryGuards.ps1` |
| Change ZDO/replication policy or transport admission behavior | `lumberjacks-platform` | `Lumberjacks/src/Comfy.Transport.Contracts/Policies/` (band/fanout/relevance policy) and `Lumberjacks/src/Game.Gateway/Valheim/ValheimZdo*.cs` | `dotnet build Lumberjacks/Game.sln -c Release && dotnet test Lumberjacks/Game.sln -c Release --no-build` (use `C:\work\dotnet9\dotnet.exe` — SDK9) | `ci.yml` `dotnet` job; G4 service-identity contract if the Gateway's `/identity` surface changes |
| Add a quest event, trigger, or action type | `comfy-quest` | `network/mod/ComfyQuestContracts/ModGlue/` (`QuestEvent.cs`, `QuestTriggerEvaluator.cs`, `QuestAuthoring.cs`) — event catalog is generated (`QuestEventCatalog.g.cs`) | `dotnet test network/mod/ComfyQuestLab.Tests/ComfyQuestLab.Tests.csproj -c Release --no-restore` then `python tools/component-packets/generate_seam_catalog.py --check` | CI `quest` job; G7 generated-file-drift (`generate_seam_catalog.py --check`, `render_quest_lab.py --check`) |
| Author/change quest content and publish a questpack | `comfy-quest` | `recipes/quest-catalogs/` (source content) and `tools/quest-packs/quest_pack.py` (packaging) | `python -m unittest discover -s tests` (covers `test_quest_packs.py`, `test_gallery_profiles.py`) | CI `quest` job's Python suite; release path is `tools/release/New-QuestRelease.ps1` → `verify_quest_release.py` |
| Change Quest Studio's authoring UI or endpoints | `comfy-quest` | `src/Quest.Studio/` (`QuestStudioEndpoints.cs`, `QuestStudioService.cs`, `QuestStudioPage.cs`, `IQuestStudioHost.cs`) | `dotnet pack src/Quest.Studio/Quest.Studio.csproj -c Release --no-restore` | CI `quest` job. The Companion adapter (`QuestStudioHostAdapter.cs` in `lumberjacks-platform`, `Lumberjacks/src/Game.Companion/`) implements `IQuestStudioHost` against the published `Comfy.Quest.Studio` package — a host-side signature change needs a coordinated repin (see boundary recipe a) |
| Change the Quest Lab in-game panel or gallery | `comfy-quest` | `network/mod/ComfyQuestLab/Ui/` (`LabPanel.cs`, `LabRunes.cs`) and `network/mod/ComfyQuestLab/Core/LabGalleryBuilder.cs` | `dotnet test network/mod/ComfyQuestLab.Tests/ComfyQuestLab.Tests.csproj -c Release --no-restore` | CI `quest` job; `licensed-mod-source` job only asserts the csproj exists — the real Lab DLL build with licensed Valheim assemblies is local-cutter only, not CI |
| Change gateway/session/handshake server behavior | `lumberjacks-platform` | `Lumberjacks/src/Game.Gateway/Valheim/` (`ValheimHandshakeService.cs`, `ValheimHandshakeEndpoints.cs`) and `Lumberjacks/src/Game.Gateway/WebSocket/` (`SessionManager.cs`, `MessageRouter.cs`) | `dotnet test Lumberjacks/Game.sln -c Release --no-build` | CI `dotnet` job; `containers` job (`docker build --target verify -f Lumberjacks/Dockerfile Lumberjacks`) if the change touches startup/DI; G4 `/identity` contract |
| Change the Companion (loopback Workbench host) | `lumberjacks-platform` | `Lumberjacks/src/Game.Companion/` (`WorkbenchKernel.cs`, `WorkbenchCatalog.cs`, `CompanionPage.cs`) | `dotnet test Lumberjacks/Game.sln -c Release --no-build` (`Lumberjacks/tests/Game.Companion.Tests/`) then `docker build -f Lumberjacks/src/Game.Companion/Dockerfile Lumberjacks` | CI `dotnet` + `containers` jobs; G4 `/identity`; `npm run workbench:check` if the catalog/manifest shape changes |
| Add or change a deploy/release lane (mod release, P7, i5, AM4) | mod cut: `networksense`; P7/AM4: `lumberjacks-platform`; i5 mod install: `networksense`; MCP/Gateway-image AM4 lane: `isolate` | mod cut `network/tools/New-ModReleaseCut.ps1` (networksense); P7 `infra/gcp/p7/scripts/New-GatewayReleaseCut.ps1` + `Promote-GatewayImage.ps1` (lumberjacks-platform); i5 `tools/i5/Deploy-ToI5.ps1` (networksense); AM4 Gateway image `tools/am4/Deploy-GatewayImage.ps1` (isolate) | Each script has a `-DryRun`/read-only mode — run that first | G6 artifact-hash gate (`Test-ArtifactHashGate.ps1`, p7 release cut aborts on DLL SHA mismatch vs the networksense manifest); `-ModArtifact` flag on `deploy-network-sense.ps1` is the hash-checked mod input |
| Change the roadmap journal / public roadmap page | `lumberjacks-platform` | `Lumberjacks/docs/roadmap/` (append a note) → auto-renders to `Lumberjacks/src/Game.Gateway/Community/roadmap.html` | `cd Lumberjacks; node scripts/roadmap.mjs note --milestone <id> --kind <kind> --summary "..." --impact "..." --verification "..."` (regenerates the HTML as part of adding the note — `npm run roadmap:render` exists separately only for re-rendering without a new note) | `npm run roadmap:test && npm run roadmap:check`; CI `roadmap-workbench` job. This repo's pre-commit hook enforces jsonl+html land together — see house rules below, this ceremony is unique to lumberjacks-platform |
| Change the public site, corpus projections, or a decision record | `baseline` (this repo) | `site/` (pages), `corpus/` (`sources.json`, `mirrors/`), `docs/decisions/` (PDs) | `python tools/corpus/build.py --check` and `python -m unittest discover -s tests -v` | G8 corpus-snapshot-provenance (`build.py --check` fails on stale/mismatched mirror SHA); `test_entrypoint_links` |
| Start any sharding/portal-router/Discord-bot/sidecar work | `sovereign-shards` | `docs/sovereign-logical-architecture-guide.md` first — **the repo has zero code**; `router/`, `shard-manager/`, `sidecar/`, `bot/` don't exist yet | none yet — "the first component lands with its own gate, named in its PR, before any second component" (repo's own AGENTS.md) | `tools/Assert-RepoIdentity.ps1`; `tools/check_boundary.py --self-test` (port-claim + no-reach-in); CI `guards` job |
| Change the MCP gateway or lab containers | `isolate` | `network/mcp/comfy_gateway/` (kernel, toolsurface) and `docker/` (compose), `network/mcp/Dockerfile` | `$env:PYTHONPATH = "$PWD\network\mcp"; python -m unittest discover -s network\mcp\tests` | CI `test-and-build` job (25/25 tests) + `docker build -t comfy-gateway:<sha> network/mcp`; any transport/API change must update `network/mcp/contracts/api-contract.json` |
| Add a shared contract type used by more than one repo | Owning repo depends on the contract: `Comfy.Quest.Contracts` → `comfy-quest` (`network/mod/ComfyQuestContracts/`); `Comfy.Transport.Contracts` → `lumberjacks-platform` (`Lumberjacks/src/Comfy.Transport.Contracts/`) | Edit in the **owning** repo only, then version-bump and republish | package build/pack per repo's CI `quest`/`dotnet` job | This is a boundary-crossing change — do not edit a consumer's copy. Follow recipe (a) below |

## It crosses a boundary

Four recurring cross-repo change shapes. Each names the guard that fails if a step is
skipped.

**(a) Changing a shared contract type** (`Comfy.Quest.Contracts` or
`Comfy.Transport.Contracts`)
1. Edit the type in the owning repo (`comfy-quest` for Quest, `lumberjacks-platform`
   for Transport).
2. Bump the package version (exact-pin discipline: `[0.1.0]`-style constraints
   throughout, no floating ranges).
3. Publish — today that means to the vendored `packages-local/` feed each repo carries
   (see [blockers](#current-blockers-honestly-labeled) — NuGet.org publication is not
   live yet). The `nuget-v*` tag workflow (`publish-nuget.yml` in both `comfy-quest`
   and `lumberjacks-platform`) is the intended real lane once `NUGET_API_KEY` exists.
4. Repin every consumer to the **exact new version** — `lumberjacks-platform`'s
   `tools/dependencies/Set-DependencyProfile.ps1 -Profile interim -Check` (or
   `-Profile public`) is the coordinated-repin gate; `comfy-quest`'s
   `tools/nuget/repin_public.py --check-interim` is the equivalent there.
- **Guard that fails if you skip a step:** G1 no-reach-in (CI greps every repo for
  `..\..\..\<repo>` / `C:\work\` paths — a consumer that didn't repin and instead
  pointed at a sibling checkout gets caught here) and the dependency-profile
  self-check scripts above, which fail on a stale or floating version.

**(b) Shipping a mod DLL to a deploy lane** (mod release → P7/i5/AM4)
1. Cut the release in `networksense`: `network/tools/New-ModReleaseCut.ps1` builds
   Release, produces `release-manifest.json` + `SHA256SUMS`.
2. Tag `mod-v*` and publish the GitHub release (assets: the DLL, manifest, boundary
   receipt, SHA256SUMS) — **not done yet fleet-wide**, see blockers.
3. The consuming deploy script takes `-ModArtifact` (e.g.
   `infra/gcp/p7/scripts/deploy-network-sense.ps1 -ModArtifact <path-or-release>` in
   `lumberjacks-platform`, or the i5 lane in `networksense`) and hashes the artifact
   against the manifest before it will admit it.
- **Guard that fails if you skip a step:** G6 artifact-hash gate
  (`Test-ArtifactHashGate.ps1` in `lumberjacks-platform` CI, and the P7 release-cut
  script's own hash-match check against the networksense manifest) — a DLL that
  doesn't match its declared manifest hash aborts the cut, it never deploys silently
  wrong.

**(c) A generated artifact consumed elsewhere** (`questlab.html`, Quest Lab/picker
zips)
1. Generate/verify in `comfy-quest`: `docs/generated/questlab.html` via
   `tools/component-packets/render_quest_lab.py --check`; zips via
   `tools/questlab-package/New-QuestLabZip.ps1` / `New-QuestPickerZip.ps1`.
2. Cut a `quest-v*` release with manifest + SHA-256 sums
   (`tools/release/New-QuestRelease.ps1`, verified by `verify_quest_release.py`) —
   **no quest releases exist yet**, see blockers.
3. Vendor the pinned tag+hash into the consumer. `lumberjacks-platform` already
   serves a copy at `Lumberjacks/src/Game.Gateway/Community/questlab.html`, but the
   automated pinned-vendor step (an `Update-QuestLabHtml.ps1`-shaped script) is
   **UNVERIFIED / does not exist yet** — this is planned Phase-5 lane I3, currently
   blocked on there being a comfy-quest release to pin.
- **Guard that fails if you skip a step:** G7 generated-file-drift
  (`render_quest_lab.py --check` / `generate_seam_catalog.py --check` in comfy-quest
  CI) catches un-regenerated output; on the consumer side, once I3 lands, a hash
  mismatch against the pinned release tag is the intended failure mode.

**(d) Corpus mirror refresh** (platform journal → baseline mirror → Pages)
1. Land the milestone in `lumberjacks-platform` (a pushed 40-character commit SHA on
   its `main`).
2. In `baseline`: `python tools/corpus/sync_lumberjacks_mirror.py --revision <sha>`
   then `--check --revision <sha>`.
3. `python tools/corpus/build.py && python tools/corpus/build.py --check`.
4. Commit the two snapshots, the provenance receipt, and the regenerated projections
   together; push — Pages deploys from `main`.
- **Guard that fails if you skip a step:** G8 corpus-snapshot-provenance —
  `build.py --check` fails when a file, hash, byte count, upstream path, or revision
  in the mirror doesn't match `provenance.json`'s recorded upstream SHA.

## Current blockers, honestly labeled

- **No NuGet package is published to NuGet.org.** `Comfy.Quest.Contracts`,
  `Comfy.Quest.Studio`, and `Comfy.Transport.Contracts` all resolve from each repo's
  vendored `packages-local/` feed (see each repo's `nuget.config`) via the `interim`
  dependency profile. The `public` profile with exact `[0.1.0]` NuGet.org pins exists
  in code but is unusable. **Unblocks when:** `NUGET_API_KEY` is added as a secret to
  `networksense`, `lumberjacks-platform`, and `comfy-quest`, and the three package IDs
  are reserved on nuget.org (both operator-owned, per
  `docs/internal/repo-split/HANDOFF-RECOVERY.md`).
- **Zero GitHub releases exist fleet-wide.** No `mod-v*` tag in `networksense`, no
  `quest-v*` tag in `comfy-quest`, no Gateway image release cut yet exercised on P7.
  The verify-release CI workflows (`verify-mod-release.yml`,
  `verify-quest-release.yml`) and the artifact-hash deploy gates (G6) are wired and
  passing on fixtures/self-tests, but **unexercised end-to-end** — nothing has gone
  through them for real. **Unblocks when:** the operator explicitly starts the
  publication step (both repos' `AGENTS.md` gate this on an explicit operator
  go-ahead, not an agent's own initiative).
- **`sovereign-shards` has zero code.** `router/`, `shard-manager/`, `sidecar/`,
  `bot/` are named in the architecture guide and `BOUNDARY.md` but none of those
  directories exist on disk. The repo's own AGENTS.md is explicit: "none yet — this
  repo has no code." **Unblocks when:** someone picks the first component (Shard
  Manager Daemon is the port-claimed one, `:8730`) and lands it with its own CI gate.
- **The `questlab.html` vendor step (I3) doesn't exist.** `lumberjacks-platform`
  serves a hand-placed copy at `Community/questlab.html`; there's no automated
  pinned-tag+hash import script yet. Blocked on the quest-release blocker above —
  there's nothing real to pin against.

## House rules that apply in every repo

- **No cross-repo source reach-ins.** Integration is pinned artifacts only —
  published packages or hash-verified release files. Never a relative path into a
  sibling checkout, never a hardcoded `C:\work\<other-repo>`. Every repo's CI runs a
  G1-shaped no-reach-in guard with a checked-in bad fixture that must fail the guard
  (self-test).
- **Scripts derive their root from `$PSScriptRoot`** (or their own repo context for
  Python/Node) and call `tools/Assert-RepoIdentity.ps1` (G2) before any
  state-changing action. A script never assumes `C:\work\...` or a sibling checkout
  exists.
- **Only `lumberjacks-platform` carries the per-commit roadmap-note ceremony.** A
  non-merge commit touching `fieldlab/`, `infra/gcp/p7/`, or the platform program
  there must append a roadmap note and stage the regenerated
  `Community/roadmap.html` in the same commit, gated by `.githooks` +
  `npm run roadmap:check --staged`. **`networksense`, `comfy-quest`,
  `sovereign-shards`, `isolate`, and `baseline` do NOT carry this ceremony** — none
  of their `AGENTS.md` files mention it, and baseline's own `AGENTS.md` says so
  explicitly ("There is no roadmap-journal ceremony in Baseline"). This is the main
  time-saver of the split: don't invent a journal-note habit in the other four repos.
- **`roadmap.mjs note --kind` is a closed vocabulary the tool doesn't tell you.**
  Valid values (from `Lumberjacks/docs/roadmap/commit-note.schema.json`): `planning`,
  `implementation`, `verification`, `deployment`, `decision`, `rollback`,
  `documentation`. `--milestone` ids must already exist in
  `valheim-volunteer-roadmap.json` — the script joins against it and fails loudly on
  an unknown id, it does not create one for you.
- **PD-4 evidence labeling.** Every technical claim is VERIFIED (reproducible command
  + retained output), INFERRED (reasoned but unconfirmed), or BLOCKED (named missing
  prerequisite) — never asserted bare. Name the gate you ran, not just "tests pass."
- **Landing is one ask, not a relay race** in every repo: "go" / "push" / "land it"
  authorizes commit → pull `--ff-only` → push `main` in one pass. Stop only for
  force-push, history rewrite, deleting someone else's work, or reaching outside the
  repo you're in.
