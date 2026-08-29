# Automatic HABS architectural curriculum

This is the 20-building transfer experiment after the single-building
architectural-roundtrip probes. It asks whether one automatic pipeline can move from
measured Library of Congress drawings to a provenance-bearing metric graph and a generic
Valheim weather-shell candidate across the frozen corpus—and whether mechanically accepted
earlier examples improve later buildings.

The experiment charter was frozen before implementation in
[`architectural-curriculum-v1.json`](architectural-curriculum-v1.json). The machine-readable
artifact contracts are in
[`architectural-curriculum-schemas-v1.json`](architectural-curriculum-schemas-v1.json).

## Current answer

The orchestration, persistence, curriculum, compiler, CSS/WebGPU views, lesson regression
guard, capsules, and verification paths work across all 20 records in the deterministic
fixture lane. That lane is deliberately watermarked `SIMULATION_NOT_EVIDENCE`; it proves
the experiment machinery, not drawing interpretation or architectural fidelity.

The latest fixture revision rendered all browser scenes, but its frozen largest-candidate
hardware benchmark failed: headless Edge returned no WebGPU adapter on all three attempts.
That failure is visible on the dashboard and blocks the rendering gate; a successful PNG
capture of the error state is not mistaken for a GPU pass.

The real lane currently stops in preflight because the pinned local
`qwen2.5vl:7b` endpoint is unavailable. The corpus and pinned RapidOCR/ONNX environment
pass. The runner does not substitute fixture geometry, a cloud model, catalog titles, or
hand-authored dimensions when the vision dependency is absent.

No command in this experiment contacts Valheim, writes a Creator OS inbox request, or
creates a ZDO.

## Real-data OCR/CV audit

The VLM boundary is still blocked, so the numeric lane was tested independently instead
of waiting for it. [`architectural-ocr-audit-v1.json`](architectural-ocr-audit-v1.json)
froze a smaller question before the corpus run: can the pinned, real RapidOCR/OpenCV lane
recover enough grounded signals to constrain later semantics without claiming autonomous
scale? `probe_habs_ocr_audit.py` runs that question over all 69 sheets with no VLM,
network request, catalog-title numeric authority, Valheim contact, or world mutation.

Revision `017d196e9584e4c0aa98` passes all six frozen gates. It recovered 4,834 OCR tokens,
214 strict local dimension candidates, and 227 held dimension-like strings. All 69 sheets
produced at least ten tokens; 37/69 contain a strict dimension and a nearby CV line
candidate; 67/69 contain an OCR role signal; median token confidence is 0.9875. The result
is `USABLE_TO_CONSTRAIN_SEMANTICS`, always paired with
`NOT_AUTONOMOUS_SCALE_AUTHORITY`.

The six-cluster pre-sort proved materially useful. C02 isolates a total strict-parse
failure (0/2 sheets) while correctly holding its scale-label notation. C01 carries 146 of
the 214 strict candidates. C04 is sparse and error-prone: its deterministic three-signal
review found only one correct numeric transcription, while C00, C01, C03, and C05 were
3/3. This is enough to route C04 through stricter redundancy checks instead of applying
one global confidence threshold.

The deterministic visual board contains three signals per cluster. Manual comparison to
the normalized source sheets found 13/15 strict parses to be correct local dimensions
(86.7%) and all 3/3 held scale controls to be correctly rejected. Neither number promotes
a value to building width, depth, or height: the two errors are a split compound door
dimension and an inch mark read as a foot mark, both at respectable OCR confidence. The
full adjudication and its limitations are frozen in
[`architectural-ocr-review-v1.json`](architectural-ocr-review-v1.json).

The review loop also removed real parser defects before this result was frozen: scale
legends and sheet references masquerading as metric values, lumber sizes masquerading as
feet, ordinal suffixes, scale fragments joined to author credits, and greedy OCR windows
whose evidence boxes sprawled across a sheet. Multi-token recovery now requires the
dimension to begin in the first token, preserving split notation while keeping local
evidence local.

Run and inspect the audit:

```powershell
$python = 'tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
& $python tools\selfie-stick\probe_habs_ocr_audit.py run
& $python tools\selfie-stick\probe_habs_ocr_audit.py verify
& $python tools\selfie-stick\probe_habs_ocr_audit.py serve --port 8877
```

The first corrected-parser run reused all 69 immutable OCR artifacts and made zero OCR
calls. A following unchanged run validates and caches all 69 sheet stages. This separates
expensive perception bytes from evolving parsers without treating stale derived facts as
current.

## Workflow

```text
69 frozen LOC master drawings
            │ verify bytes + hashes
            ▼
  lesson-free baseline for all 20
  normalize → OCR numbers → VLM semantics → deterministic gates
            │
            ├── size / height / floor features
            ▼
 deterministic clustering + outward Pareto curriculum
            │
            ▼
 seed control, then 19 unseen buildings
            │ retrieve ≤3 accepted nearby examples
            ├───────────────┬────────────────────┐
            ▼               ▼                    │
     baseline candidate  cumulative candidate    │
            └──── gate-by-gate comparison ───────┘
                            │ regression: retain baseline
                            ▼
 metric graph → generic pieces → CSS + WebGPU → capsule
                            │
                            ▼
 cumulative lesson layer + dashboard + deterministic catalog
```

