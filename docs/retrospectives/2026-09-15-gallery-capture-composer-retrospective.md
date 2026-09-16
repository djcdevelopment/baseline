# Gallery capture composer and SelfieStick — retrospective 2026-09-15

## Outcome

The local still-capture candidates let a person start from an archived gallery photo,
move an exact camera in the browser, see estimated coverage, and download a Windows or
Linux capture package. The same Steward component runs in the public gallery and in
Creator/DM; Studio's token-gated route returns the same ZIP bytes. SelfieStick uses a
versioned specification to render the authored pose in Valheim and reports the actual
pose, field of view, dimensions, image hash and restoration result. The final candidate
passed real archive captures on OMEN and AM4. This is implementation and local proof,
not evidence that a public deployment is now serving downloads.

The [work ledger](../evidence/2026-09-15-gallery-capture-composer.md) and
[evidence index](../evidence/gallery-capture-20260915.json) identify the source bases,
candidate hashes, test counts, 28 final cross-host cases, extracted-launcher run and
preserved incident files. The owner runbooks are in the sovereign repositories; this
document records why the boundaries and corrections matter.

## What the user can do

A gallery photograph selects its archived build and remains visible as a reference
thumbnail. Lens view edits the capture camera with mouse look and WASD/QE; Outside view
orbits independently and offers position and aim handles, a player-scale marker and a
small lens preview. Lens, frame and longest-edge size control vertical FOV and actual
output dimensions. The yellow pyramid and target-distance rectangle react to each
edit. Reset restores the reference. A missing camera or world receipt is explained
instead of producing an invented pose. The browser estimate uses available archived
scene geometry; the local game supplies terrain, vegetation, weather and final light.

The download contains `selfiestick-capture/v1`, a generated shot row, reference
thumbnail, dependency hashes and launchers. The user supplies the matching `.db` and
`.fwl` archive, Valheim/BepInEx installation and local `.fch` character. Results are
local PNGs and receipts. Composer shots place the render lens directly; player feet
are below it only to stream the world. Obstruction or placement failure is reported,
not hidden by moving the authored camera.

## Why each owner matters

Steward already knew the photographs, archived-world identity and read-only geometry,
so it could supply one catalog, scene and composer to both entry points. Studio owns
Creator/DM's authentication and gameplay-target rules, so its photography mode proxies
Steward reads and export without making archive geometry a live Runtime target.
SelfieStick owns game-camera behavior, local save discovery and portable execution,
so its contract and runner can be verified independently of a browser deployment.
Baseline stores the cross-repository decision and historical proof rather than another
product implementation. The boundary also made byte-equivalence and shared camera
fixtures testable: neither application can quietly implement a different lens model.

## What the proof actually covers

Shared fixtures check coordinate mirroring at the renderer boundary, lens versus
feet, all lens/frame/size combinations and projection corners. Browser execution
checked both entry points, geometry picking and drag handles, keyboard editing,
reset, resize, repeated view switches without exported camera drift, missing metadata
and WebGPU failure. The server rejected incompatible plugin versions, wrong archive
hashes and malformed camera requests before a download could be called valid. Studio
and gallery produced byte-identical export ZIPs.

The final game candidate produced 12 exact stills and two legacy rows on each of
OMEN and AM4. Every exact receipt measured the requested camera pose, vertical FOV
and PNG dimensions, with matching image hashes; representative wide, normal, tele,
landscape, square, portrait and rotated 4K images were visually inspected. The
extracted Windows launcher completed one further exact capture. Final wrappers
verified plugin/config controls, source files and actual save-discovery trees before
and after. These receipts support the local runner and proof gate. They do not claim
that hosted archive data, software releases or a public runtime were deployed.

## The failure that must stay visible

The first OMEN 0.3.0 runs assumed `-savedir` controlled the Valheim client save
directory. It did not. A legacy fallback selected cloud **Questy** and the existing
local **ComfyEra11**, and the game saved both. I initially claimed restoration had
passed because the wrapper checked the supplied source archive and character, not
the saves the client actually used. That claim was wrong; the r1 proofs are
invalidated. Questy grew from 35,705 to 44,868 bytes, its `.old` was overwritten,
and several converted world chunks and the current manifest changed.

Post-run files and hashes were preserved before any attempted repair. No exact
pre-run backup was found. Derek confirmed both Questy and ComfyEra11 are capture-only.
Their current saves match the preserved post-run copies and are retained; no older
backup has been installed. The [disposition record](../evidence/save-incident-disposition-20260915.json)
resolves whether recovery is required, but does not reverse the writes or rehabilitate
the false restoration claim.

