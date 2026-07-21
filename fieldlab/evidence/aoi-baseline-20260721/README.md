# AoI measurement landscape — 2026-07-21 baseline

**Purpose.** Not a precise capacity "knee" number — the harness can't reach one reliably and the
absolute figure isn't the point. This is a **consistent, re-runnable reference**: a coarse grid of
`config × load` capturing a broad set of health signals, so a *future* change (hysteresis, a
send-path fix, a new replication policy) can be re-run on the same grid and **diffed** against these
numbers. Broad landscape, not a topographic map.

Produced against the Lumberjacks netcode-replacement stack (20 Hz tick, 50 ms budget) run from
`infra/docker/docker-compose.yml`, driven by `scripts/load-test-dual-channel.js` (wandering bots,
`BOT_WANDER=1`), `Replication:AdaptiveDegrade=false` throughout. Harnesses:
`scripts/aoi-knee-sweep.sh`, `scripts/aoi-knee-matrix.sh`, `scripts/aoi-baseline-harness.sh`.

---

## The consistency problem is the main finding

**A single number here is trustworthy to no better than ~2×, and can swing 20× if the environment
isn't controlled.** The same cell (Tiered 100/300, 100 bots) measured **12 ms p99** on a fresh stack
and **242 ms p99** later in the same session. That 20× gap is not config and not cold JIT — a
controlled test on a *fresh* stack showed cold (~12 ms) and warm (~8.6 ms) are within ~1.4× of each
other. The blow-up came from **accumulated stack/host state**: dozens of gateway recreations and
thousands of bot connect/disconnect cycles degrade Postgres and churn host resources over a long
session.

Four contaminants, in rough order of size:

| contaminant | effect | control |
|---|---|---|
| **Accumulated session state** | up to ~20× p99 inflation, tick-rate collapse | **Fresh `docker compose down && up` per measurement session**; don't accumulate |
| **Single-process generator ceiling** | ≥~300 bots fails to connect, returns zeros | shard bots across N Node processes before trusting the high end |
| **Postgres errors under concurrent joins** | `Npgsql` exceptions on the join path add latency | isolate/warm the DB; keep DB work off the hot path |
| **Run-to-run noise** | ±2× p99, non-monotonic ordering across radii | repeat each cell ≥3×, report median; quiesce the host |

**Protocol for using this as a correlation baseline:** fresh stack, let the tick loop settle, run the
same grid, and **only believe deltas larger than ~2×**. Small movements are noise until the
environment is hardened (isolated host, pinned CPU, repeated cells).

**It is not a leaking entity queue.** A repeated run→disconnect→idle cycle test showed
`total_players` returns cleanly to 0 after every cycle and idle-tick p99 stays flat (~0.03–0.06 ms) —
disconnected bots drain properly, so the accumulation is *not* ghost players the tick loop keeps
processing. The residual long-horizon drift is Postgres/host churn over a long session; we did not
chase it further because the fresh-stack control already removes it and the absolute number is not
the goal.

---

## The landscape (reproducible cells, fresh stack)

Tiered policy, wandering bots, p99/p50 in ms. These reproduce across fresh-stack runs.

**Config A — default `NearRadius=100 / MidRadius=300`:**

| bots | overruns | total p50 | total p99 | p99/p50 | interest p99 | send p99 | sent | culled |
|---|---|---|---|---|---|---|---|---|
| 50  | 0  | 0.87 | 2.73 | 3.2 | 0.11 | — | 31k | 219k |
| 100 | 0  | 2.36 | ~12  | ~5  | 0.43 | 11.4 | 127k | 873k |
| 200 | 0  | 7.70 | 43.3 | 5.6 | 3.59 | — | 493k | 3.5M |
| 400 | 36 | 38.6 | 319  | 8.3 | 11.6 | — | 2.46M | 10.6M | *(near generator ceiling — indicative)* |

**Config B — aggressive `NearRadius=30 / MidRadius=64`:**

| bots | overruns | total p50 | total p99 | p99/p50 | interest p99 | sent | culled |
|---|---|---|---|---|---|---|---|
| 50  | 0 | 0.66 | 0.86 | 1.3 | 0.13 | 7.2k | 243k |
| 100 | 0 | 1.24 | 1.81 | 1.5 | 0.26 | 17.5k | 983k |
| 200 | 0 | 3.07 | 5.16 | 1.7 | 0.93 | 54.5k | 3.95M |

What the landscape says, broadly:

- **Send dominates; the filter is cheap.** At 400 bots (Config A) the `interest` (AoI filter) phase
  p99 was 11.6 ms while total p99 was 319 ms — the filter is ~4% of the tick. The cost is `send`
  (serialization + socket writes), which tracks *sent-update volume*. Deciding what to send is cheap;
  sending it is the ceiling. (Unsurprising, now quantified.)
