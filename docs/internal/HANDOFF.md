# Handoff — the queue after the 2026-07-21 audit

> **HISTORICAL:** This handoff records the former monorepo and is not an operational
> queue. Use [`REPO-MAP.md`](../../REPO-MAP.md) for current authority.

> **Stale handoff (redirect added 2026-07-29):** superseded by `HANDOFF-2026-07-29.md`
> at the repo root, the current canonical handoff. This file is retained as a
> historical record of the 2026-07-21 session and must not be used for cold pickup.

Ten tasks, ordered. Each states **what to do**, **why it matters**, and **how you'll know it
worked**. Every one traces to something found on 2026-07-21; nothing here is speculative.

Point a fresh session at this file.

---

## Progress — 2026-07-21 session 2 (branch `claude/handoff-code-line-2026-07-21`)

The seat-free code line is **done and verified** (sdk:9.0 container for Lumberjacks, net48 host
build for the mod). Tests 528 → **533** in Lumberjacks; mod contract tests 2 → **23**; mod builds
0 warnings.

- ✅ **1** — comfy-gateway re-provisioned off baseline (`COMFY_ROOT=baseline`, world kept in place, no server restart); `:8720` now serves `valheim,inference` only. (infra — no commit)
- ✅ **2** — dev-build split-brain resolved option (a): uncut builds admit schema-2 ZDOs unattested. `5f79fd0`
- ✅ **3** — near/mid/far band population per tick, surfaced at `/tick`. `480849f`
- ✅ **7** — landmark reach (networking slice): `ZdoIntegrationContract.Admits` + reach field + config. `1dd6c18`
- ✅ **9** — clients profile KEPT as manual noVNC (Derek's call). `296ceab`
- ✅ **10** — three sibling POSTs folded onto `BoundedRawHttp`. `7c58e49`
- ✅ **4** — AoI measurement run headless (Lumberjacks stack + wandering bots). **Closed as a measurement phase**, per Derek: the landscape is mapped, `send`-volume is the ceiling (filter ~4% of tick), the aggressive dual radius cut buys ~8× headroom, the recovered pressure model is **falsified** (player-invariant), and the harness is a re-runnable baseline (fresh-stack protocol, ±2× noise). See [`fieldlab/evidence/aoi-baseline-20260721/`](../../fieldlab/evidence/aoi-baseline-20260721/README.md). Harnesses in `Lumberjacks/scripts/aoi-*.sh`.

**Decision (2026-07-21): stop measuring, implement AoI end-to-end.** The findings justify building the
three-tier full/thinned/dropped shape + landmark reach through the gateway replication path and the
mod redirect/priority path, then re-running the baseline grid to confirm. This subsumes task 5.

Still open, needing the seat / infra / a live world:

- **NEW · AoI end-to-end implementation** — build the measured shape for real (mod + network). Task 7's landmark-reach contract is the first piece; task 5 (hysteresis) folds in here.
- **6** — two-client recipient isolation: needs two real Steam clients + you in the seat. Task 9 kept the noVNC clients available for it.
- **8** — reference production `.cfg`: needs the P7 VM's live cfg to diff against.

---

## State in six lines

- 20 commits, `ac151fc..bd6d72f`. Tree clean. `origin/main` is at `f945562`; the last few
  commits are local only.
- Tests **528/528**. Mod builds 0 warnings. Config surface **107 → 73 keys**.
- The intermittent `Game.Simulation.Tests` failure is fixed (`d5bed21`).
- Read [ADR 0010](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0010-consistency-is-predictability.md) before touching AoI.
- **Do not delete `fieldlab/autonomous/`** — it is the live definition of a running gateway and
  a running Valheim server.
- The P7 VM is running and billing, by decision.

---

# The queue

## 1 · Re-provision the local comfy-gateway off the retired repo

**Do:** rebuild and recreate `comfy-valheim-lab-comfy-gateway-1` from
`C:\work\baseline\fieldlab\autonomous\valheim-lab.compose.yml`, with `COMFY_ROOT` pointing at
`baseline`. Decide the state root first — `${AUTONOMOUS_ROOT}/state/server/data` is a **live
Valheim world**; either keep it where it is and repoint only `COMFY_ROOT`, or move it
deliberately with a backup.

**Why:** `docker inspect` reports the running gateway was launched from
`C:\work\comfy\...\valheim-lab.compose.yml`, image built **2026-07-15** from that repo's
`network/mcp`. Source changes in `baseline` do not reach it — its live command still names
`toolsurface.matrix` even though the module was deleted here. This is the exact failure the P7
cutover fixed, for a local service nobody had checked.

**Test:**
```
docker inspect comfy-valheim-lab-comfy-gateway-1 --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}'
  → must be under C:\work\baseline
docker inspect ... --format '{{json .Config.Cmd}}'   → must NOT contain toolsurface.matrix
Invoke-RestMethod http://127.0.0.1:8720/healthz      → {"ok":true,...}
```
Then confirm the MCP tool list no longer offers `valheim_matrix_*`. This is a re-provision, not
a bounce — budget for the Valheim server restarting alongside it.

---

## 2 · Resolve the dev-build split-brain

**Do:** pick one of three, all written up in `fieldlab/DECISIONS-PENDING.md`. Recommended: make
`ValheimZdoRedirectAdmissionPolicy` **admit** when `expectedModRelease` is null, flagging the
receipt unattested via the existing `LegacyUnadmitted` semantics.

**Why:** an uncut local build gets `ExpectedModRelease == null`. The handshake **fails open**
(`ValheimHandshakeService.cs:546` skips the gate on empty), while ZDO admission **fails closed**
with 503 `release_admission_unconfigured` (`ValheimZdoRedirectAdmissionPolicy.cs:30`). So a dev
build connects cleanly and then has every ZDO rejected. It costs an hour of confused debugging
the first time and it hits exactly the operator-in-the-seat workflow. Both behaviours are
deliberate — one argues in a doc comment, the other asserts in a test — which is why this is a
decision, not a bug fix.

**Test:** build the mod uncut, connect, submit a schema-2 ZDO. It must either be admitted (and
recorded as unattested) or refused at *both* gates. Update
`ValheimZdoIntegrationContractTests` — it currently asserts the 503 on purpose, so that
assertion has to change deliberately, not incidentally.

---

## 3 · Add band-population counters

**Do:** emit near / mid / far entity counts per tick from `InterestManager`, folded into the
existing `TickMetrics` snapshot so they surface at `/tick`.

**Why:** everything else needed for the knee sweep already exists — budget, overruns counter,
per-phase histogram, sent-vs-culled. Band population is the one missing piece, and without it a
sweep tells you *that* cost rose but not *which band* caused it. Do this **before** task 4 or
you will run the experiment twice.

**Test:** with `NearRadius=100`/`MidRadius=300` and a known entity layout, the three counters sum
to the changed-entity count, and moving an entity across 100.0 units moves it between buckets.

---

## 4 · Run the AoI knee sweep

**Do:** follow
[`Lumberjacks/docs/network/aoi-knee-experiment-brief.md`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/Lumberjacks/docs/network/aoi-knee-experiment-brief.md)
— it is self-contained and pastes as an opening prompt. Sweep the three-tier shape first:
`NearRadius` ~30, `MidRadius` ~64, `MidTickInterval` for the thinned rate.

**Why:** the recovered model predicts a knee across 9,600 rows and **not one has ever been
checked against an observation**. The number makes every downstream AoI argument decidable
instead of guessed. The three-tier shape is the largest single lever in the model: cost is
concentrated entirely in `near_20hz` (0–50 m), far is already zero, and area goes as r², so
pulling the full-rate radius from 50 m to ~30 m removes ~71% of the objects in the only
expensive band.

**Test:** two curves, not one — **variance onset** (p99 pulling away from p50) and **failure
onset** (first non-zero `game.tick.overruns`). Then check the variance for **correlation with
density**: correlated spread is the system telling the truth about load; uncorrelated spread is
the defect (ADR 0010). Set `AdaptiveDegrade=false` for the measurement runs and `BOT_WANDER=1`
so bots actually cross boundaries — clustered bots measure nothing.

---

## 5 · Add hysteresis at the two flap points

**Do:** a dead-band at the `InterestManager` band boundaries
(`InterestManager.cs:113`, `:118` — currently plain `<=`), and a cooldown or
degrade/recover asymmetry in `AdaptiveDegrade.ShouldSuppressMidBand`.

**Why:** `AdaptiveDegrade.cs:22-23` says degrade "lifts the instant the relevant broadcast fits
inside budget again — no cooldown, no hysteresis." Sitting exactly at budget it can answer
differently tick to tick from a cause no player can perceive, and an entity hovering at exactly
`NearRadius` flips between 20 Hz and 5 Hz every tick. Per ADR 0010 that is **chatter, not
falloff** — indistinguishable from randomness at the player's end, and therefore a fidelity
defect rather than a performance one. Adaptive falloff itself is correct and stays.

**Test:** unit-testable without a server. Oscillate an entity across the boundary by ±0.1 units
and assert its band does not change every tick. Feed alternating just-over / just-under budget
values and assert suppression does not toggle each time. Do this **after** task 4 so the knee is
measured against current behaviour, then re-measure.

---

## 6 · The two-client recipient isolation gate (M4b)

**Do:** make pending delivery and acknowledgement recipient-scoped, then run two real Steam
clients and prove neither can consume or acknowledge the other's ZDOs.

**Why:** this is the program's own stated next correctness gate
(`infra/gcp/p7/README.md`). The partitions exist; the isolation is untested. Everything about
multi-player capacity is downstream of it, and the m5 evidence explicitly says it establishes
single-client delivery authority **only**.

**Test:** two enrolled clients, one window. Each receives only its own relevant ZDO set; neither
acknowledgement affects the other's queue. Needs you in the seat for the joins.

---

## 7 · Implement landmark reach

**Do:** add a **reach** field to `ValheimPriorityObject` / `ValheimPriorityDeliveryItem`, and
extend the admission predicate at `ZdoRedirectRunner.cs:337` to *admit if rank allows **or** this
is a landmark within its reach of the observer*.

**Why:** the lighthouse. Everything else already exists — `StableKey` is your per-object
selector, `Position` is absolute, `structural_anchor` is already rank 2, the reliable lane is
already region-wide and unfiltered, and the manifest already has a broadcast wire. Today
`DistanceMeters` means *observation* distance; nothing means *visibility* range. See
[landmark-reach-design.md](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/Lumberjacks/docs/network/landmark-reach-design.md).

**Test:** an object marked with reach R is delivered to a client at distance R while an
unmarked peer object at the same distance is not, and the datagram path shows **no** added
per-tick cost — a static landmark is pure reliable-lane traffic.

---

## 8 · Track a reference production mod `.cfg`

**Do:** commit the live P7 mod config as a reference file, clearly labelled as the expected
production posture.

**Why:** the serving-path posture exists only as VM state plus a runbook paragraph. The
`ActiveSeconds` defaults were flipped to 0 (`8ba6398`) so a VM built from defaults is no longer
dangerous, but nothing in version control still records what production actually runs.

**Test:** diff the tracked reference against the VM's live `.cfg` — it should be empty, and any
drift should be explainable.

---

## 9 · Decide the `clients` profile in the lab compose

**Do:** either delete the `valheim-client-NN` services or keep them as manual noVNC clients.

**Why:** they can no longer self-drive — their `COMFY_AUTOJOIN` handler went with the swarm
harness — so they boot and idle at character select logging `rtt_ms = 0`. They are gated behind
`profiles: ["clients"]` and marked in-file, so nothing starts them by accident.

**Test:** whichever way, `docker compose up` (no profile) must still bring up only
`valheim-server` and `comfy-gateway`.

---

## 10 · Fold the sibling `WebRequest` POSTs onto the raw-socket helper

**Do:** telemetry, priority-mirror and apply-profile POSTs → the `BoundedRawHttp` helper.

**Why:** ADR 0003. They run client-side where the "URI prefix is not recognized" Mono defect is
inert, so this is genuinely low priority — required only if any ever needs to run server-side.

**Test:** each POST succeeds from a dedicated server context, where `WebRequest.Create` fails.

---

# Sequencing

**1 → 2** first: both are traps that cost time before they cost anything else.
**3 → 4 → 5** is the AoI line and must run in that order — instrument, measure, then damp and
re-measure. **6** is the program gate and needs you in the seat. **7** is the payoff. **8–10**
are tail hygiene, any time.

# Do not re-execute

`fieldlab/docs/config-surface-decisions.md` still contains its **original** D2/D3 reasoning
below a revision banner. Those recommendations were **withdrawn** — all three D2 groups are
load-bearing, and `LumberjacksProjectionRunner` in particular renders local-only primitives with
no ZDO ownership, which is the far-field proxy prototype task 7 needs. Read the banner first.

# Record

[Retro](../../fieldlab/retro/SESSION-RETRO-2026-07-21.md) (two, the second an addendum) ·
[the mess](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/audit-2026-07-21-conditional-logic.svg) ·
[the sixteen twists](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/audit-2026-07-21-the-twists.svg) ·
[AoI findings](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/Lumberjacks/docs/network/area-of-interest-findings.md) ·
ADRs [0008](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0008-liveness-is-not-admission.md) ·
[0009](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0009-verify-against-an-independent-source.md) ·
[0010](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/fieldlab/docs/adr/0010-consistency-is-predictability.md)
