# Handoff - automatic HABS frame registration v3

Resume in `C:\work\baseline`. Read the root `AGENTS.md` first. Preserve the dirty
worktree and every v0/v1/v2 source and artifact; do not reset, clean, commit, push,
seal, or run the v3 blind phase unless a later experiment actually earns that action.

## Current result

V3 is implemented and development-verified. Its scientific development gate failed,
so it is intentionally unsealed and the replacement fitter holdout was not run.

- Acquisition guard: `habs_harvester.py plan` plus `harvest --plan`
- Replacement selection: `habs-corpus-v3-holdout.json`
- Frozen acquisition plan: `habs-corpus-v3-acquisition-plan.json`
- Acquisition-plan SHA-256: `3fa84fbd64bf72489e13c742ecf20e9932cb1c293eea1b244d4ef2f137a3dc51`
- Replacement corpus: 8 buildings, 29 sheets, 123,099,962 verified bytes
- Replacement OCR revision: `315ba9abcf599f639fa7` (`PASS`)
- V3 charter/contracts: `architectural-css-fit-v3.json`, `architectural-css-fit-schemas-v3.json`
- V3 runner: `probe_architectural_css_fit_v3.py`
- Pinned v2 diagnostic baseline revision: `7331f32e25b034d03d70`
- V3 development revision: `5333d5eaed593d7607e4`
- Artifact verification: `PASS`
- Scientific development acceptance: `FAIL`
- Development lock: absent
- Blind seal/index: absent
- Replacement buildings processed by fitter: 0 of 8

The replacement selection was frozen before its rasters were downloaded or OCR was
run. It has two cabins, two barns, two farmhouses, two houses, seven states, and exactly
two wholly generic catalog-caption controls (`tx0519`, `ma0678`). The first hash-ranked
barn, `mt0670`, was rejected by the new HTTP-sized guard: 829,478,514 bytes exceeded the
805,306,368-byte building limit. The final 29-sheet plan is well below the 2 GiB total
budget and was harvested only from its exact URLs and `Content-Length` values.

## What v3 proved

The v2 diagnostic baseline was run unchanged across the original 20 plus the retired
eight. It retained the known v2 result and exposed one additional validated G1
(`md2171`) plus one G1-unvalidated candidate (`tx1238`) in the retired set.

V3 then emitted automatic hypotheses for every closed plan mass and every vertical roof
pair. It derived plan x/z spans only from independently calibrated plan frames, reserved
a distinct calibrated vertical view before constructing candidates, and preserved all
165 plan/vertical candidates. Registration used no weights, proximity score, manual label,
or scale-ratio equality. A candidate had to pass all seven frozen gates, and exactly one
passing candidate was required.

The regression and retained-capability checks all passed exactly:

| Development check | Actual | Required |
|---|---:|---:|
| Original failure cohort: selected primary mass | 8 | 8 |
| Original failure cohort: scale consensus | 6 | 6 |
| Original failure cohort: calibrated roof pair | 7 | 7 |
| Original failure cohort: validated G1 | 0 | 2 |
| `tn0305` and `il0180` remain unpromoted | yes | yes |
| Fit-time network/OCR/VLM/download/world work | 0 | 0 |

The exact `sd0401` dimensions, `tx1037` ceiling vocabulary, and `ak0535` separate
LOG CABIN/ADDITION masses also remain unchanged. The cached rerun reports 28 cached,
zero executed, and zero evidence/topology/CSS work.

The bounded failure is cross-sheet correspondence, not CSS. Across development, v3
emitted 127 frame hypotheses and 165 candidates; every candidate was rejected because
no selected plan frame and different-sheet vertical frame shared an exact OCR section
marker. The two nearest original-cohort cases were:

- `tn0304`: 5/7 gates pass. Its cross-sheet elevation matches the plan depth within
  0.129833 m (1.4169%) but has neither an exact section marker nor a matching origin.
- `tn0305`: 5/7 gates pass. Its cross-sheet elevation matches the plan width within
  0.247305 m (2.1229%) but has neither an exact section marker nor a matching origin.

Same-sheet sections do contain exact markers (`W-W` and `E-E`), but accepting them would
violate the frozen different-sheet gate. Elevations on the other sheets have compatible
metric spans but no exact section markers. Do not turn direction labels into section
markers, infer an origin merely to pass, lower the two-G1 gate, or expose the replacement
holdout. Those would erase the causal result.

## Exact cached commands

```powershell
Set-Location C:\work\baseline
$python = '.\tools\selfie-stick\out\architectural-curriculum\runtime-venv\Scripts\python.exe'

# Acquisition integrity.
python .\tools\selfie-stick\habs_harvester.py verify `
  --output .\tools\selfie-stick\out\loc-habs-v3-holdout\corpus `
  --expected-buildings 8

# Replacement OCR integrity and zero-work cache contract.
& $python .\tools\selfie-stick\probe_habs_ocr_audit.py verify `
  --charter .\tools\selfie-stick\architectural-ocr-audit-v3-holdout.json `
  --source-charter .\tools\selfie-stick\architectural-curriculum-v3-holdout-source.json `
  --selection .\tools\selfie-stick\habs-corpus-v3-holdout.json `
  --corpus .\tools\selfie-stick\out\loc-habs-v3-holdout\corpus `
  --out .\tools\selfie-stick\out\architectural-curriculum\real-ocr-audit-v3-holdout

# Pinned v2 diagnostic and v3 development are fully cached.
& $python .\tools\selfie-stick\probe_architectural_css_fit_v3.py baseline
& $python .\tools\selfie-stick\probe_architectural_css_fit_v3.py develop  # expected exit 1
& $python .\tools\selfie-stick\probe_architectural_css_fit_v3.py verify # expected PASS/BLOCKED
```

Do not run `develop --seal` or `blind`: the first must refuse and the second has not
been earned. The next experiment should improve automatic cut-line/section-marker
recovery upstream of registration, while keeping the current replacement eight blind
to the fitter. A good next diagnostic is geometric cut-line detection anchored by OCR
section bubbles on the plan sheet, tested first on the existing 28 only.
