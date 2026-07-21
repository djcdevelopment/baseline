# Decisions pending — netcode-replacement program

The single place to look when batching decisions. Append open items as
`- [ ] <date> — <decision> (source: <link>)`; check off with a link to where it was resolved.
Bounded: touch only lines you created or resolved.

## Open

- [ ] 2026-07-21 — **Telemetry heartbeat under sustained load.** The gateway rejects a
  `lumberjacks-primary` heartbeat while any queue backlog exists, and staleness trips after 15s —
  so a continuously busy session could show the dashboard stale while the system is healthy. The
  mod-side log-noise fix is queued for the next cut; whether the *gate itself* should tolerate
  load-induced backlog is a design decision, not a patch.
  (source: [retro 2026-07-21](retro/SESSION-RETRO-2026-07-21.md), lesson `L-2026-07-21-2`)

  **Recommendation (2026-07-21, for Derek):** do not loosen the gate. Record liveness *before*
  admission instead — move `service.Record(heartbeat)` in `ValheimTelemetryHeartbeatEndpoints.cs`
  above the `CanAcceptPrimaryHeartbeat` check, keep returning 409. Rationale: the 409 currently
  skips `Record()`, so `_lastSeen` never advances and the 15s staleness clock runs out; the
  coverage numbers that would *prove* the cutover is working freeze at their last accepted values
  and the headline flips to `stale`, while `redirect.Pending` / `consumer.Pending` keep updating
  live off the services — the dashboard contradicts itself. `CutoverSnapshot` recomputes
  `IsAuthoritativeComplete` per request, so recording liveness cannot make it claim completeness;
  it would read "fresh but draining", which is the truth. The same bug was already fixed once,
  narrowly, for the `PeerCount == 0` case — see the comment in `CanAcceptPrimaryHeartbeat`
  ("rejects every heartbeat after a restart and makes the dashboard stale until a player joins").
  This generalizes that fix rather than inventing a new policy. Client-side risk is nil: the mod's
  `LumberjacksTelemetryHeartbeatRunner.Post` is fire-and-forget and only logs on throw, so the 409
  changes no mod behavior. Smallest proof: a heartbeat with `consumer.Pending = 5` gets 409, and
  `GET /api/v0/telemetry/cutover` then returns `stale = false` with the live pending count.

- [ ] 2026-07-10 — **Fold the sibling client-side `WebRequest` POSTs onto the raw-socket helper**
  (telemetry, priority-mirror, apply-profile). Low priority — they run client-side where the
  "URI prefix is not recognized" defect is inert; only required if any ever needs to run
  server-side. (source: [ADR 0003](docs/adr/0003-server-side-mod-http-raw-socket.md))

## Resolved

- [x] 2026-07-21 — **Stop the P7 VM, or leave it running?** → **leave it running**, per Derek.
- [x] 2026-07-21 — **Fix release reproducibility, or accept it permanently?** → **accept it, in
  operator-in-the-seat mode**, per Derek: "accept unreproducibility when I'm in the seat driving
  and testing; that heavy read tape was for when I left Codex to build for 12 hours by itself."
  The resolution is a *mode distinction*, not a permanent acceptance — the provenance tape is an
  **independent-agent guardrail**, not an operator dev/testing requirement. Neither remedy from
  ADR 0005 is adopted now; both stay on the shelf and either may be switched on when unattended
  agent builds resume. Recorded as an amendment to
  [ADR 0005](docs/adr/0005-carry-forward-unreproducible-artifacts.md).
- [x] 2026-07-21 — **Give the P7 VM a deploy key, or keep it credential-free?** → **keep it
  credential-free for now**, per Derek ("unattended for now"): no secret at rest, updates keep
  arriving as pushed git bundles or OCI archives, and no unattended update path is opened. Revisit
  together with the independent-agent-guardrails mode above, since that is the mode that would
  actually need one. (source: [ADR 0006](docs/adr/0006-git-bundle-transport-no-vm-credentials.md))
- [x] 2026-07-21 — **Strict roster posture for future acceptance windows** → **leave it disarmed**,
  per Derek: the two-account roster path is proven beyond reasonable doubt and well documented, so
  re-arming it per window buys no new information and can only block a join. Do not make it a
  standard acceptance step; effort goes to what is not yet solved.
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
