# Repo-Split Recovery Handoff

**Written 2026-08-11 ~23:55 PT, mid-flight, in case the driving session dies
(usage limit or otherwise).** If you are a fresh agent picking this up: this
file + the two siblings in this directory are everything you need. Read all
three before touching anything.

- [`PLAN-OF-RECORD.md`](PLAN-OF-RECORD.md) — the operator-approved plan (phases 0–5).
- [`DETAILED-MANIFEST.md`](DETAILED-MANIFEST.md) — file-level move lists, csproj
  line numbers, pressure-test findings (F1–F12), guard designs (G1–G8).

Operator decisions (LOCKED — do not relitigate): baseline becomes the index
repo · Quest gets its own repo (comfy-quest) · shared contracts as NuGet
source packages · history via git-filter-repo with secret scrub.
Model routing per operator: orchestrate/think on the cheapest capable tier,
implement via Sonnet subagents, offload drafts/triage to HEARTH `gcp-gemini`.

---

## State ledger (exact, as of writing)

### Phase 0 — COMPLETE ✅
| Item | Evidence |
|---|---|
| Force-pusher hunt | **No force-pusher exists.** `gh api repos/djcdevelopment/baseline/activity?activity_type=force_push` returns empty; all pushes are the operator's own sessions. BUILDING.md §3's "force-pushes origin/main" claim is stale — fix during Phase 4 doc rewrite. |
| Guide corrected + committed | baseline `49b70861` (root guide + new `docs/PORTS.md`; stray `tests/` duplicate deleted). Port fix :8721→:8730. |
| Tag + archive | tag `pre-split-20260811` pushed; full mirror at `C:\work\_archive\baseline.git`. |
| Stale roots retired | `C:\work\comfy`, `C:\work\Lumberjacks` → `C:\work\_retired\` (gitignored artifacts preserved — never delete). Old paths now fail loudly. |
| GitHub repos created (PRIVATE) | `djcdevelopment/{networksense,lumberjacks-platform,comfy-quest,sovereign-shards}`. Flip public only after Phase 2 gitleaks scrub verification. |
| Tooling | `git-filter-repo` (pip), `gitleaks` 8.30.1 (winget; PATH needs fresh shell). |

### sovereign-shards — CHARTERED + PUSHED ✅
`ec52961` on its main: corrected guide copy, BOUNDARY.md, PORT-CLAIM (:8730),
AGENTS.md, CI no-reach-in guard, `tools/Assert-RepoIdentity.ps1` — verified
passing in-repo AND refusing (exit 1) from a wrong checkout.

### Phase 1 — IN FLIGHT 🟡 (updated 2026-08-12 ~00:20 PT)
- **1.6 script retargets: DONE, committed `9541b78f`** (companion i5 scripts →
  `Lumberjacks/tools/companion/`; p7 lane `-ModArtifact`; headless lab
  `-ModDll` alias; New-WorkbenchZip `-RepoBlobBase`; render_quest_lab
  `--out/--check`. Suites 9/9, 8/8, 14/14 green. Behavior-preserving defaults.)
- **1.1–1.3 contracts surgery: DONE, committed `5077fd75`.** Both packages
  live on the local feed (`artifacts/nuget/` + root `nuget.config`):
  `Comfy.Quest.Contracts` (ModGlue as source-only contentFiles — deliberately
  NOT compiled into its own lib, avoids duplicate-type errors in the test
  project; Companion consumes the compiled assembly via CPM
  `Directory.Packages.props`) and `Comfy.Transport.Contracts` (lib AND
  contentFiles — ProjectReference consumers Game.Contracts/authority-lab take
  the lib, the mod family takes source). No cross-seam Compile-Include remains.
  Gates: xunit 351/351, python 210/210, seam-catalog regen byte-identical,
  mod DLLs **IL-identical** to baseline (byte diff = embedded PDB
  source-document identity only, diagnosed by decompile comparison; hashes in
  the agent report, acceptable per plan). The stray safety stash from the
  mid-run incident was dropped after both commits landed.
- **1.4 test split + 1.5 Studio carve: LAUNCHED as parallel background Sonnet
  agents** at this update. 1.4 scope: `network/mod/ComfyNetworkSense.Tests` →
  new `network/mod/ComfyQuestLab.Tests`, gate = count conservation (combined
  passes = 351). 1.5 scope: `Lumberjacks/src/Quest.Studio` carved from
  Game.Companion via `IQuestStudioHost` adapter + `Comfy.Quest.Studio`
  local package (CPM row needed), gate = route-parity + Game.Companion.Tests
  green (SDK9 at `C:\work\dotnet9\dotnet.exe`). **If you are recovering and
  these never reported:** check `git status --porcelain -- network/mod
  Lumberjacks/src Lumberjacks/tests Lumberjacks/Directory.Packages.props`;
  coherent staged work → verify gates yourself; incoherent → discard only
  those paths back to `5077fd75` and re-run from DETAILED-MANIFEST F3/F4.

### Phases 2–5 — NOT STARTED. Follow PLAN-OF-RECORD in order.

---

## Recovery procedure if the contracts agent died mid-run

1. `git status --porcelain -- network/mod Lumberjacks/src tools/authority-lab nuget.config tools/component-packets/generate_seam_catalog.py tests/`
   Anything staged/modified there is its partial work.
2. Decide: if the ModGlue moves + csproj edits look coherent, verify instead of
   redo — build both mod DLLs (`dotnet build <csproj> -c Release`, host SDK 8
   handles net48; NEVER set `ComfyCopyToPlugins`) and run
   `dotnet test network/mod/ComfyNetworkSense.Tests/...csproj` +
   `python -m unittest discover -s tests`. If incoherent: `git checkout -- .`
   + `git clean -fd network/mod/ComfyQuestContracts/ModGlue artifacts/nuget`
   back to `9541b78f` and re-run 1.1–1.3 from the brief in DETAILED-MANIFEST.
3. Byte-identity baseline: build the two DLLs from the PRE-change tree
   (`git worktree add C:\work\_tmp-base 9541b78f`, build there, hash, remove
   worktree) — do not trust hashes you didn't capture.
4. Only after 1.1–1.3 gates green: run 1.4 and 1.5 (independent of each other,
   disjoint files — parallelizable).

## Phase 1 exit gate (before ANY extraction)
All green: both mod DLL builds byte-checked · ComfyNetworkSense.Tests ·
`python -m unittest discover -s tests` · Game.sln verify (SDK 9: check
`C:\work\dotnet9` or use the `sdk:9.0` container per `Lumberjacks/Dockerfile`;
docker via PowerShell, never git-bash) · `npm run roadmap:test` in Lumberjacks.
Then: append ONE roadmap note covering the Phase-1 landing round
(`cd Lumberjacks; node scripts/roadmap.mjs note --milestone <id> --kind implementation ...`
— closed vocab: kinds are planning/implementation/verification/deployment/
decision/documentation/rollback), commit the jsonl+html together,
`git pull --ff-only`, push, tag **`split-base-20260811`**.

---

## Hazards learned mid-flight (do not relearn these)

1. **Concurrent agents in this one checkout wipe each other's uncommitted
   work.** It happened: the scripts agent's edits (incl. `git mv`s) were
   silently reverted, most likely by the contracts agent taking a clean tree
   for its baseline hash capture. Defense: `git add` immediately after every
   edit; orchestrator commits promptly **with pathspec only** (`git commit -- <paths>`;
   the index is shared mutable state); verify `git show --stat` after.
2. **The permission classifier blocks agent briefs that bundle
   clone-outside-worktree + push.** Do those operations directly from the
   main loop instead (they pass individually); don't try to smuggle them.
3. **Byte-identity gate:** if DLL hashes differ after a contract switch,
   isolate embedded-path metadata (PathMap tuning) vs real IL change. Bounded,
   documented metadata diff = reportable; mystery diff = BLOCKER.
4. **PS 5.1** (`&&` is a parser error; no bulk Get-Content/Set-Content edits —
   corrupts encodings). **Docker via PowerShell** (MSYS mangles `-w /src`).
5. Landing rules: main is an R&D trunk, direct commits normal; stop only for
   force-push/history-rewrite/deleting others' work. Push protection rejects
   credential-lookalike fixtures — rewrite the fixture, never the allow-URL.

## Operator-owned items (blocked on Derek, needed by Phase 3)
- Reserve on nuget.org: `Comfy.Quest.Contracts`, `Comfy.Transport.Contracts`,
  `Comfy.Quest.Studio`.
- Add `NUGET_API_KEY` secret to networksense, lumberjacks-platform, comfy-quest.
- Naming veto window: `lumberjacks-platform` was the default (GitHub name
  `Lumberjacks` is the retired archive). Rename cost is near-zero until
  Phase 2 pushes.
