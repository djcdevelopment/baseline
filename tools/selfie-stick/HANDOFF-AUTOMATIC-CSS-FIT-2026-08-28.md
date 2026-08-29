# Handoff — automatic HABS CSS envelope fitting

Resume in `C:\work\baseline`, not the session's nominal `comfystewardview` cwd. Read the
root `AGENTS.md`, then this file. The work is an R&D probe in the Claude `/rnd` posture:
drive real data through one vertical slice, record the first edge, and do not add test files
or harden/generalize until Derek explicitly locks the result.

## Latest state — v2 stops honestly before the fresh blind set

The causal-repair successor is implemented and development-verified, but it did not earn a
development seal. Do not run its `blind` command.

- Script: `tools/selfie-stick/probe_architectural_css_fit_v2.py`
- Frozen charter: `tools/selfie-stick/architectural-css-fit-v2.json`
- Contracts: `tools/selfie-stick/architectural-css-fit-schemas-v2.json`
- Fresh selection: `tools/selfie-stick/habs-corpus-v2-holdout.json`
- Holdout OCR charter: `tools/selfie-stick/architectural-ocr-audit-v2-holdout.json`
- Holdout OCR revision: `b1743fa5580583635f51` (`PASS`, 27 sheets)
- Development output: `tools/selfie-stick/out/architectural-css-fit-v2`
- Development revision: `2c3595654934efe9a5ad`
- Development integrity verification: `PASS`
- Scientific development acceptance: `FAIL`
- Experiment status: `BLOCKED_AT_DEVELOPMENT_GATE`
- Fresh fitter blind exposure: **0 of 8 buildings**

Metadata-only LOC search froze eight new buildings across seven states and four types before
download. The API estimated 25,859,916 master bytes; verified TIFFs actually total
726,848,012 bytes. Local OCR/CV produced 1,109 tokens, 47 strict dimensions, 76 held
near-misses, and 47 CV candidates with no network/VLM activity during the audit.

The revealed v1 cohort was used for development. Generic upstream repairs now bind dimension
axis to nearby linework, require scale anchors with distinct origins, recover compatible x/z
scale from a selected closed plan loop, allow explicitly reported topology-corroborated
missing axes, and emit ridge/eave datums only as opposed-slope pairs. CSS stays read-only,
pins the graph hash, performs zero discovery, and cannot correct geometry.

The improvements are real but do not compose yet:

| v1 failure cohort (17) | v1 | v2 development |
|---|---:|---:|
| selected primary mass | 3 | 8 |
| compatible independent scale consensus | 0 | 6 |
| calibrated paired roof datums | 1 | 7 |
| validated G1 | 0 | 0 |

`tx1037` now reaches validated G1 and `ak0535` reaches G1-unvalidated, but both are known
regression controls, not members of the revealed v1 failure cohort. Across all 20 development
buildings the routes are 1 G1, 1 G1-unvalidated, 14 A0, and 4 held. `tn0305` and `il0180`
remain unpromoted. Every original regression check still passes: exact `sd0401` dimensions,
typed `tx1037` ceiling nodes, and separate `ak0535` LOG CABIN/ADDITION masses.

The only failed development check is the frozen requirement for two validated G1 buildings
inside the failure cohort (actual 0). The evidence graph contains 168 views, 319 dimension
bindings, 156 chains, 57 masses, 245 datums, and 49 roof pairs. Those facts occur on different
buildings/sheets; no generic cross-sheet registration yet proves that a selected plan mass and
a calibrated roof pair share one building frame. That is the next connector. Do not lower the
gate, tune against the fresh eight, or treat acquisition/OCR as blind fitter exposure.

## Prior state — deterministic pre-CSS topology v1

The ownership edge was locked, implemented, and run through its frozen 3/17 evaluation.

