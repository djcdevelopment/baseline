# Gallery capture composer work ledger

Recorded 2026-09-15 UTC. The requested artifact is a reviewable shared gallery/Creator
photography workspace and a portable SelfieStick capture download, with real archived
world proof on OMEN and AM4. No wall-clock or spending limit was specified. Work began
at 09:05 UTC; setup used the existing JDK, .NET, browser, Valheim installs and archive.

## Implementation and ownership

- **Steward:** one shared capture bar, camera model, Lens/Outside views, geometry
  position/aim controls, yellow projection, reference thumbnail and live preview.
  Versioned catalog, matching archived scene, detail and deterministic download endpoints.
- **Quest Studio:** Capture mode consumes a byte/hash-pinned Steward artifact. Its
  token-gated proxy returns the same exported ZIP; gameplay targeting retains its own
  authoring limits and world-session proof.
- **SelfieStick:** `selfiestick-capture/v1`, exact lens placement, vertical FOV, requested
  RenderTexture dimensions, optional legacy shot columns, pinned portable runner,
  strict disposable local save identity and restoration receipts.
- **Baseline:** repository map, this ledger and the HEARTH build receipt. Baseline's
  in-progress camera-kit files were preserved; their explicit source snapshot was
  transferred into SelfieStick with provenance.

The owning implementation notes are `docs/gallery-capture-composer.md` in
ComfyStewardView and `docs/gallery-capture.md` in SelfieStick and comfy-quest.
The machine-readable [candidate evidence index](gallery-capture-20260915.json) records
artifact hashes, source bases, test results and local proof paths.

## Evidence and practical limits

**VERIFIED:** analytic and shared camera fixtures, 83-photo archive projection, real
WebGPU controls, geometry aiming/dragging, keyboard editing, independent observer,
resize, repeated view switches, reset, unavailable metadata/WebGPU, Studio authorization,
and byte-equivalent exports from the gallery and Studio. Game proof measures requested
versus actual lens, angles, FOV, PNG dimensions, image hashes and restoration on both
machines. The final evidence index identifies the accepted candidate and each receipt.

The scene preview renders archived piece boxes. It estimates coverage; it does not
reproduce terrain, vegetation, weather or game shading. Users supply the exact archive
world, local Valheim/BepInEx client and character. Results remain local. Video, panorama,
fisheye, physical aperture and cross-world application remain out of scope.

Candidates include working changes, explicitly marked as candidates and pinned by
bytes/hash. They are not published clean-revision releases. Public deployment was not
changed. The local candidate server enables downloads only after validating the exact
runner, per-case measured receipts, PNG hashes and restored local save identity.

## Initial save-isolation failure — capture-only disposition resolved

The first OMEN 0.3.0 runs assumed `-savedir` selected the client save directory. The
client ignored it, and legacy boot fallback selected cloud **Questy** and the existing
local **ComfyEra11**. The game saved both. Initial claims that restoration passed were
wrong: the checks covered the supplied archive and character, not the actual selections.

Questy was 35,705 bytes before capture and 44,868 bytes afterward; the second run also
overwrote `.old`. Several world chunks and the current save manifest changed. Post-run
copies and logs are preserved in SelfieStick's `artifacts/incident-omen-20260915/`.
No exact pre-run Questy backup was found. Derek confirmed that Questy is capture-only;
its post-run save remains in place, matches the preserved copy, and needs no rollback.
No older backup has been restored. Derek also confirmed that the existing local
ComfyEra11 world is capture-only. It matches its preserved post-run files and remains
in place. Only an older flat archive backup was found, not an exact pre-run copy. The
[disposition addendum](save-incident-disposition-20260915.json)
records both owner decisions. This resolves the recovery disposition, while the first
r1 restoration claim remains invalid and the original writes were not reversed.

The r1 proof is explicitly invalidated and cannot authorize downloads. Version 0.3.1
requires exact unique local character/world filenames before world entry, isolates the
real save discovery path, and compares the actual original save tree and Steam character
mirrors before and after. Subsequent successful restoration does not erase the incident.

## Recovery and accounting

The first useful camera contract/plugin and shared UI artifacts were implemented in the
owning repositories. A small HEARTH extraction request failed immediately with
`WinError10061`; work continued directly with no model swap or retry loop. Receipt
`br-20260915-090614-e56e7bbe` records that failure and the validation evidence. There was
no successful delegated model output to credit.

Real tests exposed the ignored save path, then temporal motion blur in a rotated still.
The corrected still path clears history and restores the prior motion-blur setting.
The first final AM4 launch raced Steam sign-in and reported `SteamAPI_Init() failed`;
it was stopped early with restoration verified, then repeated after Steam logged in.
Failures and superseded candidate evidence are retained separately from accepted proof.
The final cleanup and test status are recorded in the evidence index. No pushes or
public deployments were performed by this implementation session. A concurrent session
committed earlier SelfieStick work as `47b311c9ba2c6d44399538396bc800c2d7ad2b9c`; it was
preserved and is not attributed to this agent.

## Source and documentation landing

On 2026-09-15 the owner repositories were committed and pushed on `main` as
SelfieStick `7bf5ae7752c1a49540c6438d36fd8f50448229aa`, Steward
`2a9197d5bd45124aa4a91982a859669ac8cd0bd3`, and comfy-quest
`85cbb2a7cc8527635fc8606b9c838000e2c540c3`. This Baseline cut records the
user path, rationale, release plan and retrospective. Quest's staged patch matched
the tested clean worktree byte-for-byte; unrelated dirty compatibility changes were
left unstaged. The historical candidate proofs above remain local-candidate evidence.

Hub checks passed: 104 unit tests, eight corpus tests, 13 corpus outputs matched,
entrypoint links and diff checks. Steward's analytic camera test passed six fixtures;
SelfieStick's seven Python tests and CameraProof build passed; Quest's Studio 149 tests,
Python 455 tests (one local-capsule skip), Lab 385 tests, generator drift, identity,
boundary and full-history secret scan passed. The separate Quest Lab and Runtime
game-plugin builds remain **BLOCKED** against the local Valheim 1.0.12 assemblies by
older `main` game API calls. They must pass before a full Quest package release.
