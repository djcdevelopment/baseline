# AM4 exact-point 4K coverage - 2026-08-27

**Status: VERIFIED capture completion; publication DEFERRED.**

This receipt records the first series-scale exterior capture framed from exact
BUILDING ZDO membership. AM4 rendered Valheim at 3840x2160 while its physical
DP-4 output remained 1920x1080. The two accepted runs produced 240 of 240 planned
PNGs for 48 frozen ComfyEra17 structures.

The originals are captured and verified, not yet published into the Era17
gallery. The historical manual-capture source is currently parked, and rebuilding
without it could remove existing joins.

## Outcome

| run | role | builds | PNGs | local bytes | result |
|---|---|---:|---:|---:|---|
| 20260827-161109 | acceptance slice | 2 | 10 | 127,722,172 | PASS |
| 20260827-162027 | remainder | 46 | 230 | 2,321,707,993 | PASS |
| total | exact-point coverage | 48 | 240 | 2,449,430,165 | VERIFIED |

All 240 files are 3840x2160. The AM4 wrapper verified every returned file's MD5
against the remote original before merging its receipt. The remainder has exactly
230 unique indices from 0 through 229, exactly five receipts for each expected
cluster, no unexpected or missing cluster id, no filename mismatch, and zero
receipts marked occluded.

The local original directories are:

~~~text
C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\comfy-orbit-captures\20260827-161109
C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\comfy-orbit-captures\20260827-162027
~~~

The remote originals remain at:

~~~text
/home/derek/valheim/BepInEx/config/comfy-orbit-captures/20260827-161109
/home/derek/valheim/BepInEx/config/comfy-orbit-captures/20260827-162027
~~~

## Physical 1080p and 4K rendering are separate

The AM4 lane now guards both dimensions explicitly:

- Valheim/X framebuffer: 3840x2160;
- active physical output: DP-4 at 1920x1080; and
- renderer: NVIDIA GeForce RTX 5070/PCIe/SSE2.

Invoke-SelfieStick.ps1 checks the physical output during preflight and again after
the AM4 runner exits. A mismatched active output aborts the capture. Read-only
mid-run and final queries independently reproduced:

~~~text
screen=3840x2160
monitor=DP-4:1920x1080
~~~

A negative preflight that deliberately expected a physical 3840x2160 mode
aborted on the observed DP-4:1920x1080 value. Repeating with the default
1920x1080 expectation passed, proving the guard can fail and the intended state
was restored.

After both this series and a later independent capture had exited, Valheim was
idle and the same display split remained in force. Keeping the X screen at 4K
therefore did not change the monitor's required 1080p mode.

## Frozen geometry and target cohort

The run used ComfyEra17 snapshot 107 and the already-frozen cluster ids.
scan_clusters.py was not rerun and no cluster was renumbered. Here y is elevation;
photographic depth is the projection of x/y/z onto the camera axis, never the raw
z column.

| input | bytes | SHA-256 |
|---|---:|---|
| C:\work\baseline\tools\selfie-stick\out\era17\clusters.json | 2,228,707 | 3793ec99b3e674a59f2816b08b53984144a8b6969be17b65c17d27702eccc92f |
| E:\omen\steward-era17-arch\cluster-zdos.parquet | 37,258,753 | 3055aefd0b192ecdd75d734dd2ae92db0c3ec6238cc728ca2ee29d1ec9580910 |
| C:\work\baseline\tools\selfie-stick\out\era17\gallery\index.json | private | 35808f16c8dd865aa396ace82c260e9976647498876ab2e1c609c469e0a4a58c |
| C:\work\baseline\tools\selfie-stick\out\era17\coverage-xyz-4k-targets.json | 2,299 | b2f4817d01b89f8a0ac42aca35f9289a5cfdbe58c49a6d3a5011cbc36187610f |

The exact point artifact has 3,513,410 rows across all 2,204 frozen clusters and
agrees with every aggregate cluster membership count. This cohort contributes
31,087 of those rows. Every one of the 240 plan rows reports geometry_source
zdo_xyz and frames_whole_build true.

The coverage picker supplied sixty in-world, non-sky candidates from its
unrepresented-creator tier. Exact camera-space simulation rejected nine because
at least one orbit would exceed the 120 m haze cap:

~~~text
508, 1136, 970, 1137, 1577, 1511, 1017, 405, 1013
~~~

The first 48 fits were frozen. They map to 48 distinct nonzero top creator ids;
this does not imply that each cluster is single-author. If all 48 are eventually
accepted into the gallery, represented creator coverage is projected to move from
211 to 259 of 296. That remains a projection until publication. Fit reserves were
2083, 1448, and 1824.