Every building is perceived lesson-free before clustering. That is both the bootstrap
input and the control arm. During curriculum execution, the same building is assessed
with the nearest accepted lesson examples. A cumulative candidate can be selected only
when it loses none of the baseline's passing gates. Advancement means a higher promotion
level or fewer unresolved assertions. A fixture result cannot demonstrate learning.

## Promotion levels

| Level | Automatic claim |
| --- | --- |
| `A0_TRIAGED` | At least one plan and one elevation/section panel classified |
| `G1_METRIC_GRAPH` | OCR-backed width, depth, height, floor count, scale consistency, and cross-view gates pass |
| `F1_MASSING` | A physical-scale, non-stretched generic piece composition fits the 256-piece budget |
| `F2_WEATHER_SHELL` | F1 plus an explicit supported roof, at least one door, and at least two windows |

The graph separates source/catalog coordinates, building-local metric coordinates, and
the unresolved future Valheim-world transform. Unsupported measurements remain
`unresolved`; they are never silently defaulted into a promoted graph.

## Run it

Create the ignored, reproducible local runtime once:

```powershell
Set-Location C:\work\baseline
python -m venv tools\selfie-stick\out\architectural-curriculum\runtime-venv
tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe `
  -m pip install -r tools\selfie-stick\requirements-architectural-curriculum.txt
```

Real preflight and run:

```powershell
$python = 'tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'
& $python tools\selfie-stick\probe_architectural_curriculum.py preflight
& $python tools\selfie-stick\probe_architectural_curriculum.py run
& $python tools\selfie-stick\probe_architectural_curriculum.py verify
```

The real run exits blocked before OCR/VLM work unless the exact configured local model is
available. `COMFY_OLLAMA` can point at an already managed compatible endpoint. The runner
does not start or replace Ollama.

Exercise the infrastructure without making an evidence claim:

```powershell
python tools\selfie-stick\probe_architectural_curriculum.py run `
  --fixture-vision `
  --out tools\selfie-stick\out\architectural-curriculum\habs-v1-fixture
python tools\selfie-stick\probe_architectural_curriculum.py verify `
  --fixture-vision `
  --out tools\selfie-stick\out\architectural-curriculum\habs-v1-fixture
python tools\selfie-stick\probe_architectural_curriculum.py serve `
  --fixture-vision `
  --out tools\selfie-stick\out\architectural-curriculum\habs-v1-fixture `
  --port 8876
```

Use `--no-browser` only for a diagnostic run. A promotable real result must benchmark the
largest promoted candidate on a hardware WebGPU adapter within the frozen startup and
frame-time limits.

## Persistence and artifact layout

The revision identity hashes the runner, charter, selection, schemas, requirements,
reused WebGPU runtime, source manifests, exact Python/packages/ONNX models, pinned vision
model digest, browser executable, mode, and diagnostic scope.

```text
out/architectural-curriculum/habs-v1/
  HEAD
  preflight.json
  report.json
  verification.json
  revisions/<content-id>/
    identity.json
    preflight.json
    bootstrap.json
    index.json
    index.html
    receipts/
      bootstrap-<building>.json
      building-<building>.json
    lessons/
      layer-00.json
      ...
    buildings/<building>/
      baseline.json
      assessment.json
      building.graph.json
      pieces.json
      normalized/*.png
      css/*.html
      webgpu/{index.html,scene.json,scene.bin,browser-receipt.json,...}
      capsule.json
      building.capsule.zip
  exports/
    architectural-curriculum-<content-id>.capsule.zip
```

Receipts contain input fingerprints and every output hash. An unchanged rerun validates
those hashes and performs zero OCR calls, zero VLM calls, and zero downloads. Corrupt or
missing output bytes invalidate only the owning stage. Lesson packs form a SHA-256 chain.
Building and catalog capsules intentionally exclude the 127.7 MB source TIFF corpus;
per-building capsules include normalized PNG evidence so their CSS views remain portable,
while source hashes and LOC URLs preserve provenance without duplicating masters. The
catalog nests those deterministic building capsules and the complete lesson chain.

## What a success means

The frozen ladder counts only 19 unseen buildings. Minimum architectural transfer is 12
G1, 8 F1, and 3 F2 buildings across multiple building types; strong and wild tiers demand
more. Promotion additionally requires measured learning with zero prior-gate regressions
and the largest-candidate hardware WebGPU gate. Fixture counts never satisfy these gates.

Even a wild result remains a non-live architectural-import candidate. Live placement,
terrain anchoring, ZDO creation, save extraction, and round-trip comparison are separate
safe-session experiments.
