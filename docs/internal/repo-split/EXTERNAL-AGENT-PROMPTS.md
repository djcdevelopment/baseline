# External-Agent Prompt Pack — Repo Split Phases 2–5

**For the operator:** paste one prompt per agent session on the external
service. Run them **in order** — each names its preconditions and start
directory. Every prompt ends with the same reporting contract: the agent
writes `docs/internal/repo-split/reports/<NN>-<name>.md` in the **baseline**
repo and commits ONLY that file (`git commit -- docs/internal/repo-split/reports`).
The validating session (Claude, low remaining capacity) reads reports + spot-runs
gates; it does not re-execute.

**Shared rules for every prompt below (paste them along with the prompt):**

> RULES: You are working in a real repo fleet on this machine.
> (1) Read C:\work\baseline\docs\internal\repo-split\{HANDOFF-RECOVERY,PLAN-OF-RECORD,DETAILED-MANIFEST}.md before acting.
> (2) NEVER run git stash / git checkout -- . / git restore / git reset / git clean in C:\work\baseline — other work may be uncommitted there.
> (3) Commit only with explicit pathspecs (git commit -- <paths>), never bare `git commit -a`.
> (4) Windows PowerShell 5.1: no `&&`, no ternary; never bulk-edit files with Get-Content/Set-Content pipelines. Run docker from PowerShell, not git-bash.
> (5) GitHub push protection rejects credential-lookalike fixtures: fix by REWRITING the fixture content, never via the allow-this-secret URL.
> (6) Label every claim in your report VERIFIED (command + output), INFERRED, or BLOCKED. Never force a green.
> (7) End your run by writing your report file and committing it (rule 3). If you are blocked, the report says exactly where and why.

---

## P1 / P2 / P3 — Extract a sovereign repo (one prompt template, run 3×)

**Precondition:** baseline tag `split-base-20260811` exists (`git -C C:\work\baseline tag -l split-base-*`). If missing, STOP and report — Phase 1 has not gated.
**Start directory:** `C:\work`
**Run once per parameter block below (P1 networksense, P2 lumberjacks-platform, P3 comfy-quest).**

> TASK: Extract the sovereign repo **{{REPO}}** from baseline with history.
>
> 1. Fresh mirror-based working clone: `git clone C:\work\baseline C:\work\_extract\{{REPO}}` (full clone, not the live checkout).
> 2. In the clone, run `git filter-repo` with `--path` include flags for exactly the INCLUDE list in your parameter block (paths preserved, no renames). Where the block names EXCLUDE paths, run a second `git filter-repo --invert-paths` pass for them. For lumberjacks-platform also apply `--strip-blobs-bigger-than 5M` AFTER confirming the include set (the oldimages purge; record dropped blobs from the filter-repo report).
> 3. Scrub: run `gitleaks git .` over the FULL filtered history. For every finding decide: real credential (STOP, report), or fixture (rewrite via `git filter-repo --replace-text` mapping). Re-run gitleaks until clean. Record findings + dispositions.
> 4. Scaffold (new files, commit normally): PROVENANCE.md ("extracted from baseline@split-base-20260811", the exact filter-repo invocations, dropped-blob list, gitleaks disposition summary, commit-map file committed under docs/provenance/); AGENTS.md + BOUNDARY.md instantiated from C:\work\baseline\docs\internal\repo-split\CHARTER-TEMPLATES.md filled with the parameter block's OWNS/DOES-NOT-OWN/ARTIFACTS; tools/Assert-RepoIdentity.ps1 modeled on C:\work\sovereign-shards\tools\Assert-RepoIdentity.ps1 with expected='djcdevelopment/{{REPO}}'; .github/workflows/ci.yml modeled on C:\work\sovereign-shards\.github\workflows\ci.yml (no-reach-in grep for 'C:\\work\\' and '../../..' + identity job) PLUS the build/test job from your parameter block; LICENSE + SECURITY.md copied from baseline root.
> 5. Interim package feed: create `packages-local/` in the new repo, copy `C:\work\baseline\artifacts\nuget\*.nupkg` into it, add a repo-root `nuget.config` with packages-local first then nuget.org. (Phase 3 replaces this with real NuGet.org pins and deletes the vendored nupkgs.)
> 6. Gates from the parameter block — all must be VERIFIED.
> 7. `git remote add origin https://github.com/djcdevelopment/{{REPO}}.git`, push main. The repo stays PRIVATE.
> 8. Move the verified clone to its working home `C:\work\{{REPO}}` (leave no copy in C:\work\_extract).
> 9. Write + commit the report per the shared contract (report also lists the final `git log --oneline -5` of the new repo).

