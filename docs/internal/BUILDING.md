# Building and verifying Baseline

Contributor-facing build/verify truth, consolidated out of `AGENTS.md`,
`HANDOFF-2026-07-29.md`, and `Lumberjacks/docs/build-release-runbook.md`.
Read in order — it's the order you'll hit these.

## 1. Two build environments — using the wrong one fails confusingly

### Lumberjacks services (net9) — build INSIDE a container

`Lumberjacks/Dockerfile` targets `mcr.microsoft.com/dotnet/sdk:9.0`. The host
here only has SDK 8, so a host `dotnet build`/`dotnet test` is **not** the
release check — it fails with `NETSDK1045` before the real build is reached.

From `Lumberjacks/`:

```powershell
.\scripts\build.ps1 -Target Verify
```

That wraps `docker build --target verify -t lumberjacks-build:verify .`
(restore, build, tests, all inside the container). For an ad hoc test run,
the repo also uses `docker run` directly:

```bash
docker run --rm -v "${PWD}:/src" -w /src mcr.microsoft.com/dotnet/sdk:9.0 \
  dotnet test Game.sln --filter "Category!=Performance"
```

Full release-cut / image-promotion steps live in
[`Lumberjacks/docs/build-release-runbook.md`](../../Lumberjacks/docs/build-release-runbook.md).

### The mod (net48) — builds in the Docker Workbench image

`network/mod/ComfyNetworkSense` targets `net48`. The supported and historical
workaround is the Docker Workbench image, which supplies the reference
assemblies while mounting the Valheim installation read-only. A host SDK
failure such as MSB3644 is an expected boundary; do not add a second host
build lane. The project also has a post-build step that can copy the built DLL
straight into `$(ValheimDir)\BepInEx\plugins`, so the canonical Workbench build
disables that copy.

Use the Workbench capability/receipt (`build.mod.release`) rather than a raw
host build. For a deliberate local diagnostic outside the Workbench, redirect
the output path somewhere that does not exist so the copy step no-ops — this is
the literal value `infra/gcp/p7/scripts/New-ReleaseCut.ps1` uses:

```powershell
cd network\mod\ComfyNetworkSense
dotnet build .\ComfyNetworkSense.csproj -c Release `
  -p:PluginOutputPath=C:\__comfy_cut_no_plugin_copy__
```

## 2. The commit ceremony — every non-merge commit

From `Lumberjacks/`:

1. `npm run roadmap:note -- --milestone <M> --kind <kind> --author <you> --summary "..." --impact "..."`
2. Stage the change **and always**: `docs/roadmap/commit-notes.jsonl`,
   `docs/roadmap/valheim-volunteer-roadmap.json` (if milestone truth changed),
   and the regenerated `src/Game.Gateway/Community/roadmap.html`.
3. `npm run roadmap:check -- --staged` — must pass before you commit.

That check includes a licensing-phrase lint: it **fails any new note or JSON
edit containing "open source"** (this project is BSL 1.1, not OSI-approved).
Write **"public source (BSL 1.1)"** instead. Full rule:
[`Lumberjacks/AGENTS.md`](../../Lumberjacks/AGENTS.md) and
[`Lumberjacks/docs/roadmap/README.md`](../../Lumberjacks/docs/roadmap/README.md).

Workbench catalog page edits follow the same shape, different commands: edit
`Lumberjacks/docs/workbench/workbench.json` only, then
`npm run workbench:render` and `npm run workbench:check`. **Never hand-edit**
a generated HTML file (`roadmap.html`, `workbench.html`).

The workbench render is **two-phase** since 2026-07-29: commit the inputs
(`workbench.json` + `scripts/workbench.mjs`) first, then render — a clean
tree stamps `Published from <sha7>` naming that commit — then commit the
regenerated HTML. A dirty-tree render stamps an unpublishable
`Preview rendered …` line, and `workbench:check` fails a clean tree whose
artifact still carries one. Guard tests: `npm run workbench:test`. Live
destinations (Discord invite/threads, GitHub URLs, site routes, downloads):
`npm run workbench:verify-live -- --pre-publish` — run automatically as a
publish gate by `tools/workbench/Publish-WorkbenchAssets.ps1`.

## 3. `main` has no long-lived branches

Background automation auto-commits and **force-pushes `origin/main`** for any
change touching the Gateway, `network/`, or `infra/gcp/p7/` — see "This
journal runs as background automation" in [`AGENTS.md`](../../AGENTS.md). Don't
rely on a stable base SHA or a long-lived feature branch: pull/rebase before
you start, and never force-push to "undo" what the automation did.

## 4. Community catalog zips go through one script

Any zip published to the `/workbench` catalog is built only via
`tools/workbench/New-WorkbenchZip.ps1`, which runs
`Test-WorkbenchZipPrivacy.ps1` as a **mandatory** gate before producing the
zip — there is no path that skips the scanner.

## 5. PowerShell 5.1 encoding trap

Never bulk-edit a file via `Get-Content`/`Set-Content` round-trips in Windows
PowerShell 5.1 — it silently corrupts UTF-8 content. Use a targeted editor or
line-level tool instead.