- **Variance onset precedes failure onset.** p99/p50 climbs (3.2→5.6 for A) with p99 brushing the
  50 ms budget at 200 bots *before* any overrun fires at 400.
- **The aggressive dual cut buys ~8× headroom.** At 200 bots Config B holds total p99 at 5.2 ms vs
  Config A's 43 ms, and keeps p99/p50 near 1.5 (vs 5.6) — far more *consistent*, which is the actual
  fidelity goal.
- **The failure mode is tick-rate collapse.** In a degraded cell the observed tick rate fell from
  20 Hz to ~7 Hz with ~300% CPU — watch `obs_tick_hz` and CPU together, not just p99.

## Rule: cut **both** radii together

Cutting `NearRadius` while leaving `MidRadius` wide is a trap. `NearRadius=30 / MidRadius=300` (only
the near band cut) was catastrophic — 100 bots → **887 ms** p99, mid-band population **14.5M**,
sent 4.1M; 200 bots → **1634 ms** — while `60/300` at 100 bots was fine (12 ms). `MidRadius` bounds
what enters the datagram lane at all; shrink only the near radius and every entity spills into the
mid annulus, which still replicates at 5 Hz over a huge area. **The outer radius is the load-bearing
wall.** Config B works because it cuts both.

## The recovered pressure model is falsified

The 9,600-row `aoi-density-pressure-matrix-20260704/modeled-pressure-matrix.csv` predicts
`server_process_ms` → a green/yellow/red `process_budget`. Its predicted `server_process_ms` is
**identical across `actor_players` = 1, 5, 25, 50, 100** (same 2.0–55.0 ms range, same 384 red cells
at every player count) — i.e. it asserts tick cost is *independent of player count*. Measurement
flatly contradicts this: at fixed config, total p99 scales 2.7 → 12 → 43 ms across 50 → 200 bots.
Player count / sent volume is a first-order driver the model omits. **Do not use that model for
capacity planning.** (This is the "validate the model against reality" step the 2026-07-04 campaign
never reached — it produced zero networked measurements.)

## How to diff a future change against this baseline

Re-run the same grid on a fresh stack and compare the health signals, not a single p99:

- **Serialization / socket optimizations** → should drop `send` p99 and `total` p99 at 200+ bots.
- **A new AoI policy / radius change** → should shift `sent`/`culled` and the `interest` phase.
- **Hysteresis / debounce (HANDOFF task 5)** → should change `sent` counts and, if it reduces churn,
  tighten `interval` slip; watch for it *not* re-introducing overruns.
- Always cross-check **`obs_tick_hz`, overruns, CPU, degraded/deadline, and gateway error count** —
  a change that trades p99 for dropped ticks or DB errors is not a win.

## Caveats

- Single-host, single-process generator (≤~300 reliable bots), `AdaptiveDegrade` off (raw pressure,
  no shedding), bots wander uniformly (real players clump — localized O(N²) interest cost will differ),
  coarse grid, single runs per cell (so ±2× noise). Harden the environment (fresh stack, sharded
  generator, repeated cells, quiesced host) before treating any cell as precise.

## Decision: measurement phase closed — build AoI end-to-end

Recorded 2026-07-21, per Derek. The measurement has done its job. It is already clear the system
**needs** aggressive AoI, and the shape is known: cut the full-rate radius hard, cut both radii
together, keep the reliable lane region-wide, and grant long-range presence to landmarks as a
separate channel (task 7, already implemented at the contract layer). We now have (a) a baseline to
diff against, (b) a clear understanding of *why* we test (send-volume is the ceiling, not the
filter), and (c) how to shape future tests (fresh stack, watch tick-rate/CPU/errors, believe only
>2× deltas). Chasing a precise knee number on a single-host, single-process harness would add
nothing decidable.

**Next: implement the AoI shape end-to-end in the mod and network**, not just measure it — the
three-tier full/thinned/dropped shape plus landmark reach, wired through the gateway's replication
path and the mod's redirect/priority path, then re-run this baseline grid to confirm the headroom
holds in the real path. This supersedes the standalone HANDOFF task 5 (hysteresis), which folds into
the same implementation.

## Files

- `sweep_default.csv` — Config A bot-count sweep (100/300).
- `sweep_near30mid64.csv` — Config B bot-count sweep (30/64).
- Harnesses live in `Lumberjacks/scripts/aoi-{knee-sweep,knee-matrix,baseline-harness}.sh`.

*Interpretation first-drafted via HEARTH `gcp-gemini-pro`, then reconciled against the fresh-stack
control run and edited.*
