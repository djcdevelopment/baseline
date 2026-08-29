# Architectural Round Trip

One measured HABS building now reaches a portable, configuration-driven Valheim
candidate without losing its evidence or pretending unsupported detail exists.

The specimen is Library of Congress control `sd0401`, Cedar Pass Lodge Cabin 1-2.
The run requested `F3_INHABITABLE`; the fidelity router approved `F1_MASSING`. That
demotion is the important result: the sheets support more than the current deterministic
prefab compiler can reproduce.

## What the probe builds

```text
LOC HABS TIFFs + metadata
        ↓ content hashes, rights, source URLs
immutable evidence bundle
        ↓ three independent scale anchors
sheet calibration
        ↓ observed / inferred / authored / unresolved assertions
metric building graph (authority)
        ├─→ source-registration CSS check
        ├─→ plan / elevation / section CSS check
        └─→ fidelity router
                ↓ approved F1, omissions published
           90-piece Godbuild candidate
                ├─→ prefab-residual CSS check
                ├─→ hardware WebGPU preview
                └─→ deterministic Build Capsule
                         ↓ inline base64url / HTTP / gdoc bridge
                    Creator OS preflight
                         ↓ only after a safe active session and world transform
                    Valheim ZDOs → save extraction → CSS round trip
```

The last line was deliberately not crossed in v0. The current Creator Session is closed,
Valheim is not running, the installed and built Lab DLLs differ, and the building-local to
world transform is unresolved. No mailbox request was sent and no world was mutated.

## Result

Revision `c2e64ee9cd262dd1a660` passed:

- four of four source objects have SHA-256, source URL, media type, byte count, and rights;
- three independent plan anchors disagree by 1.03%, inside the frozen 2% gate;
- graph closure, dimensions, opening containment, roof scope, and cross-view checks pass;
- the router caps the requested F3 build at F1 and publishes every excluded surface;
- 90 pieces stay inside the 256-piece budget at physical scale 1.000;
- the largest declared major-dimension residual is 0.057 m, inside the 0.25 m gate;
- browser screenshots passed for source registration, graph projections, and prefab residual;
- Edge 151 used an Intel hardware WebGPU adapter: 90 instances, 1,080 triangles,
  282.2 ms startup, and 17.0 ms p95 across 30 benchmark frames;
- inline-base64url and HTTP resolved byte-identical 128,649-byte bundles;
- the Build Capsule SHA-256 is
  `bc94c70a3b68784f840f0b47b74f3e972492a2be4a58778cd206c47f2737a218`;
- an isolated Quest Lab fixture accepted and staged the exact 90-piece capture/blueprint pair;
- interruption after calibration and a full restart reused all three prior stages, and the
  following full rerun reused every immutable stage with zero network downloads.

The WebGPU view uses oriented prefab envelopes, not game meshes. A Valheim `wood_roof`
is intrinsically sloped, while its envelope is a box; the graph elevation remains the
roof-shape authority.

## Run it

From the Baseline root:

```powershell
python .\tools\selfie-stick\probe_architectural_roundtrip.py --stop-after calibrate
python .\tools\selfie-stick\probe_architectural_roundtrip.py
python .\tools\selfie-stick\probe_architectural_roundtrip.py
```

The first command exercises the frozen kill point. The second resumes it. The third is
the no-op determinism run. Add `--no-browser` when only structured artifacts are needed.

The current pointers are:

```text
out/architectural-roundtrip/sd0401/
  HEAD
  PREFLIGHT_HEAD
  report.json
  blobs/sha256/<content-hash>
  revisions/<revision-id>/
    evidence.json
    inventory.json
    calibration.json
    building.graph.json
    route.json
    css/{source,graph,prefab}.html
    webgpu/{index.html,scene.json,scene.bin}
    creator/{plan,manifest,...}
    capsule.json
    receipts/*.json
  exports/*.capsule.zip
  exports/*.base64url.txt
```

Revision files and stage receipts are immutable. `HEAD`, `PREFLIGHT_HEAD`, `report.json`,
and `run-state.json` are mutable pointers/observations. A source or engine change produces
a new revision instead of editing an old one.

## Coordinate contract

Three coordinate frames remain distinct:

- `source_geo` is the LOC WGS84 catalog position. It is provenance, not a placement.
- `building_local` is right-handed metric XYZ: X follows sheet-right, Y is height, and Z
  follows sheet-up. The main footprint sheet-left/lower finished-floor corner is origin.
- `valheim_world` is a named world UID plus anchor XYZ and yaw. It remains unresolved until
  Creator OS placement; the exact-placement contract rotates local XYZ about +Y and then
  translates it.

The frozen charter initially called sheet-right “east.” Source inspection showed the
HABS north arrow is oblique to the sheet, so the graph records that cardinal alias as an
invalid assumption and leaves geographic yaw unresolved.

## Give the build to another agent

The ZIP is the easiest handoff. Give the agent the bundle plus its SHA-256, or put the
bundle at an HTTP URL:

```powershell
python .\tools\selfie-stick\probe_architectural_roundtrip.py `
  --resolve .\tools\selfie-stick\out\architectural-roundtrip\sd0401\exports\habs-sd0401-c2e64ee9cd262dd1a660.capsule.zip `
  --expected-sha256 bc94c70a3b68784f840f0b47b74f3e972492a2be4a58778cd206c47f2737a218 `
  --resolve-out .\resolved-sd0401
