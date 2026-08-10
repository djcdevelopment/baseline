# Quest Lab expansion retrospective — 2026-08-09

## Executive summary

Quest Lab r24 is now a creator-ready local workflow rather than a collection of live probes.
The release landed on `main` as `1643e923` with a guarded 91-row atlas, 90 unique Valheim
signatures, stable canonical creator events, a durable event archive, offline exports, an
optional local-first Google Sheets handoff, and Gallery v2 lifecycle tooling. The final OMEN
pass validated the exact DLL, and Derek accepted the rebuilt marble-grand gallery visually.

The result is deliberately honest: machine evidence proves the event contract, archive
integrity, package contents, and fixture geometry; human review remains authoritative for
appearance. Google OAuth was not exercised because it requires the creator's own Cloud project
and consent. A final live comparison request was delivered after visual acceptance, but OMEN
exited before returning that receipt; automated comparison coverage remains green.

## What shipped

### Canonical events and archive

- The generated atlas remains guarded at 91 rows / 90 signatures / 77 methods / 34 creator
  events, with 57/57 creator-safe runtime signatures and 86/86 practical routes.
- Quest Lab and ComfyNetworkSense share the exact event catalog, loader, evaluator, and authoring
  contract; local/RPC and overload paths stay deduplicated before durable persistence.
- Each session writes descriptive `comfy-questlab-events/v1` JSONL, with atomic CSV projection,
  bounded queue/rotation/retention, explicit drop notices, crash-tail handling, and privacy-safe
  defaults.
- The offline parser is strict when asked, tolerant for legacy inputs, formula-safe, nested-field
  redacting, mirror-aware, and capable of JSON/CSV/XLSX/ZIP output. The loopback Sheets companion
  is fixed to localhost and uses explicit `drive.file` OAuth only after creator opt-in.

### Gallery v2 and creator operations

- Gallery profiles are generated and drift-checked; bounded batch commands cover prepare, run,
  reset, report, export, identify, evidence, clear, compare, build, and rebuild.
- The first Truth Lens pass exposed that the standing pre-r24 gallery had all nine braziers
  intersecting the roof. The r24 rebuild cleared only marked objects, preserved the tree recovery
  ledger, and produced `marble-grand-20260809T204409Z-01` with all nine fixtures below the roof.
- The acceptance record keeps the visual decision separate from the machine verdict. Derek's
  review accepted the solid marble floor, larger scale, hall width, canopy, braziers, rune
  banners, sign lighting, welcome camp, tree clearance, and Quest grid readability.

## Evidence and verification

Repository gates:

- 208 Python tests passed, with two expected environment skips.
- 319 shared .NET tests passed.
- Both Release builds completed with zero warnings and zero errors.
- The privacy-clean creator package is `B7F3D6F785388D4513F19ABD4FD70FEF24E177562167FFDE05DB05C8E0734576`.

OMEN receipts:

- Exact r24 creator contract: 34/34 events, 34/34 example quests, zero double completions.
- Final event session: 309 canonical rows, sequences 1–309, one clean segment, zero drops,
  clean shutdown, and 309 matching CSV mirror rows collapsed by the parser.
- Gallery Truth: 9/9 fixture clearances pass; 631/823 floor slabs pass Valheim's live RoofCheck,
  so the remaining weather warning is retained rather than promoted to a visual claim.
- Local Sheets doctor: one readable session, no credentials, and zero network requests.

Artifacts are retained under the ignored `captures/questlab/omen/` handoff directory. The
repository package and documentation remain the durable creator-facing handoff; machine paths
and local receipts are evidence, not public installation requirements.

## What worked

1. **Truth Lens before aesthetic confidence.** Bounds, fixture clearance, roof checks, and fresh
   prefab comparisons caught a real placement defect that a role count would have missed.
2. **Authoritative JSONL plus projection.** Treating JSONL as the source and CSV/XLSX as
   projections made mirror verification, crash recovery, and spreadsheet safety composable.
3. **Bounded operations.** The mailbox accepts named operations and fixed selectors, not console
   text or arbitrary paths. That kept live testing repeatable and reversible.
4. **Human review at the right boundary.** Code verified geometry and lifecycle safety; Derek's
   visual judgment decided whether the rebuilt hall actually looked good.

## What did not work, and how it changed the design

- The first final gallery evidence was a fail: all nine braziers were about 1.98 m too high.
  The rebuild path and runtime mesh measurement were used to correct the placement instead of
  dismissing the observation as lighting or a camera artifact.
- Lexical filename ordering once allowed crash-tail tolerance on the wrong JSONL segment. The
  parser now chooses the highest selected segment per filename session group and enforces live
  byte/line bounds while streaming.
- The live comparison request arrived after OMEN had exited, so no receipt was invented. The
  missing receipt is documented as an external evidence gap; automated compare tests remain the
  contract proof.
- Google Sheets was not tested with real credentials. That is intentional: organizations must
  supply their own OAuth client, consent policy, and Workspace permissions. Local JSONL/CSV/XLSX
  remains fully useful without that external setup.

## Follow-up options

These are optional polish/evidence tasks, not release blockers:

- Capture a fresh live `gallery_compare` receipt during a future OMEN session.
- Run the eight-school human lane once more if a publisher-facing gameplay witness receipt is
  desired; the exact synthetic contract already covers all 34 canonical events.
- Tune canopy coverage if the 631/823 RoofCheck warning is unacceptable for a particular biome,
  then repeat the visual acceptance pass.
- Exercise the one-click Google path with an organization's real Desktop OAuth client.

The durable lesson is to keep three claims separate: what the catalog/evaluator proves, what the
runtime archive observed, and what a human saw. Quest Lab is strongest when those layers agree,
and when a disagreement produces a bounded receipt instead of a confident guess.
