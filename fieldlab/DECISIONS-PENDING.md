# Decisions pending — netcode-replacement program

> **2026-08-01 provenance correction and resolution:** the old resolved gateway
> note below is historical, not current workstation truth. The stale
> `ComfyGatewayBoot` task was disabled without deletion and its retired
> `C:\work\comfy` listener was stopped; active Baseline Dev/Lab launchers/config
> use explicit `:8721`. See the canonical
> [MCP endpoint provenance audit](../docs/audit/2026-08-01-mcp-endpoint-provenance-audit.md)
> and root [decision queue](../DECISIONS-PENDING.md). Do not promote `:8720`
> receipts or treat the retired task as Baseline evidence.

The single place to look when batching decisions. Append open items as
`- [ ] <date> — <decision> (source: <link>)`; check off with a link to where it was resolved.
Bounded: touch only lines you created or resolved.

## Open

- [ ] 2026-08-05 — **When to spend the r42 Gateway fix cut and the next P7 window.** The
  session-plane fix plan is landed (five fixes + enrollment addendum); implementing it invalidates
  the promoted r41 pair, so the cost is a coupled pair cut, re-promotion, a fresh boot receipt, and
  candidate 12 — plus the local wedge repro (harness throttle) that should reproduce the redelivery
  stall on AM4 *before* GCP spend. (source: [fix plan](evidence/p7-gateway-session-plane-fix-plan-20260805.md), [SESSION-RETRO-2026-08-05](retro/SESSION-RETRO-2026-08-05.md))

- [ ] 2026-08-05 — **Ratify the enrollment-lane proof as the alpha gate (ADR 0017), and pick the
  alpha posture.** Proposed: alpha runs on a fallback-capable candidate with the mod-zip→visible-world
  proof as the gate; the permanent no-fallback final cuts only after alpha traffic survives. Needs
  Derek's yes, and the client-harness enrollment support it implies. (source: [ADR 0017](docs/adr/0017-prove-the-lane-users-ship-on.md))

- [ ] 2026-08-05 — **Restore `zdoRedirectEnabled=true` on P7 before the next armed window.** The
  server was left in native play mode; the armed config is
  `djcdevelopment.valheim.comfynetworksense.cfg.bak-20260805T1020Z` beside the live cfg on the VM.
  A candidate run against a native-mode server would be measuring the wrong lane — restore first.
  (source: [fix plan addendum](evidence/p7-gateway-session-plane-fix-plan-20260805.md))

- [~] 2026-07-22 — **PINNED 2026-07-28** (networking-lane hard hold — see
  [PINNED-networking-lane-2026-07.md](PINNED-networking-lane-2026-07.md); return here on re-open):
  **Re-confirm the co-presence ownership bug actually reproduces before deploying/arming
  the fan-out.** The 2026-07-22 live test showed the "empty world" was an autoport config boolean, not
  single-recipient starvation; delivery reached both consumers. The fan-out (`c8db19d`) is built + green
  in tests but may fix a case that isn't triggering. Test: two clients, *both* default configs (autoport
  off), stand in one base — does the 2nd still see empty? (source: [SESSION-RETRO-2026-07-22](retro/SESSION-RETRO-2026-07-22.md), [ADR 0013 reality check](docs/adr/0013-ownership-visibility-split.md))

- [ ] 2026-07-21 — **Restore the pruned quest slice as a `QuestTriggerEvaluator` consuming the gameplay
  events** (Increment 4+). Client-side trigger + local-player attribution from the comfy backup
  (`djcdevelopment/comfy`, `handoffs/comfy-control-surface/`), dropping the screenshot/outbox coupling
  in favour of the RPC→gateway seam. (source: [ADR 0012](docs/adr/0012-gameplay-telemetry-is-client-side.md), plan increment 4)

