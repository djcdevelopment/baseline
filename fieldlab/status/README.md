# Program status & live dashboard (retired 2026-07-21)

**This surface is historical, not live.** `program-status.json` covered the P0-P6 /
I0-I7 ladder; the M-series program that followed it lives in
`Lumberjacks/docs/roadmap/valheim-volunteer-roadmap.json` (milestones, gate/proof
state) and `Lumberjacks/docs/plan-m1-strict-admission.md` (active plan + risk
register) — see `fieldlab/plan-baseline-cutover.md` open item 3 for why keeping two
status surfaces in sync stopped working (`program-status.json` sat stale for days
after Stages 1-4 landed, with nothing catching it). Retiring this one rather than
adding a third reconciliation job: **one status surface, the roadmap.**

- **Dashboard (retired, stable URL preserved):** https://claude.ai/code/artifact/1c10f4f8-d747-4411-a400-26d5fb155117
  — now shows a retirement banner and points here instead of live phase/gate state.
- **Historical record:** `program-status.json` — frozen 2026-07-20 (`status` /
  `current_status` fields at the top explain the freeze); `phases`/`trust`/`infra`
  remain an accurate record of P0-P6 and are not being deleted.
- **Renderer:** `../scripts/render-dashboard.py` → `dashboard.html` (deterministic,
  no network) — kept only to reproduce the frozen view; no longer run on a cadence.

## If this ever needs touching again

There is no update protocol going forward — this surface does not track new work.
If a genuine historical correction is needed (a P0-P6 fact was simply wrong, not
"work continued past what's recorded"), edit `program-status.json`, re-run
`python fieldlab/scripts/render-dashboard.py` (full Python312 path on OMEN — PATH
`python` is a Store stub), redeploy `dashboard.html` to the same artifact URL above
(Artifact tool with `url` param), and commit both in the same slice as the
correction.