**P1 parameter block — networksense**
- INCLUDE: `network/` `tools/i5` `tools/am4` `tools/modpack` `tools/synthetic-baseline-extractor`
- EXCLUDE (second pass): `network/mcp` `network/mod/ComfyQuestLab` `network/mod/ComfyQuestRuntime` `network/mod/ComfyQuestContracts` `network/mod/ComfyQuestLab.Tests`
- OWNS: client telemetry mod, HUD, Owner Score, mod deploy lanes (i5/am4/modpack). DOES NOT OWN: transport server+contracts (lumberjacks-platform), quest product (comfy-quest), Dev MCP (isolate), index (baseline).
- ARTIFACTS: publishes mod DLL releases (mod-v* tags, sha256 manifest); consumes Comfy.Quest.Contracts + Comfy.Transport.Contracts (packages-local until Phase 3).
- GATES: `dotnet build network/mod/ComfyNetworkSense/ComfyNetworkSense.csproj -c Release` (host SDK 8 is fine; never set ComfyCopyToPlugins) · `dotnet test network/mod/ComfyNetworkSense.Tests` = **166 passed** · gitleaks clean · Assert-RepoIdentity passes in-repo.

**P2 parameter block — lumberjacks-platform**
- INCLUDE: `Lumberjacks/` `infra/gcp/p7` `fieldlab/scripts` `fieldlab/autonomous` `fieldlab/docs` `fieldlab/NETCODE-MAP.md` `fieldlab/PORTAL-LIFECYCLE-MAP.md` `fieldlab/plan-native-network-final-cutover.md` `tools/p7` `tools/wave0` `tools/workbench` `tools/authority-lab` `tools/guest-package` `.githooks` `tests/test_powershell_param_contracts.py` `tests/test_guest_package.py` `tests/fixtures`
- EXCLUDE (second pass): `Lumberjacks/oldimages` `Lumberjacks/network/mcp`
- Also: `--strip-blobs-bigger-than 5M`. NOTE the two py tests need a tests/__init__.py — create one if the filter didn't carry it.
- OWNS: net9 gateway/services/companion, transport contracts package, p7 infra, fieldlab live harness, roadmap journal + ceremony (its pre-commit hook works unchanged — set `git config core.hooksPath .githooks` and record it in AGENTS.md). DOES NOT OWN: the mod (networksense), quest product (comfy-quest), evidence archive (baseline).
- ARTIFACTS: publishes Comfy.Transport.Contracts (Phase 3), gateway images, roadmap.html; consumes mod DLL releases + Comfy.Quest.Contracts/Studio.
- GATES: `C:\work\dotnet9\dotnet.exe build Lumberjacks/Game.sln -c Release` clean (if SDK9 host build fails on container-only assumptions, use the Dockerfile verify stage and say so) · `cd Lumberjacks; npm ci; npm run roadmap:test` green · `python -m unittest discover -s tests` green for the carried tests · gitleaks clean · identity guard.

**P3 parameter block — comfy-quest**
- INCLUDE: `network/mod/ComfyQuestLab` `network/mod/ComfyQuestRuntime` `network/mod/ComfyQuestContracts` `network/mod/ComfyQuestLab.Tests` `Lumberjacks/src/Quest.Studio` `tools/component-packets` `tools/questlab-doctor` `tools/questlab-events` `tools/questlab-grimoire` `tools/questlab-pacing` `tools/questlab-sheets` `tools/quest-packs` `tools/quest-bridge` `tools/quest-runtime` `tools/blueprints` `recipes/quest-catalogs` and the 17 quest test files `tests/test_quest*.py` `tests/test_questlab*.py` `tests/test_i5_questlab_batch.py` `tests/test_gallery_profiles.py` `tests/test_fallingwater_blueprint.py` `tests/test_verify_questlab_release.py` `tests/test_verify_questlab_truth.py` plus `tests/fixtures` `tests/__init__.py` (enumerate the actual tests/ dir against DETAILED-MANIFEST before filtering; report the final list).
- EXCLUDE: none beyond the include scoping.
- OWNS: quest product (Lab/Runtime/Contracts/Studio), quest tooling + generators, questlab.html artifact. DOES NOT OWN: hosting Companion (lumberjacks-platform), telemetry mod (networksense).
- ARTIFACTS: publishes Comfy.Quest.Contracts + Comfy.Quest.Studio (Phase 3), questlab.html + workbench zips (hash-recorded); consumes Comfy.Transport.Contracts? (NO — verify: quest mods must not reference it; report if they do).
- GATES: `dotnet build network/mod/ComfyQuestLab/ComfyQuestLab.csproj -c Release` · `dotnet test network/mod/ComfyQuestLab.Tests` = **185 passed** · `python -m unittest discover -s tests` green for the carried set · `python tools/component-packets/render_quest_lab.py --check --out <temp>` runs · gitleaks clean · identity guard.

