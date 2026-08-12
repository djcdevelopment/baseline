# AoI density-pressure matrix — recovered artifacts (campaign of 2026-07-04)

Rescued 2026-07-21 from `C:\work\comfy\network\mcp\var\matrix\`, a gitignored var directory
in a retired source repo. These were never tracked in git. They are committed here because
they are the only surviving record of the area-of-interest density campaign, and because a
`var/` directory in a retired checkout is not a durable home for evidence.

See [`Lumberjacks/docs/network/area-of-interest-findings.md`](https://github.com/djcdevelopment/baseline/blob/aceb2eb48d770885a2c4171b926867f4ee82b4a4/Lumberjacks/docs/network/area-of-interest-findings.md)
for what they mean and what to do next.

## What these three files actually are

### `modeled-pressure-matrix.csv` — 9,600 rows. **Modeled, not measured.**

A full predictive model of network pressure across the AoI parameter space. Columns include
`density_band`, `observer_range`, `observer_distance_m`, `interest_bucket` (e.g. `near_20hz`),
`build_zdos_500m`, `total_zdos_500m`, `modeled_movement_events_per_sec`,
`modeled_reliable_events_per_sec`, `modeled_low_priority_events_per_sec`,
`estimated_datagram_updates_per_sec`, `estimated_udp_kbps`, `process_budget`
(e.g. `green_under_tick`) and `priority_expectation`.

This is the substantial artifact and it is genuinely useful — but every number in it is a
**prediction**. Nothing here was observed.

### `plan.json` — 96 cells. **The campaign barely ran.**

| status | cells |
|---|---|
| done | 1 |
| assigned | 1 |
| pending | 94 |

A cell is a density band coordinate + observer range offset + event profile + a 60 s
benchmark window.

### `results.jsonl` — 1,000 rows, of which **one is real**.

| source | rows | what it is |
|---|---|---|
| `sim-viking01` … `sim-viking30` | 998 | **Simulated.** Each row carries a `sim` key and a thin metric set (`avg_fps`, `bytes_out_per_sec`, `load_time_ms`, `p95_rtt_ms`). A dry run proving the checkout/report pipeline worked end to end across all 96 cells. |
| `test` | 1 | Smoke row (`{"fps": 60}`). |
| `viking1` | **1** | **The only real in-game capture.** |

The single real row, in full context:

- cell `open_control.self.movement_only` — the *empty* control cell
- `benchmark_type: safe_state_frame_probe`, `benchmark_completed: true`, 62.8 s
- `avg_fps: 12.03`, `p95_frame_time_ms: 16.4`, `load_time_ms: 19,930`
- `nearby_build_pieces: 48`, `nearby_entities: 0`, `nearby_players: 0`
- `mode: Solo`
- **`rtt_ms: 0`, `jitter_ms: 0`, `bytes_in_per_sec: 0`, `bytes_out_per_sec: 0`,
  `packets_in_per_sec: 0`, `packets_out_per_sec: 0`**

## The conclusion that matters

Those zeros are the whole story. The client was in **Solo mode and never connected**, so
every network field is empty. Even the one real sample measured **no network traffic at all**
— which means the campaign produced **zero networked AoI measurements**.

That is the honest answer to "we did so much testing and never incorporated it" for this
campaign specifically: the harness was built, modeled and proven, and then it stopped before
producing anything that *could* have been incorporated. Not neglect — an unfinished
measurement run.

It is also a textbook instance of the trap recorded in
`Lumberjacks/docs/network/interest-subscription-events-testing.md`: a client that does not
move through a live world produces nothing an interest-management campaign can use. Here it
was worse than stationary — it was disconnected.

## If this is re-run

1. **Assert connectivity before recording.** A sample with `rtt_ms == 0` and
   `bytes_in_per_sec == 0` is not a measurement; it should be rejected at capture, not
   discovered in analysis three months later.
2. **Validate the model against reality.** 9,600 modeled rows exist and not one has been
   checked against an observation. The first real cells should be chosen to falsify the
   model's `estimated_udp_kbps` and `interest_bucket` predictions, not to confirm them.
3. **Commit results as they land.** These files spent three months one `rm -rf` from gone.
