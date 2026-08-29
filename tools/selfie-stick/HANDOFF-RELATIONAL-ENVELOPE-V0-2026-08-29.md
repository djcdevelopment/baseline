# Relational Envelope v0 handoff — 2026-08-29

## Outcome

The smallest constraint-driven architectural increment is implemented and verified.
It is intentionally not a general CAD solver: it admits one orthogonal rectangular
primary mass and one centered equal-pitch gable, keeps observations immutable, and
separates architectural inference from game compilation.

Verified revision: `11e2337c5052f7ffecb5`

Dashboard while the existing baseline server is running:

`http://127.0.0.1:8765/tools/selfie-stick/out/architectural-constraint-envelope/revisions/11e2337c5052f7ffecb5/index.html`

## What landed

- `architectural-constraint-envelope-v0.json` freezes scope, evidence authority,
  tolerances, fixtures, and the no-live-world boundary.
- `architectural-constraint-envelope-schemas-v0.json` defines the observation,
  constraint-model, solved-graph, reconciliation, and receipt contracts.
- `probe_architectural_constraint_envelope.py` implements content-addressed
  `run`, `verify`, and `serve` commands.
- `test_architectural_curriculum.py` has one focused relational-envelope scar test
  with subcases for immutable observations, explicit conflicts, view translation,
  and narrative-datum rejection.
- Every fixture emits a constraint model, solved-or-held graph, and interpretation
  receipt. Solved fixtures also emit pieces and a compilation receipt.

Pipeline boundary:

`pinned source evidence -> immutable observations -> shared envelope constraints ->`
`solved graph -> bounded reconciliation -> game-only adapter -> WebGPU proof`

## Evidence from the three fixtures

### tn0304 — positive development fixture

- The written dimensions bind the envelope at 7.953375 m by 7.467600 m.
- The section chain binds floor-to-eave at 2.222500 m and eave-to-ridge at
  3.594100 m, producing a 5.816600 m ridge and a 43.907838° roof pitch.
- The North active elevation starts with 1,862 broad roof hypotheses. Constraint
  propagation retains 88, a 95.2739% reduction. The selected hypothesis differs
  from the explicit rise by 2.503 mm.
- A view-only vertical translation brings the North roof relation within 1.669 mm.
  Source coordinates are not changed.
- The unseen South elevation starts with 2,613 hypotheses. It retains 41, a
  98.4309% reduction. Its relative vertical agreement is within 0.711 mm.
- South needs one explicit 29.171 mm horizontal ridge-centering reconciliation to
  enter the 3% evidence tolerance. The observation stays intact; the repair, reason,
  before/after values, candidate, role, and bound are recorded.
- Three tempting interpretations are rejected: a shared absolute elevation origin,
  two equal-height levels inferred from historical prose, and the legacy visual
  plan frame. Exactly one envelope hypothesis is admissible.
- Architectural floor count remains unresolved. The compiler's single ground-floor
  surface is recorded as game-only adaptation, not evidence.
- Compilation closes with 40 pieces and no hidden overlap.

### sd0401 — accepted regression control

- Main width/depth are unchanged relative to the accepted F2 oracle.
- Maximum eave/ridge deviation is 8.620 mm, under the 100 mm bound.
- The accepted F2 artifact is evaluation-only and does not feed solver features.
- Compilation remains within budget at 62 pieces.

### tn0305 — negative abstention control

- Missing width and depth remain blocking contradictions.
- Status is `HELD_INSUFFICIENT_CONSTRAINTS`.
- No footprint, roof, compilation receipt, or pieces are invented.

## Hardware and regression proof

- WebGPU adapter: Intel Xe-LPG, classified `hardware`.
- tn0304: 40 instances, 480 triangles, 3 draw calls.
- Startup: 276.8 ms (limit 1,000 ms).
- Frame p95: 16.9 ms (limit 33 ms).
- Capture: PASS; validation errors: none.
- Focused architectural suite: 15/15 PASS.
- Broad repository suite: 104/104 PASS.
- Unchanged rerun: `CACHED_VERIFIED` with owned artifact hashes rechecked.
- Network requests, downloads, OCR calls, VLM calls, and world writes: all zero.

Commands:

```powershell
& 'C:\work\venvs\steward-arch\Scripts\python.exe' tools/selfie-stick/probe_architectural_constraint_envelope.py run
& 'C:\work\venvs\steward-arch\Scripts\python.exe' tools/selfie-stick/probe_architectural_constraint_envelope.py verify
& 'C:\work\venvs\steward-arch\Scripts\python.exe' -m unittest -v test_architectural_curriculum
```

Run the architectural test command from `tools/selfie-stick`.

## Scar retained from implementation

The first run failed because it treated detected diagonal segment endpoints as roof
eaves. The segments visibly stopped short, which recreated pixel-authority behavior.
The final pass uses the explicit roof rise to predict a narrow eave band, then asks
the existing pinned Hough pass for horizontal support and intersects that datum with
the candidate slopes. This is the desired bidirectional loop:

`vision proposes slopes -> constraints predict the eave -> vision validates support`

No new detector or Hough tuning was introduced.

## Known limits and next ruthless increment

The WebGPU result is a functional prefab-envelope proxy, not a detailed expression
of the solved roof. The visual adapter still presents coarse modular roof strips and
does not communicate provenance or constraint residuals in 3D.

Do not widen this into arbitrary polygons, openings, appendages, or a cohort solver
yet. The next useful experiment is one additional adversarial rectangular-gable
fixture with a genuinely conflicting written dimension. Exercise the already-built
weighted-compromise contract and require either a <=100 mm explained solution or an
honest `HELD_CONFLICT`. If that fixture passes, the following increment should make
the game adapter consume solved pitch/ridge geometry directly before adding more
architectural topology.

No Quest/live-world files were changed, and no promotion is authorized by this R&D
result.
