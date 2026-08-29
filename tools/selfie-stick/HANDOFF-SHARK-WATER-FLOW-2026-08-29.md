# Shark-mode water-flow handoff — 2026-08-29

## Outcome

The bounded automatic lane is flowing, but this pass did **not** earn promotion or
retain a live build.

- `tn0304` ran from pinned source raster through cutline, dimensions, provisional
  graph, 72-piece compilation, and hardware WebGPU capture.
- The automatic sentinel is `WATER_FLOWING_PROVISIONAL`; verification is `PASS` and
  promotion is `NONE` because the different-sheet North-elevation CSS residual is
  still `FAIL`.
- A separate immutable `sd0401` F2 derivative placed all 250 pieces in Valheim and
  returned the exact prefab census, but the mandatory live spatial diff failed
  `missing 67, extra 67`.
- The fail-closed branch ran immediately: BuildOff, graceful Stop, then exact world,
  FWL, and character rollback. The authored build therefore is **not retained**.
- Offline diagnosis isolated and fixed a half-turn quaternion canonicalization seam.
  There was no same-session live retry.

## Automatic source-to-visible result

Authoritative result:

`C:\work\baseline\tools\selfie-stick\out\architectural-water-flow\tn0304\result.json`

Visible dashboard:

`C:\work\baseline\tools\selfie-stick\out\architectural-water-flow\tn0304\dashboard.html`

Pinned inputs and result:

- Upstream v3 revision: `5333d5eaed593d7607e4`
- Native sheet SHA-256:
  `fcc3592829debfb3f9db14223be82cf78b33f46ef15063970875088616bae119`
- Cutline: paired `W-W` OCR markers plus source-pinned Hough segments, axis `z`, PASS
- Width: `26'-1 1/8"` = `7.953375 m`
- Depth: `24'-6"` = `7.4676 m`
- Eave: `7'-3 1/2"` = `2.2225 m`
- Roof rise: `11'-9 1/2"` = `3.5941 m`
- Calculated ridge: `5.8166 m`
- Compiled scene: 72 pieces
- Browser: Intel hardware WebGPU, capture PASS, p95 `16.8 ms`
- Held-out North elevation residual: FAIL

Important correction: the source-backed depth is `24'-6"`, not `24'-8"`. Native
rotated OCR and an independent normalized view agree on the numeric atoms. The runner
records `24'-8"` as `REJECTED_NO_NATIVE_OR_NORMALIZED_OCR_SUPPORT`; no authoritative
dimension was hardcoded. See `dimension-evidence.json` beside the result.

## Immutable live input

This is deliberately separate from the provisional `tn0304` output.

- Accepted F2 HEAD: `3d7189c1c6641f19f873`
- Source folder:
  `C:\work\baseline\tools\selfie-stick\out\architectural-roundtrip-f2\sd0401\revisions\3d7189c1c6641f19f873\creator`
- Explicit derivative: `habs-sd0401-f2-liveproof-r0`
- Transform: bake `+90 degrees`; request live placement at yaw `0`
- Piece count: 250 across nine prefabs
- Pieces SHA-256:
  `f7cbc42ac80bd7cae8876bb58fe38091fdb6a8f29e6b3bd820ce5271d71a993a`
- Capture SHA-256:
  `971a3620d100c2435e345926d2a704bb980d4eb71f2e59515f10a1a8c7cd7669`
- Blueprint SHA-256:
  `93a31986efba9f2e74e362b92e4a0ae28aa0c26cb4e9f89e180def48c7b57761`
- Inverse proof: 250/250; maximum position-component error
  `1.7763568394002505e-15 m`; quaternion error `0`

Offline boundary receipt:

`C:\work\baseline\tools\selfie-stick\out\live-spatial-revision-sd0401-f2\live-boundary.json`

Canonical artifacts:

`C:\work\baseline\tools\selfie-stick\out\live-spatial-revision-sd0401-f2\canonical\habs-sd0401-f2-liveproof-r0`

The normal importer still rejects the architectural source sidecar. Derivation requires
the explicit architectural-name and yaw options, then re-enters the normal importer
validation path.

## Live lap and receipts

Creator Session: `arch-water-20260828-r0`

The stale proposed site near `(233.52, 31.12, -146.88)` was rejected after Prepare
showed the current character logout at `(5.62972069, 61.80255, 0.07770743)`, inside the
existing tower. An all-category world export selected a clear vertical shelf instead:

- Build-at corner: `(1.493071, 70.5, -7.786793)`, yaw `0`
- Maximum canonical-pivot distance from the player: `13.436889 m` (under `24 m`)
- Existing ZDOs in the padded proof footprint: zero

Gate receipts live under:

`C:\work\baseline\tools\selfie-stick\out\live-spatial-revision-sd0401-f2\live`

Observed sequence:

1. Blueprint check completed: 250 buildable pieces, nine prefabs, exact pieces hash.
2. Pre-count completed: no blueprint-built pieces in the loaded area.
3. Build authority enabled through Creator Session.
4. `last-live-receipt.json` completed with
   `placed=250 failed=0 x=1.493071 y=70.5 z=-7.786793 yaw=0`.
