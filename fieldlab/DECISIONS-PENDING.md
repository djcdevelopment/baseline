# Decisions pending — netcode-replacement program

The single place to look when batching decisions. Append open items as
`- [ ] <date> — <decision> (source: <link>)`; check off with a link to where it was resolved.
Bounded: touch only lines you created or resolved.

## Open

- [ ] 2026-07-21 — **Stop the P7 VM, or leave it running?** It was started for the step-6
  re-provision and is still up and billing. Deferred by Derek ("we'll get back to the VM
  shortly"). (source: [retro 2026-07-21](retro/SESSION-RETRO-2026-07-21.md))
- [ ] 2026-07-21 — **Fix release reproducibility, or accept it permanently?** Two known remedies,
  neither chosen: pin `EnableSourceControlManagerQueries=false` in the csproj (hash becomes a
  function of source alone, loses embedded provenance), or reorder cuts to
  commit-first-build-second (keeps provenance; rebuild then needs the same origin URL). Until one
  is chosen, mod artifacts are auditable only by hash continuity, not by rebuild.
  (source: [ADR 0005](docs/adr/0005-carry-forward-unreproducible-artifacts.md))
- [ ] 2026-07-21 — **Give the P7 VM a deploy key, or keep it credential-free?** Today every update
  reaches it as a git bundle or an OCI archive pushed from a workstation. That is deliberate (no
  secret at rest) but rules out any unattended update path.
  (source: [ADR 0006](docs/adr/0006-git-bundle-transport-no-vm-credentials.md))
- [ ] 2026-07-21 — **Telemetry heartbeat under sustained load.** The gateway rejects a
  `lumberjacks-primary` heartbeat while any queue backlog exists, and staleness trips after 15s —
  so a continuously busy session could show the dashboard stale while the system is healthy. The
  mod-side log-noise fix is queued for the next cut; whether the *gate itself* should tolerate
  load-induced backlog is a design decision, not a patch.
  (source: [retro 2026-07-21](retro/SESSION-RETRO-2026-07-21.md), lesson `L-2026-07-21-2`)
- [ ] 2026-07-21 — **Strict roster posture for future acceptance windows.** It is in-memory only
  and every container recreate disarms it; it was left disarmed for the step-6 world test so it
  could not block the join. Decide whether acceptance runs should re-arm it via
  `POST /valheim/handshake/config` as a standard step.
  (source: `Lumberjacks/docs/roadmap/m5-v3-acceptance-receipt.json`)
- [ ] 2026-07-10 — **Fold the sibling client-side `WebRequest` POSTs onto the raw-socket helper**
  (telemetry, priority-mirror, apply-profile). Low priority — they run client-side where the
  "URI prefix is not recognized" defect is inert; only required if any ever needs to run
  server-side. (source: [ADR 0003](docs/adr/0003-server-side-mod-http-raw-socket.md))

## Resolved

- [x] 2026-07-12 — **2nd I3 repeatability window** → satisfied inside the P7 composition: window
  `i7-w6` re-proved I3 redirect `receipts_match_no_loss` (3474 == 3474, 0 loss/dup) on a fresh clean
  GCP window, alongside the other three rungs. (source: `evidence/i7-w6/gate-summary.json`)
- [x] 2026-07-12 — **P7/I7 close: one vs two live windows** → one fresh clean window (`i7-w6`) +
  retro-archive of the corroborating partial `i7-gcp-w1`; the two independent windows satisfy
  repeatability with a single human touchpoint. (source: `retro/SESSION-RETRO-2026-07-12.md`,
  lesson `L-2026-07-12-5`)
- [x] 2026-07-10 — **Disarm the pin after the I2 gate** → yes; disarmed on am4
  (`ownershipPinEnabled=false`, commit `1f337c7`), back to observe-only baseline for P4.
- [x] 2026-07-10 — **I2 repeatability:** do one more clean join → **yes** (Derek's blessing,
  evening session): window A of the P4 gate session. Pin re-armed + save-integrity snapshot
  taken + server restarted (staged via `scripts/run-redirect-window.ps1 -Stage arm-pin`);
  **execution pending the join** — the gate itself is not marked until its artifact exists.
- [x] 2026-07-10 — **Idle-restart vs timed gates:** practice adopted = the arm stage restarts
  the container itself and the join follows immediately, so the 150s window sits at the start
  of a fresh ~30-min `UPDATE_IF_IDLE` cycle (encoded in `run-redirect-window.ps1`; the arm
  output says JOIN NOW). Revisit only if a window clips again.
- [x] 2026-07-10 — **Next phase:** **P4** with window A (I2 repeat) folded into the same game
  session, per Derek (two-window shape confirmed via AskUserQuestion, then blessed). Headless
  runway complete + committed (`ed18c55`, `5d088e9`; Lumberjacks `129677f`); one launch + two
  joins runs the gates. Note: window A runs on 0.5.11 (pin code carried unchanged from 0.5.10;
  redirect flag off/inert) — mechanism-across-builds repeatability, recorded honestly.