## Plan receipts

| plan | builds | rows | max distance | bytes | SHA-256 |
|---|---:|---:|---:|---:|---|
| coverage-xyz-4k-smoke.json | 2 | 10 | 117.8 m | 7,915 | 8ab65a222fbf3d6f8d7b12eb8894275847678311610e7424c415f6146a0681fd |
| coverage-xyz-4k-smoke.tsv | 2 | 10 | 117.8 m | 989 | 111c2ba6de289e9e2cd8b633ea76e9bc9da2eb4a59fc8a1bbcb8a03a90b62107 |
| coverage-xyz-4k-remainder.json | 46 | 230 | 106.5 m | 167,759 | ca5c4f011a5a9dfc14155225e6f13a584709c68c2bbddec2f62b9de6ffe649f4 |
| coverage-xyz-4k-remainder.tsv | 46 | 230 | 106.5 m | 20,709 | 4bd4c055ef3447722914f71a6cb2fa081ecc8083fe652974d708ffd075865284 |

Across both plans, camera distance spans 17.4 to 117.8 m. The acceptance slice
used cluster 2003 as a typical compact build and cluster 1077 as the near-cap
case. All ten acceptance frames retained their target, used planned clearance,
and returned zero occlusions.

The capture DLL on AM4 matched this explicit reference:

~~~text
C:\work\_retired\comfy\handoffs\valheim-camera-proof\bin\Release\net472\ComfyCameraProof.dll
~~~

| property | value |
|---|---|
| bytes | 87,040 |
| MD5 | 4d86b4faffb5851516654887b28c2fd1 |
| SHA-256 | 9dad9118e741ff6b200cb68104a6652db8cba8b3942d0e467ce20a4cd79f69ee |

The reference path is an explicit provenance input, not a new executable default
or a product authority.

The ignored per-run provenance receipts are:

| receipt | SHA-256 |
|---|---|
| C:\work\baseline\tools\selfie-stick\out\era17\run-provenance-coverage-xyz-4k-smoke.json | 2024b6b7e04908aeb7b3e0a5b973bccd7efafcf7a847630c74fdca3894ebfa04 |
| C:\work\baseline\tools\selfie-stick\out\era17\run-provenance-coverage-xyz-4k-remainder.json | 3157a91bd696e19b478027689997a3b6c6fd3b1ad183010a8bc85656b51284d5 |

## Runtime placement and pixel audit

The remainder's clearance outcomes were:

| outcome | frames |
|---|---:|
| planned | 206 |
| lifted 8 m | 12 |
| lifted 16 m | 7 |
| lifted 26 m | 1 |
| lifted 60 m | 3 |
| swung 15 degrees and lifted 60 m | 1 |

The largest planned-to-placed displacement was 61.3 m. Despite those recoveries,
all 230 receipts report occluded false and between 523 and 2,515 pieces near the
aim point.

check_overlay.py used 184 distinct planned camera poses and sampled 24 of the 230
remainder frames. With the known rightmost 120 px excluded, it found 0.00 percent
of the image frozen and lit; the failure threshold is 0.05 percent. The smoke
slice was independently clean. Originals retain the small NET SHOW recovery tab
at the far right. The established gallery derivation crops those 120 px without
altering the originals.

All ten smoke frames and fourteen deliberately chosen remainder frames were
visually inspected. The remainder sample covered the 60 m recoveries, the 106.5 m
near-cap frame, a clean ordinary compound, the final cohort member, and all five
views of the clearest composition edge:

- cluster 713 is a clean, readable coastal compound;
- cluster 914 remains legible at 106.5 m;
- clusters 1642, 1669, and 2445 remain whole but become high, wide coverage after
  their 60 m lifts;
- cluster 1107 is a sparse gridded mountain-basin installation rather than a
  conventional house; and
- every cluster 1938 view is dominated by its dead-tree grove.

Cluster 1938 was not silently replaced after inspection. Its exact membership
contains 250 wood-wall pieces, 30 roof pieces, five placed swamp trees, and 103
glowing guck sacks. The camera therefore found a real wood structure deliberately
interleaved with dense foliage, but none of its five exterior views isolates the
house cleanly. It is valid coverage and a weak publication candidate. That is the
bounded photographic edge exposed by this lap.

## Publication is deliberately deferred

The existing gallery index still contains 2,633 images. Its configured historical
manual source is absent:

