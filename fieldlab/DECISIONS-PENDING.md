# Decisions pending — netcode-replacement program

The single place to look when batching decisions. Append open items as
`- [ ] <date> — <decision> (source: <link>)`; check off with a link to where it was resolved.
Bounded: touch only lines you created or resolved.

## Open

- [ ] 2026-07-21 — **An uncut dev build is split-brain: which side is wrong?** With no baked
  release id (`ValheimReleaseIdentity.ExpectedModRelease == null`, what every local build gets),
  the handshake **fails open** — `ValheimHandshakeService.cs:546` skips the gate when the expected
  id is empty — while ZDO admission **fails closed**, returning 503 `release_admission_unconfigured`
  for every schema-2 submission (`ValheimZdoRedirectAdmissionPolicy.cs:30`). So a local dev build
  connects cleanly and then has every ZDO rejected. This bites operator-in-the-seat work
  specifically, and costs an hour of confused debugging the first time.
  Both sides are *deliberate*, which is why this is a decision and not a bug fix:
  `ValheimReleaseIdentity.cs:26-31` argues null must disable the gate ("a dev Gateway that refuses
  every join teaches people to switch the flag off and leave it off"), and
  `ValheimZdoIntegrationContractTests.cs:23-24` asserts the 503 on purpose. Changing either means
  deleting a considered decision, so pick one:
  (a) ZDO admission admits on null and marks the receipt unattested, reusing the existing
  `LegacyUnadmitted` semantics — consistent with the handshake, and safe in production because a
  cut release always bakes a real id, so null cannot occur in a promoted image;
  (b) the handshake fails closed on null too — consistent, but dev builds then cannot join at all,
  which is the outcome `ValheimReleaseIdentity` explicitly argues against;
  (c) leave both and document the trap loudly.
  Recommend (a). (source: audit 2026-07-21)
- [ ] 2026-07-10 — **Fold the sibling client-side `WebRequest` POSTs onto the raw-socket helper**
  (telemetry, priority-mirror, apply-profile). Low priority — they run client-side where the
  "URI prefix is not recognized" defect is inert; only required if any ever needs to run
  server-side. (source: [ADR 0003](docs/adr/0003-server-side-mod-http-raw-socket.md))

## Resolved

- [x] 2026-07-21 — **Telemetry heartbeat under sustained load** → **keep the gate strict; separate
  liveness from admission.** The gate's invariant is real — a backlogged primary genuinely is not a
  fully authoritative window — but returning 409 *before* `Record()` meant a correct rejection also
  destroyed unrelated liveness information, freezing the coverage figures that prove the cutover is
  working while the queue counters beside them kept updating live. `RecordAndAdmit` now records then
  gates; the 409 and its conditions are unchanged. Proved by running the new test against the old
  ordering, where it fails. (source: [ADR 0008](docs/adr/0008-liveness-is-not-admission.md))
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
