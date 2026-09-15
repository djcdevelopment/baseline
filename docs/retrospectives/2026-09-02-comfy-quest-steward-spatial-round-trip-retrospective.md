# Comfy Quest ↔ ComfyStewardView spatial round trip — retrospective 2026-09-02

## Executive summary

This work began with a plausible architecture and a substantial implementation produced by
several agents, but without enough reason to trust the seams between the pieces. It ended with a
local, tested operator loop in which ComfyStewardView can export a sphere from one exact world
snapshot, Quest Studio can turn it into Runtime Experience v2 intent, Runtime can record the
actual three-dimensional observation, and Steward can ingest and render that evidence against
the same snapshot.

The durable design is deliberately small. The products remain sovereign and exchange two
strict, bounded, content-addressed JSON files. Baseline retains the rationale and discovery
links, not another implementation. Quest evidence has its own DuckDB rather than living in
Steward's rebuildable analytics cache.

The audit was worth doing. The earlier work was internally convincing but missed failures that
only appeared across runtimes or at lifecycle boundaries: .NET and Java did not have a shared
numeric hash representation; Studio could lose spatial evidence behind its public 20-receipt
view; repeated downloads produced different bytes; `count_in_area` was implemented in Runtime
but dropped by Studio and unrenderable in Steward; record-count limits did not guarantee the
document byte limit; and reused snapshot ids could display evidence from different world bytes.
Those were corrected and guarded before landing.

The implementation landed on `main` as:

- Comfy Quest package commit `91a0ff837d92fa7fb24a55852886a1ec4aaa5bc9`, whose packages
  identify source commit `442425a5c0fe95b4ea8ba8af8826dc961041d898`;
- ComfyStewardView commit `9820b830ccd0a2e22fac4344076d735e79de629b`; and
- Baseline commit `7a30d2d7f5319008cf811db9bdbf9bb3e4b404fa`.

The local contract and repository claims are **VERIFIED** below. A real browser-to-game-to-map
lap on AM4 was **UNVERIFIED at closeout** and was not implied by landing the code.

## What the operator gets

The intended lap now has six visible handoffs:

1. In Steward, select one real ZDO from the active snapshot.
2. Choose a world-fixed or Charm-relative sphere and download its anchor file. The server
   re-resolves the snapshot and ZDO; it does not trust coordinates posted by the browser.
3. Import that file into a specific Studio route. Studio preserves the source snapshot, piece,
   producer revision, and content hash while lowering it into an Experience v2 spatial area.
4. Play the exact compiled revision. Runtime evaluates Euclidean X/Y/Z predicates and writes
   the resolved center, observed point or count, progress, and outcome into receipts.
5. Download the newest exact run's spatial evidence from Studio. Repeating the download over
   the same receipt set produces identical bytes.
6. Import the evidence into Steward with the operator token. Steward verifies the contract and
   hash, stores it idempotently in `quest-evidence.duckdb`, and overlays it only when snapshot
   id, world id, and source-file SHA-256 all match.

The X/Z circle on the map is explicitly a projection. Positional evidence retains both Y
coordinates and Runtime's true 3D distance. Count evidence shows its current/required tally and
does not invent a representative point.

## What shipped

### Comfy Quest

- Runtime Experience v2 gained first-class `spatial_areas`, route `area_id` references, and the
  closed predicate set `within_radius`, `entered`, `left`, `remained`, and `count_in_area`.
- The pure evaluator records bounded progress and actual-versus-expected evidence using all
  three axes. `entered` and `left` retain the decisive crossing point rather than whichever
  position happened to be latest.
- The public anchor and evidence schemas are strict, capped at 256 KiB, and hashed over ordered
  scalar fields. Numeric values use normalized IEEE-754 binary64 bits, including one canonical
  representation for both signed zeros.
- Studio imports anchors with optimistic revision checks, rejects ambiguous route ids, retains
  source provenance, and treats an identical re-import as a true no-op.
- Studio selects evidence from the exact campaign or standalone release identity, scans the
  bounded internal receipt window rather than the 20 rows intended for display, and emits the
  largest newest record prefix that actually fits the byte cap.

### ComfyStewardView

- Anchor export resolves snapshot provenance and ZDO geometry from DuckDB and includes the full
  source revision. Only world-fixed and Charm-relative spheres are admitted.
- Strict Java consumers reproduce the .NET anchor and evidence hashes, reject duplicate and
  trailing JSON, validate true 3D distance, and distinguish positional from count evidence.
- The import API is protected by a byte-exact operator token. Evidence persistence is
  transactional, content-idempotent, bounded, and separate from the analytics cache.
- Overlay queries join on snapshot id, world id, and file SHA-256. A cache rebuild that reuses a
  numeric snapshot id therefore cannot inherit evidence belonging to other bytes.
- The existing point-only rehearsal database migrates in place to nullable observation points
  and explicit current/required counts.
- Deployment preserves an existing import token, protects the remote environment file, records
  token rotation accurately, and leaves the evidence database intact when refresh removes the
  rebuildable cache and rendered layers.

