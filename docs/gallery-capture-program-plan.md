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
| Real local proof | OMEN and AM4 each passed nine lens/frame cases at 1920, three 3840 frame cases and two legacy cases; the extracted Windows launcher also passed. Final save fingerprints and restoration receipts match. |
| Source landing | Pushed to `main` in SelfieStick `7bf5ae7`, Steward `2a9197d`, and comfy-quest `85cbb2a`; Baseline records this cut. Local candidate artifacts remain versioned and hash-pinned; clean-revision release promotion follows. |
| Public rollout | Pending a release cut from pushed source with exact artifact pins and a proof-gated Steward deployment. Local candidate testing is historical evidence, not a claim that public downloads are live. |

Quest Studio and Lab test gates pass in the clean landing checkout. The separate
Quest game-plugin projects currently fail to build against local Valheim 1.0.12
assemblies because `main` has older game APIs; compatibility edits in the primary
Quest working tree belong to another task and are excluded from this capture landing.

The [machine-readable index](evidence/gallery-capture-20260915.json) pins local
candidate and PNG bytes. The initial OMEN 0.3.0 isolation failure remains historical:
the client ignored `-savedir`, selected cloud Questy and an existing local ComfyEra11,
and saved both. The initial restoration claim was invalid. Derek confirmed both are
capture-only; current post-run saves match preserved evidence and are retained. No
older backup was installed. This disposition does not turn the invalid r1 runs into
acceptance proof. The corrected 0.3.1 runner and final r4 proofs are the accepted path.

## Next release cut

1. Resolve the separate Quest plugin build compatibility gate before publishing its
   next full package. Preserve the unrelated compatibility work until its owner lands it.
2. Build Steward's shared composer and SelfieStick's runner from pushed, immutable
   revisions. Record the new ZIP/DLL byte counts and SHA-256 in their release manifests.
3. Import the published Steward artifact into Studio through its verified importer,
   publish the exact Studio package, and check the gallery and Studio exports are
   byte-equivalent for one camera specification.
4. Re-run the real local capture matrix if runner or plugin bytes change. Stage the
   archive catalog, hosted thumbnails, pinned runner and actual OMEN/AM4 receipts
   through Steward's proof gate. Review the PNGs and restoration evidence again.
5. Enable public downloads only from that staged, proof-validated release. Keep
   incomplete photographs visible with their availability reason.

This is a release sequence, not a request to redeploy on a documentation push.
Moving-camera capture follows the still release: define a time-sampled camera path,
runner contract and game proof before adding a video control. Fisheye, panorama,
physical aperture simulation and cross-world composition remain later work.
