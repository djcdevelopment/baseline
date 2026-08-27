# Clean motion capture R&D — 2026-08-27

This is the durable selfie-stick receipt for the cluster 504 motion experiment.
The longer narrative remains in
[`../../docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md`](../../docs/internal/RUNBOOK-selfie-stick-era17-series-2026-08-22.md),
under "R&D lap: clean 2 m motion at cluster 504".

## Outcome

**VERIFIED:** one publish-safe 1080p motion artifact exists on AM4:

`/home/derek/valheim-capture/clips/20260827-135453/0504_stormtwil_push125cm_yawleft6_publish.mp4`

| property | value |
|---|---|
| SHA-256 | `f20c47ab4a40cb0aad6ee3d4ac173e517c938b67b43cbc5ebcc04fee9f723d47` |
| bytes | 9,211,189 |
| video | 1920x1080, H.264 High, yuv420p |
| cadence | exactly 486 decoded frames at 60/1 fps |
| duration | exactly 8.100000 s |
| camera | 1.25 m smooth push, yaw 6.69, pitch 1.61 |
| scene | cluster 504, `ThunderStorm`, clock 0.71, no driven flash |

The first frame, final frame, and one-frame-per-second contact sheet contain no
NetworkSense text, title bar, desktop, cursor, crosshair, gameplay HUD, or minimap.
`freezedetect=n=-60dB:d=0.5` emitted no `freeze_start`; door, pillar, hearth,
floor, and portal parallax visibly advance.

This is publish-safe with respect to capture chrome. It is still a composition
candidate rather than a final creative lock: the endpoint retains a natural cyan
portal pulse, and the 6-degree left bias brings the blue hanging banner into the
left edge.

## The four-step bracket

Only one pose variable changed in each lap.

| run | camera delta | raw clip bytes | raw clip SHA-256 | observation |
|---|---|---:|---|---|
| `20260827-133124` | 2 m, yaw 12.69 | 26,004,367 | `3c084114876095fa151579123696b94bf4a9a283c111bc2f0334e1ddcb538f65` | clean motion, but the portal grows too large at the endpoint |
| `20260827-133955` | 1.25 m, yaw 12.69 | 21,343,540 | `1160ea36dd4ceefae0967d0aa681a1ef53a44029f1866e9bd003c7f6cc06a3d8` | motion remains legible; shorter travel reduces but does not remove the portal |
| `20260827-134827` | 1.25 m, yaw 9.69 | 25,834,095 | `a6d0730f178fdabd89d4c55ead3ade61271d2ae4a1dc2562066de9e9562286bb` | right door/portal shift outward and hearth shifts toward center; 3 degrees is not enough |
| `20260827-135453` | 1.25 m, yaw 6.69 | 25,078,078 | `24dd7765fa490218c96edd9337c22eb6fcb7aaf6e85b333b6d487c7dd3e8bef5` | portal shifts farther outward; left banner establishes the opposite composition edge |

The exact coordinate-bearing TSV remains in the ignored local path
`out/era17/clips-clean-125cm-yawleft6.tsv` and its AM4 plan copy; coordinates are
not duplicated into this public repository. Its non-coordinate controls are
recorded above, and its 248-byte SHA-256 is
`59bb4609be9fd67bb9eb66020159908dd4df53bd8a1f1c5c086f0a9abbc585e9`.

## Capture-state proof

For every lap, the wrapper temporarily set NetworkSense `isModEnabled=false`
while retaining `portalConnectionCacheEnabled=true`. The boot log independently
reported `Portal connection cache enabled; interval=5s.` NetworkSense `OnGUI`
therefore disappeared without disabling the portal cache.

The wrapper restored both pre-existing operator files byte-for-byte after every
run:

| file | SHA-256 before and after |
|---|---|
| NetworkSense config | `217c14758239bb89b06926db0b49f28b9070f122a0e2e088059fcd340bce66c7` |
| `orbit-request.json` | `c25bff61ecc3cbda1d6d215879d903eb25183b517f4e7bd8bbb2bf569f4c5cc1` |

Valheim was idle after each run. The request file remains armed because it
predated this work. No `comfystewardview` files or ZDO-geometry artifacts were
read or changed by this capture lane.

## Slicer defect and recovery

**VERIFIED defect:** the AM4 staging runner's raw per-receipt clip is not
publication-safe. It deliberately begins 0.25 s before the receipt and ends
0.25 s after it (`dur = wall_s + 0.5`) with `-c copy`. The driven camera turns
off before that post-roll ends, so normal gameplay HUD and minimap enter between
8.1 and 8.2 seconds. A copy-only trim was rejected because the discontinuous raw
timestamps produced an invalid 11.95-second result.

The accepted recovery preserved the raw clip and normalized the first 486
decoded frames onto a new 60 fps timeline:

```powershell
ffmpeg -hide_banner -loglevel error -y `
  -i 0504_stormtwil_push125cm_yawleft6_clean.mp4 `
  -vf "select='lt(n,486)',setpts=N/(60*TB)" -frames:v 486 -an `
  -c:v libx264 -preset slow -crf 16 -pix_fmt yuv420p -r 60 `
  -movflags +faststart 0504_stormtwil_push125cm_yawleft6_publish.mp4
```

The remote capture was executed with:

```powershell
ssh homebase '~/valheim-capture/run-clips-clean-lap.sh ~/valheim-capture/plans/clips-clean-125cm-yawleft6.tsv'
```

These are reproducibility receipts, not instructions for a human operator to
finish the work; both commands were executed during the lap.

## Staging provenance

The ignored local plans under `out/era17/` and their uploaded AM4 copies had
matching hashes:

| staging input | bytes | SHA-256 |
|---|---:|---|
| `clips-clean-1.tsv` | 236 | `b449925d4b83454408362cf804a0aa59ed6a1f380bc1de8f373fe460ed13eaef` |
| `clips-clean-125cm.tsv` | 241 | `e2eabe7d0ec90e371ee374b5611b49b250aaa772e749b385f253e671933d6c8e` |
| `clips-clean-125cm-yawleft3.tsv` | 248 | `a70cd4b97ffdc06a86d6c0d12d50f7a5c7ad55818b0b8d47865ba199668c16eb` |
| `clips-clean-125cm-yawleft6.tsv` | 248 | `59bb4609be9fd67bb9eb66020159908dd4df53bd8a1f1c5c086f0a9abbc585e9` |
| `run-clips-clean-lap.sh` | 3,179 | `34ac3eedb8f54860c1cedfbbd6036cb6c14cd1acf564dc5f49d2eafd31e1a758` |

These staging files and the AM4 runner are not authoritative product code.

## Edge and next bounded question

The clean artifact closes the motion/chrome question. The next implementation
edge is the runner: its publication output must use exact normalized boundaries
rather than debug pre/post-roll plus stream copy. The next creative question is
inside the 3-to-6-degree yaw bracket, or a lateral camera offset, but should not
be mixed with the slicer repair in one lap.

Uncertainty retained: one build and weather realization, 1080p only, natural
storm and portal animation, second-generation CRF 16 output, visual rather than
automated chrome detection, no audio, no driven flash, and no 4K pass.