---

## P4 — Phase 3: publish + repin (AFTER P1–P3 and after the operator reserves NuGet IDs + adds NUGET_API_KEY secrets)

**Start directory:** `C:\work\lumberjacks-platform` (then comfy-quest, then consumers)

> TASK: Wire real package publishing and repin consumers. Read PLAN-OF-RECORD Phase 3.
> 1. In lumberjacks-platform: add `.github/workflows/publish-nuget.yml` — on tag `nuget-v*`, pack `Lumberjacks/src/Comfy.Transport.Contracts` and `dotnet nuget push` to NuGet.org with the NUGET_API_KEY secret. Version from the tag. Same in comfy-quest for Comfy.Quest.Contracts + Comfy.Quest.Studio.
> 2. Tag `nuget-v0.1.0` in each producing repo; verify the workflow publishes (or report the exact failure).
> 3. In every consuming repo (networksense, lumberjacks-platform, comfy-quest): switch nuget.config to nuget.org (drop packages-local + delete the vendored nupkgs), pin exact versions 0.1.0, restore + full build/test gates from that repo's ci.yml. THIS IS THE ROLLBACK COMMITMENT POINT — record in each report that rollback is now "repin version" not "revert to baseline".
> 4. networksense: add `.github/workflows/release-mod.yml` — on tag `mod-v*`, build Release DLL, emit manifest.json + sha256, attach as GitHub Release assets. Cut `mod-v0.5.46-split-proof` and verify `infra/gcp/p7/scripts/New-ReleaseCut.ps1 -ModArtifact <downloaded dll>` in lumberjacks-platform hash-verifies it (p7 smoke, no deploy).
> 5. Report per the shared contract.

---

## P5 — Phase 4: slim baseline into the index repo (AFTER P1–P3 verified; P4 not required)

**Start directory:** `C:\work\baseline`

> TASK: Execute PLAN-OF-RECORD Phase 4 exactly. Summary: `git rm -r` the moved trees (network/mod quest+sense projects, network/ tooling that left, Lumberjacks/, infra/gcp/p7, fieldlab live-harness paths, the moved tools/* dirs, moved tests) — ordinary commits, NEVER rewrite baseline history; keep the evidence/index surfaces (fieldlab evidence+retros, docs/, data/, site/, corpus/, handoffs/, plans/, remaining tools). Write REPO-MAP.md at root (surface → repo → path → artifact contract → owning guard, covering all 5 repos + isolate). Rewrite README.md doors + docs/internal/START-HERE.md + GLOSSARY.md for the fleet. Write docs/decisions/pd-9-repository-split.md (rationale from PLAN-OF-RECORD Context; ownership answers: production compose + env templates → lumberjacks-platform) and amend pd-8 (isolate has a remote; network/mcp reconciliation). Corpus: create corpus/mirrors/lumberjacks/{workbench.json,commit-notes.jsonl} snapshots + provenance.json, repoint corpus/sources.json, drop Lumberjacks/** triggers from .github/workflows/pages.yml, verify `python tools/corpus/build.py --check` green. Reconcile network/mcp with C:\work\isolate (diff, port anything newer in baseline, then git rm network/mcp; record in the PD-8 amendment). Remove .githooks (ceremony lives in lumberjacks-platform now) and fix BUILDING.md's stale force-push claim. Gates: `python -m unittest discover -s tests` green on the remaining set · `python tools/corpus/build.py --check` · `python -m unittest tests.test_entrypoint_links` green after the README rewrite. Commit in coherent chunks with pathspecs; push. Report per the shared contract.

---

## P6 — Phase 5: verification matrix + guards (LAST)

**Start directory:** `C:\work`

> TASK: Execute PLAN-OF-RECORD Phase 5. In each of the 5 repos, confirm the ci.yml gates run green locally and add the missing named guards G1–G8 from DETAILED-MANIFEST (each with a commented-out bad fixture proving it CAN fail — actually flip each fixture on once, observe the failure, flip it off, record both outputs). Run integration lanes I1 (mod artifact → p7 hash gate), I3 (questlab.html render → hash verify), I4 (corpus mirror → pages build), I5 (headless lab boot with released DLL, if a Valheim environment is available — else mark BLOCKED with what's missing). I2 (Studio publish → Runtime load on OMEN) needs the operator's game client — write the exact manual steps for them instead of running it. Report per the shared contract, one section per repo.

---

## Validation contract (what the low-capacity session does with each report)

Reads the report; spot-runs at most: one build, one test suite, `git log` shape,
gitleaks summary line. Flags discrepancies; never re-executes the whole task.