```

The same `--resolve` argument accepts:

- `buildcapsule+base64url:<payload>` — the complete ZIP encoded inline;
- `https://.../build.capsule.zip` — raw bundle bytes, pinned by `--expected-sha256`;
- `gdoc:<document-id>` — a public/shared Google Doc whose plain-text export contains one
  `buildcapsule+base64url:` string.

The inline and HTTP paths are verified. The Google Doc bridge is implemented but remains
`UNVERIFIED_NO_REMOTE_DOCUMENT` because no shared document was supplied. Google is only a
transport connector: the capsule bytes and SHA-256 remain authoritative.

After extraction, another agent starts with `capsule.json`, follows `entrypoints.graph`
for source-of-truth geometry or `entrypoints.creator_plan` for the candidate pieces, and
must honor `route.published_omissions`. The package contains no machine-specific absolute
paths.

## Why it stopped at F1

The measured sheets support an F2 weather shell and much of F3. The compiler does not yet
earn those labels because:

- secondary roof junctions are observed but not normalized into buildable roof planes;
- openings are located but not segmented into traversable Valheim wall bays;
- interior partitions are visible but insufficiently dimensioned for deterministic piece
  placement;
- jamb, paneling, and crown profiles have no target vocabulary mapping.

The F1 candidate preserves the measured physical scale, distributes overlap rather than
warping the building, and places exterior wall pivots inward by their known 0.4274 m
thickness so the exterior faces—not the pivots—match the source footprint.

That narrow follow-on experiment is now complete. It promoted the same frozen specimen to
F2 without changing the source evidence or calibration; the result is recorded below.
Only after a separately safe Creator Session should it be built, extracted as ZDO
XYZ/quaternions, and compared back against this graph.

## F2 follow-on — opening-aware weather shell

The frozen contract in `architectural-roundtrip-f2.json` inherited v0 revision
`c2e64ee9cd262dd1a660` byte-for-byte. It allowed promotion only if real exterior wall bays
replaced solid-wall opening proxies, the main/vestibule/mechanical roofs were explicit
planes, the shell stayed within 256 pieces, and interruption/transport/Creator contract
checks still passed.

```text
accepted v0 graph + immutable evidence
        ↓ opening inventory and target-module adaptations
exterior wall interval compiler
        ↓ wall bodies stop at doors and windows
18 compiled openings + one published target conflict
        ↓ explicit 26° / 45° / inferred 26° roof planes
F2 metric graph
        ├──→ opening-bay CSS receipt
        ├──→ roof-plane CSS receipt
        └──→ hardware WebGPU preview
                 ↓ fidelity gates
            250-piece F2 weather shell
                 ↓ deterministic package + isolated Creator fixture
            portable Build Capsule
```

Revision `3d7189c1c6641f19f873` passed all 14 frozen F2 gates:

- 18 of 19 source openings compile (94.7% recall): 3 doors and 15 windows;
- opening centers remain source-registered at 0.000 m error, wall bodies intrude 0.000 m,
  and the largest unfilled solid interval is 0.010 m;
- all 18 module-width adaptations are explicit;
- the omitted vestibule east door remains published because the target door swing envelope
  cannot fit its 1.378 m host wall;
- six roof planes replace every flat placeholder, cover 100% of their plan footprints, and
  overlap both appendage joins with zero computed gap;
- the main ridge differs by 0.026 m, the vestibule eave by 0.083 m, the largest secondary
  overhang is 0.588 m, and the largest declared weather seam is 0.045 m;
- the physical-scale candidate contains 250 pieces, six below the frozen budget;
- Edge 151 used the Intel hardware WebGPU adapter for 250 instances / 3,000 triangles:
  332.2 ms startup and 17.7 ms p95 over 30 benchmark frames, with no validation errors;
- the isolated Creator fixture accepted and hash-preserved the exact blueprint/capture pair;
- the 143,248-byte, 25-member capsule has SHA-256
  `0630fcdec4e99c05fa38c42aacdd98d8a9c2dab40affbf8ca97240d4f83fa034`;
- inline base64url and HTTP resolution returned identical bytes, and a separate local
  resolver/extraction smoke test verified all packaged member hashes;
- the process stopped after `openings`, resumed with both earlier stages cached, and the
  following run cached every immutable stage. Only the live-state preflight was re-observed.

Run the F2 lap from the Baseline root:

```powershell
python .\tools\selfie-stick\probe_architectural_roundtrip_f2.py --stop-after openings
python .\tools\selfie-stick\probe_architectural_roundtrip_f2.py
python .\tools\selfie-stick\probe_architectural_roundtrip_f2.py
```

The accepted output is under
`out/architectural-roundtrip-f2/sd0401/revisions/3d7189c1c6641f19f873/`.
`building.graph.f2.json` remains geometry authority; `opening-compilation.json`,
`roof-compilation.json`, and `route.json` explain the promotion. The WebGPU view still
renders oriented prefab envelopes rather than Valheim meshes.

Live placement remains blocked safely: there is no active Creator Session or Valheim
process, the built and installed Lab DLL hashes differ, and the world anchor/yaw is
unresolved. No request was sent and no world was mutated. The next earned fidelity edge
is F3, specifically dimensioned interior partitions plus a room/traversal graph; live ZDO
round-trip validation remains a separate session-safety edge.
