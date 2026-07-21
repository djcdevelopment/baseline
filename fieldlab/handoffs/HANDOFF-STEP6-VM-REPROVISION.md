# Handoff prompt — VM re-provision + world-test (paste into a fresh session opened in `C:\work\baseline`)

> Snapshot as of 2026-07-21, right after §5 steps 1–5 of the cutover landed. Regenerate if it goes stale.
> **Open this session in `C:\work\baseline`, not `C:\work\comfy`.** That's a new memory/project scope —
> nothing from prior comfy-rooted sessions carries over automatically. This file plus the docs it
> points at are the standalone context; don't assume anything else is remembered.

---

We're continuing the **comfy + Lumberjacks monorepo cutover**. `baseline`
(https://github.com/djcdevelopment/baseline) now exists: comfy's history landed unmodified at repo
root, Lumberjacks' full history landed under `Lumberjacks/` via `git subtree`. Orient from
`fieldlab/plan-baseline-cutover.md` (the original audit + cutover plan) and the living roadmap
(https://claude.ai/code/artifact/3b391578-5333-4f3a-84c8-db36ea4b1a8e, or `Lumberjacks/docs/roadmap/`)
for current milestone state. The retired I0–I7 dashboard
(https://claude.ai/code/artifact/1c10f4f8-d747-4411-a400-26d5fb155117) is history only — don't treat it
as current.

**Where we are.** §5 steps 1–5 are done, verified, and pushed (`origin/main` clean, 0 ahead/behind):
trees landed with history preserved, ~30 cross-repo hardcoded paths fixed, release manifest schema
collapsed to v3 (one `source.baseline_commit`), the release gate extended from `gateway` alone to all
five P7 services (`eventlog`/`progression`/`operatorapi` now pinned by image digest too, no admission
check — they have nothing to admit), `program-status.json` retired to a historical record. Verified:
`roadmap:check` passes, Gateway tests 157/159 (2 known pre-existing Windows-path failures, not ours),
mod + all four Lumberjacks Docker targets build clean, a full v3 manifest built from real artifacts
round-tripped through `build-release-bundle.ps1`/`validate-release-bundle.ps1` end to end.

**What's NOT done — this session's job:** step 6, the plan's actual completion criterion —
*re-provision `comfy-lumberjacks-p7` from `baseline` and confirm it reproduces what was world-tested
in `m5-recipients-20260720-r1`* (mod `035faa8793114c75…`, gateway image `sha256:69e025e8c13b…`,
manifest `Lumberjacks/docs/roadmap/m5-recipients-build-candidate.json`). The VM is currently **STOPPED**
(`comfy-lumberjacks-p7`, project `lumberjacks-exp-20260711-djc`, `us-west1-b`, `n2-highmem-2` — that's
a deliberate cost downsize from `n2-highmem-8`, don't flag it as a problem). Everything proven so far
was session state — hand-copied image, hand-copied mod, compose file copied, strict roster armed by an
HTTP call. None of it survives a rebuild. This is the test that proves the cutover actually worked.

**Gotchas from this session that aren't written anywhere else — read before touching the VM:**
- `infra/gcp/p7/environment.example` now needs **three more required vars**
  (`LUMBERJACKS_EVENTLOG_IMAGE`/`_PROGRESSION_IMAGE`/`_OPERATORAPI_IMAGE`) beyond what the *live* VM's
  `/etc/comfy-p7/environment` currently has — that file predates this cutover's gate extension. Compose
  will refuse to start until it's updated with real promoted image refs for all three.
- **How do the four non-gateway... now five images actually reach the VM?** Gateway's image transport
  path (build → tag → get onto the VM) predates this session; the same mechanism needs extending to
  `eventlog`/`progression`/`operatorapi`, and I never verified what that mechanism is end-to-end
  (registry push? `docker save`+`scp`+`docker load`, like `build-release-bundle.ps1`'s bundle?). Check
  `deploy-gateway.ps1` and `PROMOTION-DRILL.md`'s cold-start phase for the existing pattern before
  inventing a new one.
- `New-GatewayReleaseCut.ps1` (the narrow "gateway image only, mod frozen" tool) was **deliberately not
  extended** to build the other three images — doing so would contradict its reason to exist. A
  Gateway-only cut still needs real image refs for the other three in its bundle; reuse whatever's
  already promoted rather than rebuilding them.
- `Lumberjacks/scripts/roadmap.mjs`'s `checkStaged()` assumes Lumberjacks is the repo root and now
  fails on a correctly-staged commit (path-relativity mismatch). Plain `roadmap:check` (no `--staged`)
  still works — use that.
- `infra/gcp/p7/README.md` and a few other docs still write commands against `C:\work\comfy\...` —
  that's now stale (the checkout is `C:\work\baseline`), left alone on purpose since fixing comfy's own
  self-references was out of scope for the cutover. Substitute mentally, or fix them if you're already
  touching the file.

**Standing rules for this program:**
- This is live, paid, shared GCP infrastructure. Confirm the re-provision plan with Derek before
  starting the VM, deploying, or restarting services — don't just execute because the plan doc says to.
- **KVM-elimination guardrail**: drive verification through MCP tools, not hand-typed console commands
  or eyeballing a screen.
- **IAP SSH must run in the foreground** — backgrounded, the payload runs and the output is lost.
- The world-test half of this needs **Derek actually in the seat** — launching Valheim, joining,
  playing the acceptance route from `infra/gcp/p7/README.md` §7–9. Get the VM/deploy/config side fully
  proven and ready first so that join is the only thing he has to do.

Confirm the re-provision plan with Derek before touching the VM, then go.