### Baseline

- [PD-11](../decisions/pd-11-spatial-authoring-round-trip.md) records the ownership and file
  boundary.
- `REPO-MAP.md` makes ComfyStewardView discoverable as the world-snapshot and spatial-authoring
  authority.
- The obsolete Meta-Creator schemas, compiler, Studio, deployment script, fixtures, and tests
  were removed. Their Git history remains the reconstruction path; Baseline no longer presents
  a second product authority.

## The seams the first implementation missed

| Seam | Why it looked healthy | Correction |
| --- | --- | --- |
| Cross-runtime numeric hashing | Each language could hash its own decimal rendering consistently. Java and .NET disagree at formatting thresholds and on signed zero. | Hash finite numbers as lowercase 16-character IEEE-754 bits and normalize both zeros. Shared fixtures now pin ordinary, decimal-edge, and signed-zero cases. |
| Receipt visibility | Studio's status card correctly showed only 20 receipts, so tests using recent evidence passed. Older spatial receipts silently disappeared from export. | Keep the public list at 20 while the evidence path uses Runtime's bounded 200-receipt maximum. |
| Repeat export | The bundle was valid on every click, but `exported_utc = UtcNow` changed its content hash every time. Steward therefore stored duplicate logical evidence. | Set export time to the newest included receipt time and assert identical repeated downloads. |
| Document bounds | Taking at most 512 records satisfied the schema count but could still exceed 256 KiB once pretty-printed. | Serialize candidates and binary-search for the largest newest prefix within the actual byte limit. |
| Count evidence | Runtime evaluated `count_in_area`, but Studio required an observed point and discarded it. Steward also assumed every row had coordinates. | Carry bounded current/required values; require null point and distance for counts; migrate the evidence table and render the tally without a fake marker. |
| Boundary-crossing evidence | `entered` and `left` could report the latest point even when an earlier pair was what satisfied the predicate. | Persist the point on the decisive side of the first observed crossing. |
| Multi-experience identity | Standalone project compilation and campaign publication can have different pack/content identities. | Select and export the actual Runtime receipt pack and content hash. |
| Cache rebuilds | Joining only by numeric snapshot id worked until a rebuilt cache reused that id. | Require the id, world id, and file SHA together for every overlay lookup. |
| Import idempotency and malformed drafts | Duplicate route ids could throw, while identical imports still advanced revision and timestamp. | Return `route_ambiguous` and leave a byte-identical mapping unchanged. |
| Deployment lifecycle | Refreshing rebuildable state risked treating evidence and credentials as disposable. | Preserve the dedicated evidence volume and existing token; restrict `.env` permissions to the operator. |

## What worked

### The file boundary made distrust productive

The two-file design gave the audit a finite surface: parse, validate, hash, lower, observe,
export, import, join. Neither repository needed source access to the other, and every value that
crosses can be retained and inspected. The same boundary also made offline use and exact replay
natural rather than special modes.

### Shared answers were stronger than parallel implementations

The most useful cross-language tests do not merely ask whether Java and .NET return *a* hash.
They pin the same expected hash. That immediately exposed numeric canonicalization as protocol,
not an implementation detail. The evidence fixture likewise guards date normalization, null
count geometry, snapshot provenance, and 3D distance.

### Failure injection changed passing checks into evidence

Critical guards were deliberately observed failing before their fixes were restored:

- removing the extended receipt scan produced `spatial_evidence_missing`;
- removing the import no-op advanced revision and failed the idempotency assertion;
- substituting standalone identity into campaign evidence failed the provenance assertion;
- returning Java's prior signed-zero representation broke the shared hash; and
- omitting the snapshot file hash from Steward's join made the reused-id regression fail.

This mattered because the starting concern was not lack of tests. It was that a collection of
self-consistent tests could all agree with the same mistake.

### Evidence and user display were allowed to have different bounds

Keeping Studio's visible receipt list small while giving the export path a larger, still-bounded
internal view avoided a false choice between a usable screen and a trustworthy handoff. The same
principle appears in Steward: the map is a 2D projection, while the tooltip and stored evidence
retain the 3D facts.

## What did not work

### Predicate coverage was treated as one shape

The first pass generalized every spatial result as “sphere plus observed point.” That was true
for four predicates and false for `count_in_area`. Because Runtime, Studio, storage, and UI were
tested separately, the advertised predicate could exist in one layer and vanish at the next.
The better review question was not “does spatial evidence work?” but “can every closed-registry
member complete the full producer-to-consumer path?”

### Validity was confused with repeatability

The first evidence download was schema-valid and hash-valid, yet a second click produced a new
file for no new observation. Similarly, a 512-record bundle met one declared bound while
violating the byte bound. Idempotency and size are properties of the serialized artifact, not
of the in-memory object. Testing the final bytes exposed both defects.

### Parallel agents shared one mutable commit boundary