- Script: `tools/selfie-stick/probe_architectural_css_fit_v1.py`
- Frozen charter: `tools/selfie-stick/architectural-css-fit-v1.json`
- Contracts: `tools/selfie-stick/architectural-css-fit-schemas-v1.json`
- Output root: `tools/selfie-stick/out/architectural-css-fit-v1`
- Immutable evidence revision: `da9fb53b6e49c3718ea3`
- Development: `PASS`, sealed before blind exposure
- Blind result: `INSUFFICIENT_AUTOMATIC_EVIDENCE`
- Blind routes: 0 validated G1, 13 `A0_TRIAGED`, 4 `HELD`
- Verification: `PASS` across 20 buildings
- Cached rerun: 17 cached, zero evidence/topology/CSS work

The first post-blind rerun found a persistence-only issue: dynamic executed/cached counters
were being written into immutable `index.json`. After all receipts validated and before any
evidence work, that write failed. The current source has a completed-seal cache short-circuit;
it validates the sealed receipts and writes counters only to the mutable root report. It did
not rewrite revision `da9fb53b6e49c3718ea3` or any automatic seal. Use a fresh `--out` root
for a from-scratch reproduction because the source content address has consequently changed.

The v1 dataflow moves view partitioning, dimension-chain ownership, mass selection, and typed
vertical datums ahead of the metric graph. CSS consumes only sealed evidence and metric graphs,
pins the graph hash, emits attributed residuals, performs zero discovery operations, and
cannot correct geometry.

All seven development checks passed. `sd0401` recovered exact 15.928975 m width, 4.333875 m
depth, and 3.302 m ridge after the development seal, with zero cross-role view overlap.
`tx1037` kept both ceiling observations typed as ceiling. `ak0535` retained distinct LOG CABIN
and ADDITION masses and selected 6.2992 m rather than the basement's 10.9474 m as primary
width.

The blind transfer gate then failed without tuning. Across the 17, all lacked passing scale
anchor/spread and numeric-envelope gates, 16 lacked paired typed eave/ridge evidence, and 14
lacked a selected closed two-axis primary mass. Five also lacked opposed-slope gable topology
and three lacked an independent holdout. Both negative controls stayed unpromoted.

The next connector is still upstream of CSS: complete scale notation must transfer to the
disjoint plan owner, two-axis chains must close a primary mass without building-specific
labels, and a paired typed eave/ridge stack must survive. The revealed 17 are no longer blind.
Do not tune v1 or admit lessons from it; a next experiment needs a new charter and fresh
holdout.

## Current state

The automatic 20-building HABS sweep is implemented and complete.

- Script: `tools/selfie-stick/probe_architectural_css_fit.py`
- Frozen charter: `tools/selfie-stick/architectural-css-fit-v0.json`
- Contracts: `tools/selfie-stick/architectural-css-fit-schemas-v0.json`
- Output root: `tools/selfie-stick/out/architectural-css-fit`
- Current immutable revision: `3899e363a8b63658dc8a`
- Scientific result: `INSUFFICIENT_AUTOMATIC_EVIDENCE`
- Verification: `PASS`
- R&D record: `tools/selfie-stick/EXPERIMENT.md`, section beginning at line 1444
- Operator README: `tools/selfie-stick/README.md`, section beginning at line 332

The prescribed three-building follow-up is also complete.

- Script: `tools/selfie-stick/probe_architectural_css_topology.py`
- Output root: `tools/selfie-stick/out/architectural-css-topology`
- Current immutable revision: `cf5c847a7f5232d38c0c`
- Scientific result: `ATTRIBUTION_SEPARATED`
- Verification: `PASS` over 49 hashed artifacts
- Scope: `sd0401`, `tx1037`, and `ak0535` only; 39 structural-line overlays

The sweep reused 69 frozen real-OCR sheets and produced 168 automatic panels and 165
bound dimensions. Routes were 0 validated G1, 2 `G1_UNVALIDATED`, 14 `A0_TRIAGED`, and
4 `HELD`. The unchanged rerun cached all 20 buildings with zero evidence reads and zero
fit, OCR, VLM, network, download, or world work.

No Ollama/VLM was called or replaced. No Creator OS messages, Valheim contact, prefab
routing, ZDO generation, or world writes occurred.