- [ ] 2026-07-21 — **Area co-presence: adopt the ownership/visibility split (ADR 0013).** The live
  two-human test proved the queue is multi-tenant but co-located players can't share buildings/portals
  — visibility is expressed by moving the single `recipient` stamp + Valheim ownership. ADR 0013
  adopts per-observer fan-out onto the existing durable queue (evolve, don't rewrite).
  **Status:** gateway substrate proven headless (`8f92edf`, N=2/10 isolation + WAL replay + dedup);
  **Phase 0 shadow + Phase 2 fan-out BUILT** (uncommitted, flag-gated default-off, mod builds clean +
  70 mod / gateway tests green), awaiting the **live two-human test**
  ([runbook](docs/runbook-copresence-fanout-live-test.md)). Phase 1 proved a no-op (runner already
  emits per-peer). **Remaining Derek-facing calls:** (a) after the live test, the per-recipient-seq fix
  to restore `complete=True` under multiple recipients (pre-existing global-seq artifact, not fan-out);
  (b) fan-out vs region-shared partitions (deferred to Phase 4, only against measured WAL amplification).
  (source: [ADR 0013](docs/adr/0013-ownership-visibility-split.md), [findings](FINDINGS-multiplayer-copresence-2026-07-21.md))

- [ ] 2026-07-30 — **What is P7 still for, and does it come back?** This session narrowed the
  answer to **exactly one thing: the Valheim UDP world** (2456-2457). The community surface is
  already live and green on AM4 behind the Tailscale Funnel (`verify-live` PASS, 69/0/0), and
  Funnel is TCP/HTTPS-only so the dedicated server cannot ride it — that, and only that, is what
  still needs a cloud VM. Demos no longer need it either (see [[demo-streaming-sunshine-moonlight]]).
  The open call is whether P7 returns as a booked play/UAT window, gets replaced for the world role,
  or stays down; the boot fixes below only matter under the first two.
  (source: [SESSION-RETRO-2026-07-30](retro/SESSION-RETRO-2026-07-30.md), [ADR 0014](docs/adr/0014-boot-must-converge-or-say-so.md))

- [ ] 2026-07-30 — **When to spend a cold stop/start proving the P7 boot fixes, and how to land the
  half that needs terraform?** The boot work is committed but **UNVERIFIED** — deliberately, since
  the VM stays stopped. Two parts with different costs: the systemd unit can be applied by hand over
  SSH on any future boot (steps staged in
  [RUNBOOK-boot-determinism.md](../infra/gcp/p7/RUNBOOK-boot-determinism.md)), but the
  `bootstrap.sh.tftpl` half is the GCE `metadata_startup_script` and needs terraform, which is off
  the table from this checkout (a plan here would destroy the VM + 4 live resources —
  [RECONCILE-GAP.md](../infra/gcp/p7/RECONCILE-GAP.md)). So the durable fix for a rebuilt VM is
  blocked on the same reconcile that has been deferred all along. Runbook step 1 captures evidence
  the fix destroys, so it must run **before** the fix is applied.
  (source: [SESSION-RETRO-2026-07-30](retro/SESSION-RETRO-2026-07-30.md), [ADR 0014](docs/adr/0014-boot-must-converge-or-say-so.md))

- [ ] 2026-07-29 — **Prune the stale P7 world auto-backups?** Four
  `ComfyEra16_backup_auto-*.db` at ~1.33 GB each (~5.3 GB); three are from 07-25/07-26. Pruning
  those three reclaims ~4.4 GB on a disk at 67% (`/mnt/comfy-p7` 21G/32G; `/` is tighter at 79%).
  **Deliberately declined 2026-07-29** in favour of the conservative option — the save-abort
  hazard has fired twice on this box, so backup copies of a 9.16M-ZDO heirloom world have real
  recovery value. Revisit only under actual disk pressure, and note the backups are env-driven
  (see [[p7-world-backups-dev-prod-split]]) so the durable fix is cadence, not deletion.
  (source: [SESSION-RETRO-2026-07-29 addendum 3](retro/SESSION-RETRO-2026-07-29.md))

- [ ] 2026-07-29 — **Restore the swarm harness from `1887626`?** Offered and not taken up while
  Derek was out. It is the only ready-made multi-client harness in the repo, and its own removal
  doc argues the counter-case ("a real capability that was dropped, not merely dead code"). Note
  restoring it does **not** by itself produce agents that play, let alone play *against* each
  other: `AutoCharacterSelectPatches` gets a container past the menu and `MatrixCheckinRunner`
  drives benchmark cells; no adversarial or combat logic ever existed. It is also gated behind
  the unseeded lab clients (pinned item 5, a manual Steam login only Derek can do).
  (source: [SWARM-HARNESS-REMOVED.md](../network/mod/ComfyNetworkSense/SWARM-HARNESS-REMOVED.md), [SESSION-RETRO-2026-07-29 addendum 3](retro/SESSION-RETRO-2026-07-29.md))

*(The AoI optimization items below remain on **hard hold**; see
[PINNED-aoi-optimization.md](PINNED-aoi-optimization.md) — **except** the multi-player-density item,
now promoted to the active ADR 0013 track above.)*

## Pinned — hard hold (2026-07-28, networking lane)

The whole networking/ComfyNetworkSense lane is paused at a green machine-state:
[PINNED-networking-lane-2026-07.md](PINNED-networking-lane-2026-07.md) holds the Wave 0 human
gates (H0-1…H0-4), the ADR 0013 co-presence live test (+ its reproduce-first precondition above),
the patch-load A/B benchmark run, the CRE-E08 candidate→DLL step, and the client01/02 Steam
seeding. No human Steam test is scheduled by the pause. Effort moved to adoption track A7
(Community Workbench).

## Pinned — hard hold (2026-07-21)

Full context and Derek's rationale in [PINNED-aoi-optimization.md](PINNED-aoi-optimization.md).
Move an item back to `## Open` only when Derek re-opens it.

- [~] 2026-07-21 — **Validate the far → approach re-sync under band-shaping.** A dropped far ZDO is
  acked (mandatory, or duplicate storm), so native believes the peer has it; a static far object a
  player leaves and returns to may not be re-offered. Test: fly >64m from a build, return, confirm it
  reloads. First suspect if "distant builds don't reload" is reported. **PINNED.** (source: [ADR 0011](docs/adr/0011-aoi-lives-on-the-producer.md), band-shaping baseline)
- [x] 2026-07-21 — **Band-shaping under multi-player density.** Cost is observers × changed-entities;
  the production validation was single-observer. Two clients in one dense area is the real scaling test.
  → **UNPINNED / promoted:** reproduced live and re-scoped as the ownership/visibility split
  ([ADR 0013](docs/adr/0013-ownership-visibility-split.md)); tracked as the active co-presence item in
  `## Open` above, not on hold. (source: [ADR 0011](docs/adr/0011-aoi-lives-on-the-producer.md))
- [~] 2026-07-21 — **AoI "v.5": hysteresis at the 30/64m band edges + landmark announcement wiring +
  re-run the baseline.** MVP shipped; the edges still flap without a dead-band (ADR 0010), and the
  gateway-side `ReachMeters` is dead-carried (populate it on the priority-manifest broadcast). **PINNED.** (source:
  approved AoI plan; folds in old task 5)

- [x] 2026-07-21 — **An uncut dev build is split-brain: which side is wrong?** → **resolved (a)**:
  ZDO admission now admits on a null baked release and marks the receipt `LegacyUnadmitted` (unattested),
  matching the handshake's fail-open. `ValheimZdoRedirectAdmissionPolicy.cs` returns 200 unattested
  instead of 503 `release_admission_unconfigured` when `expectedModRelease` is null; the deliberately-503
  assertion in `ValheimZdoIntegrationContractTests` was changed to assert admit-unattested. A cut release
  always bakes a real id, so null cannot occur in a promoted image. (HANDOFF task 2.) Original write-up:
  With no baked
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
- [x] 2026-07-21 — **The local comfy-gateway still runs from the RETIRED repo.** → **re-provisioned
  off baseline** (HANDOFF task 1). Rebuilt the `comfy-valheim-lab-comfy-gateway` image from
  `${COMFY_ROOT}/network/mcp` with `COMFY_ROOT=C:/work/baseline`, and recreated only the gateway
  container. The live world was kept in place — `AUTONOMOUS_ROOT` still points at
  `C:/work/comfy/fieldlab/autonomous`, so `/lab/state` binds the same `state/server/data` and the
  valheim-server was never restarted. Verified: `config_files` now
  `C:\work\baseline\...\valheim-lab.compose.yml`, `.Config.Cmd` providers `valheim,inference` (no
  `toolsurface.matrix`), `/healthz` `{"ok":true}`, var mount now `C:/work/baseline/network/mcp/var`.
  The `:8720` surface is now current with this repo. Original write-up: discovered while
  retiring matrix. `docker inspect comfy-valheim-lab-comfy-gateway-1` reported
  `config_files=C:\work\comfy\fieldlab\autonomous\valheim-lab.compose.yml`,
  `working_dir=C:\work\comfy\fieldlab\autonomous`, `COMFY_ROOT=C:/work/comfy`, and an image built
  **2026-07-15** from that repo's `network/mcp`. Baseline's copy of the compose is a faithful clone
  that has never driven anything. This is the same failure the P7 cutover fixed, for a local service:
  source edits in `baseline` do not reach the running gateway, so its live command still names
  `toolsurface.matrix` even though the module is gone from this repo.
  **This is a re-provision, not a bounce** — the image must be rebuilt and the state root moved, and
  `${AUTONOMOUS_ROOT}/state/server/data` is a **live Valheim world**. Decide whether to cut it over to
  baseline (mirroring the P7 approach) or leave the lab gateway sourced from the retired repo
  deliberately. Until then, treat the running `:8720` surface as stale relative to this repo.
- [x] 2026-07-21 — **Retire the matrix MCP surface** → **source side done.** `matrix.py` deleted,
  the four `/valheim/matrix/*` kernel routes removed, three providers lists cleaned (compose,
  `start-comfy-gateway.ps1`, and the `gateway.py` argparse default). The running `:8720` gateway is
  unaffected until the retired-root item above is resolved — it serves an image built 2026-07-15
  from `C:\work\comfy`.
- [x] 2026-07-21 — **D3 + D4, the P3/P5 lab experiments and probe auto-start** → **done**, per
  Derek. 15 keys, three runner files, and `TryDriveNetcodeProbeAuto` removed; 88 → 73 keys. The
  gateway-side injection surface stays (it is wired into `ValheimHandshakeService`).
  (source: [config-surface-decisions](docs/config-surface-decisions.md)) `network/mcp/comfy_gateway/toolsurface/matrix.py`
  (~16 KB, 5 tools) has no client since the mod-side checkout/report loop was deleted. It is **not** a
  simple delete: `kernel/gateway.py` lazily imports it from three custom HTTP routes
  (`/valheim/matrix/{checkout,report,status}`), and it is named in two `--providers` lists. Removing it
  is kernel surgery on the **running** `:8720` gateway plus a bounce, so it needs its own pass with a
  `/checkmcp` after — not a tail-end cleanup. Note the recovered dataset is now committed, so nothing
  is lost by retiring it. (source: `network/mod/ComfyNetworkSense/SWARM-HARNESS-REMOVED.md`)
- [x] 2026-07-21 — **Whether to retire the `clients` profile in `valheim-lab.compose.yml`.** →
  **KEEP as manual noVNC clients**, per Derek (HANDOFF task 9). The four `valheim-client-NN` services
  stay, profile-gated; the in-file comment now records the KEEP decision and how to drive them by
  hand (`--profile clients up valheim-client-01` + noVNC) or restore self-drive (commit 1887626).
  Verified `docker compose config --services` returns only `comfy-gateway` + `valheim-server`. The
  file is untouched otherwise — it is the live definition of the running gateway + server.
- [x] 2026-07-10 — **Fold the sibling client-side `WebRequest` POSTs onto the raw-socket helper**
  (telemetry, priority-mirror, apply-profile). → **done** (HANDOFF task 10). Telemetry heartbeat's
  bespoke socket copy, the priority-mirror `WebRequest`, and the apply-profile `WebRequest` all route
  through `BoundedRawHttp` now (`SendBounded` where a credential header is needed, `PostForBody`
  otherwise). Mod builds net48 0/0; the live dedicated-server POST acceptance stays the low-priority
  integration step. (source: [ADR 0003](docs/adr/0003-server-side-mod-http-raw-socket.md))

## Resolved

- [x] 2026-08-02 — **Lab server compose/state provenance and rendered-client session boundary** — full Baseline state-root migration completed; remaining diagnostic execution is tracked in the Saga. See canonical [PD-7](../docs/decisions/pd-7-lab-runtime-provenance-and-session-boundary.md).

- [x] 2026-07-21 — **Trim the gameplay producer's per-hit `[gp]` diagnostic logging before real
  traffic.** → **gated behind a new `[Gameplay] gameplayEventVerboseLogging` flag (default false),
  not deleted.** The per-hit damage line and the per-death line — the two firehose sources — now log
  only when the flag is on; the discrete lifecycle lines (RPC registered / event sent / server
  received) stay at Info since they fire only on actual routed events. Keeps the diagnostic instrument
  for the next debugging pass while silent under load. Mod builds clean (0 warnings); flag hot-reloadable.
  Not yet deployed to P7. (source: `GameplayEventProducer.cs`, `PluginConfig.cs`)
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