The most avoidable process failure happened after the code was correct. Another workspace actor
committed while packaging and verification were still running. Commit `7008322` combined the
spatial work with unrelated CreatorOS work. A package built before that commit named an older
source revision; later, another commit landed between the Contracts and Studio pack commands,
temporarily giving the pair different provenance.

No history was rewritten after the problem was disclosed. The final shape uses a source/version
commit (`442425a`) followed by one package commit (`91a0ff8`) containing both artifacts built
from that source. That is mechanically sound, but the mixed `7008322` history remains.

The lesson is concrete: separate worktrees are insufficient if several agents also write and
commit the same active branch. Package production needs one stable source commit and one writer
for the entire pair. A second agent may inspect or test that revision, but must not advance
`main` between the two packs.

### Local green did not become a live claim

Maven compiled the service, Node parsed the inline UI, PowerShell parsed both deployment scripts,
Bash parsed the entrypoint, and Docker Compose accepted the deployment model. None of those
actions clicked through the browser, exported from a real current snapshot, or observed Valheim
produce the return evidence. Stopping at **VERIFIED locally** was the correct outcome; calling
the round trip operationally complete would have repeated the original trust mistake at a
larger scale.

## Evidence state

### VERIFIED locally

Comfy Quest:

- 384 Quest Lab xUnit tests passed.
- 137 Quest Studio xUnit tests passed.
- 446 Python tests passed.
- Lab and Runtime Release builds completed with zero warnings and zero errors.
- Generator drift, source intents, repository identity, release self-test, package validation,
  no-reach, diff, and full-history secret-scan gates passed. Gitleaks scanned 223 commits.

ComfyStewardView:

- 15 Maven tests passed, including five cross-runtime contract/store tests.
- Inline browser JavaScript, both deployment PowerShell scripts, the Bash entrypoint, Docker
  Compose configuration, and `git diff --check` passed.

Baseline:

- 104 unit tests and 8 corpus tests passed.
- All 13 deterministic corpus projections matched.
- Entrypoint-link and diff checks passed.

The final local rehearsal packages are:

| package | bytes | SHA-256 |
| --- | ---: | --- |
| `Comfy.Quest.Contracts.0.9.3-local.nupkg` | 140,047 | `016f0b74dc81f11f1b332bdd9d83dcb67aa858e4e69500bd58beacf5effd2265` |
| `Comfy.Quest.Studio.0.9.3-local.nupkg` | 437,785 | `d0afa0882242683ad948637bd66c8923c046d860307d156c2ca71a0ed7248555` |

Both packages identify source revision `442425a5c0fe95b4ea8ba8af8826dc961041d898`
and were committed together by `91a0ff837d92fa7fb24a55852886a1ec4aaa5bc9`.

### UNVERIFIED at closeout

- This work did not record an AM4 Steward deployment from `9820b83`.
- This work retained no browser click-through that exported an anchor from a disposable real
  snapshot and imported its returned Runtime evidence.
- This work retained no live Valheim Runtime evidence for the new spatial operator lap.
- At closeout, the `0.9.3-local` packages were rehearsal artifacts, not a public NuGet release.
- Runtime `world_uid` is retained but is not declared equivalent to Steward `world_id`.
- Only spheres with a world center or zero-offset Charm-relative center are in scope. Rotation,
  offsets, other shapes, and inferred world-identity mapping remain intentionally absent.

## What should happen next

At closeout, the next proof was one disposable end-to-end lap, not another architecture pass:

1. deploy an exact clean Steward revision to the automation seat;
2. export one anchor from a known snapshot and retain its bytes and hash;
3. import it into Studio, compile and play that exact Quest revision;
4. cause one positional predicate and one `count_in_area` predicate to emit evidence;
5. download the evidence twice and verify byte identity;
6. import it twice and verify the second import is a no-op; and
7. render it on the referenced snapshot, then select a deliberately reused snapshot id with a
   different file hash and verify that it renders nothing.

That lap should ask a human only whether the selection/import/overlay flow is understandable.
Hashing, identity, counts, database survival, and wrong-snapshot refusal are machine questions
and should be established before the browser is handed over.

Public package publication remained a follow-up under the existing NuGet runbook. New geometry,
transforms, or identity mapping should wait for an observed authoring need rather than expanding
the protocol speculatively.

## Durable lessons

**A round trip is a product, not two endpoints.** Every registry member has to survive every
hop, and the test must follow the bytes all the way back to where they are displayed.

**Content addressing requires canonicalization and determinism.** A valid hash algorithm is not
enough if two runtimes serialize numbers differently or if wall-clock metadata changes an
otherwise identical artifact.

**Bounds compose only when the final artifact is measured.** A record cap, UI cap, database cap,
and byte cap protect different resources. None implies another.

**Immutable provenance needs a stable writer boundary.** Source commit, package version, and
package bytes form one publication unit even when Git records source and artifacts in separate
commits.

**Do not upgrade local proof into live evidence.** The implementation is ready for the lap. The
lap is still the event that can prove the operator experience.