5. Post-count completed with exactly 250 standing and this exact census:
   `wood_beam=32`, `wood_door=3`, `wood_floor=32`, `wood_pole2=65`,
   `wood_roof=38`, `wood_roof_45=2`, `wood_wall_quarter=59`,
   `wood_window=15`, `woodwall=4`.
6. Spatial diff receipt
   `04-diff\blueprint-diff-20260829T065749Z-40f0885b-receipt.json` completed
   `DIFFERENT — expected 250, selected 250, missing 67, extra 67`.

The diff was the mandatory gate, so stopped-world export and live persistence
verification were correctly not claimed.

## The scar exposed by live execution

Exactly 67 derivative pieces have authored quaternion `(0,1,0,0)`, a 180-degree yaw.
The 67/67 diff cardinality covers exactly those pieces across eight prefab families.
The first eight receipt examples are members of that set.

The importer rounded normalized quaternion components to signature precision before
choosing the `q/-q` representative. The C# live contract chose the representative
first. Valheim's ZDO Euler round trip reconstructs an exact half-turn with approximately
`W=-4.371139e-8`; the old live order therefore flipped `(0,1,0,epsilon)` to
`(0,-1,0,0)` after rounding.

The narrow correction is in:

- `C:\work\comfy-quest\network\mod\ComfyQuestLab\Core\LabCaptureContract.cs`
- `C:\work\comfy-quest\network\mod\ComfyQuestLab.Tests\LabCaptureContractTests.cs`

The C# contract now rounds to its retained six-digit precision before hemisphere
selection, matching the authoritative importer. The single new regression is the scar
for a ZDO-round-tripped half-turn; it is not a new test layer. Offline reconstruction
produced `old_mismatches=67` and `new_mismatches=0`. The accepted 250-piece derivative
regenerated byte-identically.

The copied `04-diff\*-capture.json` is the staged expected sidecar, not a dump of the
selected live transforms. Do not mislabel it as direct live-field evidence.

## Rollback and current machine state

- BuildOff receipt:
  `C:\work\comfy-quest\captures\creator-session\arch-water-20260828-r0\20260829T065917Z-buildoff`
- Graceful Stop receipt:
  `C:\work\comfy-quest\captures\creator-session\arch-water-20260828-r0\20260829T065921Z-stop`
- Exact Close/restore receipt:
  `C:\work\comfy-quest\captures\creator-session\arch-water-20260828-r0\20260829T065934Z-close`

Stop was graceful, forced no process, and quarantined no partial save. Close reports
`restored_world_entry_state=true` and `restored_game_state=true`. Current hashes match
the pre-lap backups:

- `ComfyQuestDemo.db`: 3,130,909 bytes,
  `c4b0edd8edc38e33696a98951f393b5d6b06da6614dcd3948a3d6bae51ad1906`
- `ComfyQuestDemo.fwl`: 57 bytes,
  `645b126df278c057429ac9f06509fabd9513f1289cb9937466c9be8f402e8ad5`
- Steam `questyfour.fch`: 19,626 bytes,
  `6657933077a6c11fd63803878ae8416ed3296032758274220cbbc4f093a52f76`

Valheim is absent and Creator Session Status refuses because there is no active
session. The exact derivative pair remains staged in the Lab blueprint directory with
the hashes above; there are no retained live pieces to inspect or clear.

## Verification already paid for

- Architecture curriculum: 14/14 PASS
- Baseline broad discovery: 104/104 PASS
- Quest broad Python discovery: 391/391 PASS
- Total broad Python: 495/495 PASS
- Lab capture contract after the seam fix: 10/10 PASS
- Godbuild importer: 3/3 PASS
- Production `ComfyQuestLab` build: 0 warnings, 0 errors
- Both repositories: `git diff --check` PASS
- Saved-world verifier: exact synthetic 250-row export PASS; 3 mm drift FAIL closed

Do not rerun the 28-building cohort or add generalized test infrastructure before the
next live question requires it.

## Ruthless next steps

1. In a fresh Creator Session, prove only a four-piece `0/90/180/270` rotation ladder
   and retain its normalized observed signatures. Require spatial diff
   `missing=0, extra=0`.
2. Only after that seam is green, rerun the immutable 250-piece derivative once at a
   freshly exported clear site. Do not reuse the stale coordinates blindly.
3. Require all of: check, zero pre-count, `placed=250 failed=0`, exact prefab census,
   spatial diff `0/0`, graceful Stop, and saved-world verifier PASS.
4. Retain the build only after the stopped-save proof passes. Otherwise run the same
   pinned `Close -Restore -RestoreGameState` branch with no mutation retry.
5. For the automatic lane, attack the failed different-sheet CSS residual by improving
   the pre-CSS graph/registration evidence. Do not loosen CSS thresholds to manufacture
   green.
6. Keep `tn0305` as the one checked negative. Do not pay for the full cohort until the
   first held-out residual or live persistence proof changes the R&D decision.

No promotion is justified yet: automatic water is visible, the live failure produced a
specific upstream scar, rollback proved safe, and the next experiment is smaller than
the failed 250-piece proof.