## Edge found

Calibration and plan fitting are connected, and the follow-up now separates the formerly
combined attribution. The three misses are ownership errors at different joins:

- `sd0401`: the section and north-elevation crops overlap by `0.719356` of the smaller
  panel, and the fitter chose the compound `34'-11"` plan depth. The sealed dimension
  candidates contained `15.928975 × 4.333875 m` plus a `3.302 m` ridge; all three matched
  the accepted graph exactly only after the new candidate seal was written.
- `tx1037`: the held `CEILING | 9'-7 1/4"` binding was scored as `eave_height_m` even
  though strict `ROOF EDGE` datums survive independently. The reported `0.873 m` eave
  failure is semantically invalid; this is ceiling/eave conflation, not a scale failure.
- `ak0535`: the floor panel adopted the basement's `35'-11"` overall width. The floor
  chain instead labels `LOG CABIN 20'-8" × 16'-5"` and the `ADDITION` separately; the
  floor/basement crop overlap is `0.566`, and section C has separate ridge, ceiling,
  first-floor, and basement stacks.

This historical diagnostic led to v1 above. Do not tune the corpus promotion gates, reroute a
v1 blind graph, or use the revealed 17 as a fresh holdout. The safe next action is a new frozen
charter/corpus split for scale ownership, two-axis mass closure, and paired datum survival.

## Resume commands

Use the already pinned local environment; do not install packages into another toolchain.

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'

# This should be a fully cached 20-building run.
& $python .\tools\selfie-stick\probe_architectural_css_fit.py run
& $python .\tools\selfie-stick\probe_architectural_css_fit.py verify

# Bounded attribution probe; should report ATTRIBUTION_SEPARATED and PASS.
& $python .\tools\selfie-stick\probe_architectural_css_topology.py run
& $python .\tools\selfie-stick\probe_architectural_css_topology.py verify

# Completed v1 blind run; validates and reuses all 17 sealed receipts.
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py blind
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py verify

# v2 remains a cached, unsealed development diagnosis. `develop` exits nonzero by design.
& $python .\tools\selfie-stick\probe_architectural_css_fit_v2.py develop
& $python .\tools\selfie-stick\probe_architectural_css_fit_v2.py verify

# The server will not survive reboot.
& $python .\tools\selfie-stick\probe_architectural_css_fit.py serve --port 8878
& $python .\tools\selfie-stick\probe_architectural_css_fit_v1.py serve --port 8879
```

Then open `http://127.0.0.1:8878/index.html`. The most useful detail page is
`http://127.0.0.1:8878/buildings/tx1037/index.html`.

Expected unchanged-run receipt:

```text
revision 3899e363a8b63658dc8a
RESULT INSUFFICIENT_AUTOMATIC_EVIDENCE
cached: 20
executed: 0
evidence_reads: 0
fit_runs: 0
verification: PASS

topology revision cf5c847a7f5232d38c0c
topology RESULT ATTRIBUTION_SEPARATED
topology verification: PASS

v1 revision da9fb53b6e49c3718ea3
v1 RESULT INSUFFICIENT_AUTOMATIC_EVIDENCE
cached: 17
executed: 0
evidence_reads: 0
topology_runs: 0
css_runs: 0
v1 verification: PASS

v2 development revision 2c3595654934efe9a5ad
v2 development acceptance: FAIL
v2 integrity verification: PASS
v2 fresh blind buildings exposed: 0
```

## Worktree caution

The Baseline worktree was already dirty with the larger architectural R&D vertical slice.
Most architectural files remain untracked, while `README.md` and `EXPERIMENT.md` are
modified. These changes are intentional and mutually dependent. Preserve them, do not use
blanket staging, reset, checkout, or cleanup, and do not commit/push unless Derek asks.

The generated `out/` revisions are local experiment evidence and ignored by Git. The
tracked/untracked implementation added in the final lap is limited to the script, charter,
contracts, README section, experiment-log section, and this handoff; do not mistake the
other existing architectural files for disposable scratch.