~~~text
C:\Program Files (x86)\Steam\steamapps\common\Valheim\BepInEx\config\comfy-manual-captures
~~~

The smoke command reached capture, pull-back, receipt merge, overlay analysis, and
provenance successfully, then exited nonzero only when build_valheim_index.py
encountered that missing source. The remainder therefore used -SkipFollowUp,
which skips only index/scoring work after the same capture verifications.

**BLOCKED:** do not rebuild or publish the gallery until the parked manual source
has been restored and the full historical index can be proven not to shrink.
Creator coverage remains 211 of 296 in the current gallery until then.

## Exact planning and capture commands

From C:\work\baseline, the frozen plans can be regenerated without rescanning:

~~~powershell
$targetDoc = Get-Content C:\work\baseline\tools\selfie-stick\out\era17\coverage-xyz-4k-targets.json -Raw | ConvertFrom-Json
$smokeIds = $targetDoc.smoke_cluster_ids -join ','
$remainderIds = $targetDoc.remainder_cluster_ids -join ','

python C:\work\baseline\tools\selfie-stick\plan_shots.py --clusters C:\work\baseline\tools\selfie-stick\out\era17\clusters.json --cluster-points E:\omen\steward-era17-arch\cluster-zdos.parquet --out C:\work\baseline\tools\selfie-stick\out\era17\coverage-xyz-4k-smoke.json --region in-world --cluster-ids $smokeIds --exclude-sky --max-height-m 300 --elevation 40 --margin 1.15 --max-distance 120 --aim-height 0.5 --time-of-day 0.64 --alt-shots 0 --min-clearance 3 --fires
python C:\work\baseline\tools\selfie-stick\plan_shots.py --clusters C:\work\baseline\tools\selfie-stick\out\era17\clusters.json --cluster-points E:\omen\steward-era17-arch\cluster-zdos.parquet --out C:\work\baseline\tools\selfie-stick\out\era17\coverage-xyz-4k-remainder.json --region in-world --cluster-ids $remainderIds --exclude-sky --max-height-m 300 --elevation 40 --margin 1.15 --max-distance 120 --aim-height 0.5 --time-of-day 0.64 --alt-shots 0 --min-clearance 3 --fires
~~~

The capture commands executed were:

~~~powershell
.\tools\selfie-stick\Invoke-SelfieStick.ps1 -Run coverage-xyz-4k-smoke -CaptureDllReference C:\work\_retired\comfy\handoffs\valheim-camera-proof\bin\Release\net472\ComfyCameraProof.dll -TimeoutMinutes 30
.\tools\selfie-stick\Invoke-SelfieStick.ps1 -Run coverage-xyz-4k-remainder -SkipFollowUp -CaptureDllReference C:\work\_retired\comfy\handoffs\valheim-camera-proof\bin\Release\net472\ComfyCameraProof.dll -TimeoutMinutes 90
~~~

They are execution receipts, not a reason to reshoot completed runs. The registry
will require an explicit force flag if a deliberate repeat is ever needed.

## Concurrency note

During the post-capture audit, another agent launched an independent sixteen-frame
roof-end run on AM4 as 20260827-165844. It began after this series had completed,
used a distinct run directory and receipt id, and quit normally. None of its
artifacts were pulled, merged, or counted here. A transient Valheim PID during the
audit belonged to that later run, not to a restart of 20260827-162027.

## Edge and next bounded question

The monitor/render separation and exact-point series transport are closed:
physical 1080p survives a 4K Valheim capture, and 240 planned frames return with
complete identities and receipts.

The next bounded question is publication recovery, not another broad reshoot:
restore the historical manual-capture source, prove a no-shrink gallery rebuild,
then adjudicate the 48 five-view sets. Cluster 1938 is the first explicit
composition review case. Do not change clustering, target identity, and camera
recovery in the same lap.

## Uncertainty retained

- Machine validation covered every file; visual judgment covered 24 of 240
  originals, including every smoke frame and fourteen selected remainder frames.
- A receipt's occluded false value proves the runner's ray test passed, not that
  foliage or exposure makes a strong photograph.
- ZDO positions are prefab pivots rather than render-mesh corners.
- Runtime recovery moved 24 remainder cameras and can weaken composition even
  when the target remains in frame.
- Top creator id is an attribution heuristic for a multi-author cluster, not a
  player name or sole-authorship claim.
- The 48-creator increase is not reflected in the gallery until the historical
  source is restored and publication succeeds.
- The small right-edge recovery tab remains in originals and relies on the
  existing, explicit 120 px derived-image crop.
