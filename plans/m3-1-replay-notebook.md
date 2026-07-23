# M3-1 — Counterfactual Replay Notebook

## Objective
An offline notebook/workbook that loads a recorded session's JSONL logs from
git, re-runs the scoring equations (owner election, priority/shedding) under
adjustable weights, and diffs outcomes against what actually happened. Tuning
becomes: replay → adjust → diff → then apply live. No game or server needed.

## Context
- Equations, weights, and normalization: `network/telemetry-and-scores.md`
  (owner score composite, component scores, hysteresis/cooldown rules).
- Record types: `client_sample`, `server_sample`, `event_marker`,
  `owner_election`, plus `decision_trace` if M2-2 has landed.
- First locate the real session logs in git (`data/`, `network/`, or fieldlab
  outputs) — pick the richest single session as the demo dataset and record
  its path in the notebook header.

## Steps
1. Build `tools/replay/` (Python, stdlib + pandas/matplotlib acceptable):
   loaders for each JSONL record type keyed by `session_id`, aligned on
   `timestamp_utc`.
2. Implement the scoring math as pure functions mirroring the doc exactly —
   one function per component score, weights as a parameters dict. Where the
   doc says "conceptual formula," implement the doc's stated early weighting
   and flag divergences from mod code with a comment.
3. Notebook `tools/replay/replay-workbook.ipynb` (or a marimo/plain-script +
   HTML export if Jupyter is unavailable) with sections: load session →
   timeline with event markers → owner elections recomputed under the live
   weights (should reproduce recorded winners; report mismatches, don't hide
   them) → counterfactual pane: edit the weights dict, re-run, diff table
   ("with proximity 0.30: Alice wins at 14:32 instead of Bob; N fewer
   low-priority drops during combat").
4. A `README.md` in `tools/replay/` telling the next agent how to point it at
   any other session.

## Acceptance
- Reproduction check: recorded `owner_election` winners are reproduced from
  raw inputs for the demo session, or every mismatch is listed with a suspected
  cause (this is a finding, not a failure).
- Changing a weight produces a materially different, explained diff.
- Runs clean from a fresh checkout with documented deps.

## Out of scope
Live tuning application; HUD; bundling into the lab stack (M4-2 consumes this).