The correction is mechanical. Runner 0.3.1 requires exact unique local world and
character filenames before world entry. Windows parks the real Unity save directory
intact and installs disposable copies at its fixed discovery path; Linux isolates its
XDG path. The wrapper fingerprints the actual original save tree and Steam character
mirrors, not just inputs. Failure receipts and cleanup compare those before/after
states. This is the standard the first r1 gate should have enforced.

## Other corrections and cost

Visual review of a rotated still found temporal motion smearing even though camera
pose and PNG dimensions matched. The final plugin clears temporal history and
temporarily disables motion blur around the render, then restores the prior setting.
The first AM4 final launch raced Steam sign-in and failed `SteamAPI_Init()`; it was
stopped with restoration verified, then repeated after Steam was ready. Those
superseded outputs remain separate from accepted r4 proof.

The later clean Windows landing worktree exposed a byte-stability problem in
Studio's pre-existing pinned creator renderer: Git expanded LF to CRLF on checkout,
so the embedded resource failed its hash test even though the Git blob was right.
Quest now fixes checkout EOL for that asset and the new composer assets in
`.gitattributes`. A version pin must survive a fresh checkout, not only the
developer's existing working tree.

The clean landing checkout separated Studio validation from Quest's game-plugin
compatibility work. Studio built and its 149 tests passed, as did the Python and Lab
test gates. The compatibility edits were then applied in an isolated Quest checkout,
pushed as `dd3685b`, and rebuilt against AM4's Valheim 1.0.12 Linux assemblies:
Lab and Runtime both finished with zero warnings and errors. That is compile evidence
only; the installed game plugins were left untouched and no live plugin-load claim is
made.

Work began at 09:05 UTC and the first evidence index was written at 10:45 UTC;
no wall-clock or dollar cap had been specified. Existing resident tools, game installs
and archive inputs supplied the setup. One small HEARTH extraction call failed
immediately with `WinError10061`; it produced no accepted delegated output. The
implementation and review were done directly by Codex. Candidate hashes and
receipts are recorded, but frontier-model dollar cost is not available. The useful
artifact was delivered inside roughly 100 minutes; the early save incident is still
a serious process failure and is not offset by that timing.

## Final staged release

The release cut was completed from pushed source. Steward `2a9197d`, SelfieStick
`7bf5ae7`, and Quest `dd3685b` were rebuilt into pinned composer, server, runner and
Studio package artifacts. The package-consuming Studio host and the gallery exported
the same 109,900-byte ZIP for the same archived composition. The local proof-gated
Steward catalog exposed 83 photographs and accepted the exact runner and both fresh
host receipts.

OMEN and AM4 each passed 12 exact and two legacy captures with measured camera values,
unchanged source saves, and restored plugin/control state. Two early AM4 attempts
failed because the remote launch omitted `DISPLAY=:0`; they produced no frames and
restored cleanly. The corrected run passed. This recovery is recorded as history,
not hidden behind the successful receipt.

The user-facing browser preview is the clearest first test: choose a photograph,
adjust the lens, frame or size, inspect Outside view, and download. Creator/DM embeds
the same composer, but its larger workbench made the intended test unclear. The next
UI pass should make Capture's entry point and first action explicit instead of asking
new users to infer them from a dense workspace.

The stage was deliberately local. Both loopback servers were stopped after review,
public downloads were not enabled, AM4 Ollama remained inactive, and the temporary
CameraProof autorun hook was removed from OMEN and the AM4 session was stopped with
its original plugin state restored. The exact pins, receipts, limitations and failed
attempts are in the [stage evidence](../evidence/gallery-capture-stage-20260915.json).

## Source landing and what changes next

The documentation and implementation are landed on `main` through selective commits:
SelfieStick `7bf5ae7`, Steward `2a9197d`, Quest `85cbb2a`, `dd3685b`, and `072e6d3`,
and Baseline `97e77bc`. Dirty, unrelated Quest and Baseline worktrees were preserved.
Public promotion is the remaining release action. It must use only the reviewed pins
and receipts, recheck the deployed proof gate, and keep incomplete photographs visible
with their availability reason. The [program plan](../gallery-capture-program-plan.md)
defines that sequence. Moving-camera capture should wait for a time-sampled contract
and game proof; an attractive browser control alone would not establish local video.

The lasting lesson is specific: an input-path check is not a save-isolation check.
Inspect what the game actually selected, then compare those exact files through
restoration. Also inspect the image, not only numeric camera receipts. The final
release gate now reflects both lessons.
