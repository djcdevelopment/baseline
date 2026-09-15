# Gallery capture program plan

Updated 2026-09-15. This plan tracks one still photograph of an archived Valheim
world from gallery reference through a local game capture. The owning implementation
and runbooks are in [ComfyStewardView](https://github.com/djcdevelopment/ComfyStewardView/blob/main/docs/gallery-capture-composer.md),
[comfy-quest](https://github.com/djcdevelopment/comfy-quest/blob/main/docs/gallery-capture.md),
and [SelfieStick](https://github.com/djcdevelopment/SelfieStick/blob/main/docs/gallery-capture.md).
Baseline holds the cross-repository rationale and [evidence ledger](evidence/2026-09-15-gallery-capture-composer.md).

## Player outcome and boundary

Choose an archived photograph in the public gallery or Creator/DM, adjust a still
composition in Lens or Outside view, inspect an estimated coverage pyramid, and
download one portable capture. The archive reference supplies pose, world identity,
weather, time and lighting; the local Valheim client renders the finished PNG. A
photograph lacking enough pose or world metadata remains browsable and explains why
composition or replay is unavailable.

Steward owns the photo catalog, matching read-only scene, shared composer and export
service. Quest Studio embeds a pinned copy of that composer and proxies the same
export through its token boundary. SelfieStick owns the `selfiestick-capture/v1`
contract, game plugin and Windows/Linux runner. The runner accepts the exact archive
pair and a local character, uses disposable copies, records observed versus requested
camera values, and restores original save discovery and plugin state. Baseline owns
the evidence and ownership map. Each repository builds independently; cross-repository
bytes carry an explicit version, size and SHA-256 pin.

## Current state

| Stage | State and evidence |
| --- | --- |
| Shared still composer | Implemented in Steward; both real browser entry points, camera fixtures, geometry aim, keyboard movement, reset, resize and independent observer passed. |
| Archive catalog and export | 83 Era 11 photos projected; a valid local proof gate enables deterministic ZIP downloads and rejects false proof summaries, wrong archive or incompatible plugin. |
| Portable exact capture | SelfieStick 0.3.1 captures the authored lens pose, vertical FOV and requested dimensions; legacy shot lists keep their prior placement behavior. |
| Real local proof | The pushed SelfieStick runner was freshly proved on OMEN and AM4: each passed nine lens/frame cases at 1920, three 3840 cases and two legacy cases. Final save fingerprints and restoration receipts match. The earlier r4 proofs remain historical. |
| Pushed-source stage | Steward composer/server and SelfieStick runner were rebuilt from pushed revisions; Quest `0.9.14-gallery.3` was packed from pushed revision `dd3685b`. The local Steward gate enabled downloads from the two new proofs, and the gallery and package-consuming Studio host exported identical ZIP bytes. The [stage evidence](evidence/gallery-capture-stage-20260915.json) pins every artifact. |
| Public rollout | Pending promotion of the reviewed staged artifacts to the public deployment. Local proof-gate success does not change live downloads. |

Quest Studio and Lab test gates pass. Minimal Valheim 1.0.12 API compatibility edits
are now pushed in Quest `dd3685b`; AM4 builds Lab and Runtime with zero warnings and
errors. This is compile evidence only. Broader unrelated edits in the original Quest
working tree remain preserved.

The [machine-readable index](evidence/gallery-capture-20260915.json) pins local
candidate and PNG bytes. The initial OMEN 0.3.0 isolation failure remains historical:
the client ignored `-savedir`, selected cloud Questy and an existing local ComfyEra11,
and saved both. The initial restoration claim was invalid. Derek confirmed both are
capture-only; current post-run saves match preserved evidence and are retained. No
older backup was installed. This disposition does not turn the invalid r1 runs into
acceptance proof. The corrected 0.3.1 runner and final r4 proofs are the accepted path.

## Staged release and public promotion

The staged release completed source landing, clean-revision artifact pins, Studio's
package import and byte-equivalent export, a fresh 14-shot matrix on both game hosts,
and a local proof-gated Steward catalog with hosted thumbnails. The game harnesses
restored both hosts, and the loopback stage servers were stopped. Quest Lab and Runtime
also compile against AM4's Valheim 1.0.12 assemblies with zero warnings; live plugin
load remains unproven.

Public promotion is the remaining release action. Use only the exact artifacts and
receipts in the stage evidence, verify the deployed proof gate before downloads are
advertised, and keep incomplete photographs visible with their availability reason.

This is a release sequence, not a request to redeploy on a documentation push.
Moving-camera capture follows the still release: define a time-sampled camera path,
runner contract and game proof before adding a video control. Fisheye, panorama,
physical aperture simulation and cross-world composition remain later work.
