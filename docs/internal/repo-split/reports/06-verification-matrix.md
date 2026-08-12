# 06 — Phase 5 verification matrix

Date: 2026-08-12

## Verdict

VERIFIED — All seven requested hosted workflow receipts are green at the exact
40-character revisions recorded below. G1–G8 each have a passing production-shaped
check and an observed failing fixture; the detailed matrix distinguishes hosted,
local, and fixture evidence.

VERIFIED — I4 is complete. I1 and I3 verify real local candidate bytes across the
repository boundary, but do not constitute published-release proofs.

BLOCKED — I1 and I3 cannot complete their published lanes because the corresponding
GitHub releases do not exist. I2 requires the operator's OMEN game client and private
world. I5 requires a published NetworkSense DLL plus explicit authority to boot the
live Valheim lab. None of those prerequisites was invented or bypassed.

## Exact revision and CI receipts

| Surface | Exact revision | Receipt |
| --- | --- | --- |
| NetworkSense | `8d9ced6179569d9049af982bb47e41e2f8b56a19` | VERIFIED — [CI run 31579060267](https://github.com/djcdevelopment/networksense/actions/runs/31579060267) passed both jobs: 166/166 game-independent tests and the boundary job. G1 scanned 147 files, G2 covered 14 host entrypoints plus the extractor, and G5 inspected 2 consumer projects. |
| Comfy Quest | `a7043648fe171152f71c5af743a2b81a9f8eef02` | VERIFIED — [CI run 31579881772](https://github.com/djcdevelopment/comfy-quest/actions/runs/31579881772) passed all 4 jobs: 185/185 xUnit tests, 199/199 Python tests, identity, boundary, generated-file checks, Studio packaging, and the licensed-source explanation gate. |
| Lumberjacks Platform | `d5128c03d1df5c2ab45adf042bcc7e8c48ad290b` | VERIFIED — [CI run 31586106534](https://github.com/djcdevelopment/lumberjacks-platform/actions/runs/31586106534) passed all 5 jobs. The solution passed 649/649 tests (250 Simulation + 247 Gateway + 126 Contracts + 26 Companion), the verify container repeated all 649, Authority Lab passed 7/7, Python ran 10 with 8 passed and 2 sealed-artifact skips, roadmap passed 46/46, and Workbench validated 8 tools. |
| Sovereign Shards | `4ad00beb59161ecc46bb87f8d2e42f8204c970af` | VERIFIED — [guard run 31578704964](https://github.com/djcdevelopment/sovereign-shards/actions/runs/31578704964) passed identity and boundary jobs. The boundary self-test accepted 1 safe fixture, rejected 3 bad fixtures, scanned 2 tracked executable/config surfaces, and retained `127.0.0.1:8730`. |
| Isolate | `600e2d88cd50c1f11b0931fbfb5d110536ba35b3` | VERIFIED — [CI run 31584942448](https://github.com/djcdevelopment/isolate/actions/runs/31584942448) passed 25/25 tests and built `comfy-gateway:600e2d88cd50c1f11b0931fbfb5d110536ba35b3`. Compose registers exactly 4 providers: Valheim, inference, Workbench, and Quest Lab. |
| Baseline hub | `39262cee83e2eb4148716be919be448aeed1b94e` | VERIFIED — [Hub CI run 31586644439](https://github.com/djcdevelopment/baseline/actions/runs/31586644439) passed the hub boundary over 858 tracked files, 1 retained entrypoint test, 8 corpus contract tests, the mirror check, and 13 deterministic projections. |
| Baseline Pages | `39262cee83e2eb4148716be919be448aeed1b94e` | VERIFIED — [Pages run 31586644505](https://github.com/djcdevelopment/baseline/actions/runs/31586644505) reconstructed the corpus projections, staged the historical Quest Picker surface, uploaded the artifact, and completed the static Pages deployment. |

## Named guard matrix

| Guard | Positive proof | Negative proof |
| --- | --- | --- |
| G1 — no source reach-in | VERIFIED — NetworkSense scanned 147 files in hosted CI; a local audit at the recorded revisions found 56 Comfy Quest and 218 Platform executable/config surfaces; Baseline checked 858 tracked files; Sovereign Shards checked 2 tracked executable/config surfaces. All passed without a sibling checkout or `C:\work\...` executable default. | VERIFIED — 7 bad fixtures were observed red: 1 each in NetworkSense, Comfy Quest, Platform, and Baseline, plus Sovereign Shards' 3 fixtures for an absolute work-root, a parent traversal, and forbidden port 8721. The Baseline fixture failed with `Baseline executable boundary violations: disabled fixture reached C:\work\networksense`. |
| G2 — repository identity | VERIFIED — NetworkSense covered 14 host entrypoints plus its extractor; Platform covered 30 state-changing entrypoints; Comfy Quest and Sovereign Shards accepted only their expected origins. Isolate's advertised verifier now defaults to project `isolate`, profile `Lab`, and host port 8722. | VERIFIED — NetworkSense, Comfy Quest, and Sovereign Shards each rejected a wrong-origin fixture; Platform rejected 1 unguarded state-changing fixture; Isolate rejected 1 stale `baseline`/8721 payload with exactly 2 mismatches, `project` and `published_port`. |
| G3 — Compose project-name uniqueness | VERIFIED — Platform checked exactly 8 Compose files, each with one `lumberjacks-*` project name. | VERIFIED — 1 copied-Compose fixture using `copied-project` was rejected. |
| G4 — service identity | VERIFIED — Gateway and Companion provide 2 source-level `/identity` contracts for repository, service, schema, and non-unknown revision; the extraction runtime receipt observed both services with the expected repository and revision. Current hosted CI rechecked both source contracts; its `Endpoints=0` field correctly records that CI made no live network probe. | VERIFIED — 1 stale payload naming `djcdevelopment/baseline` with revision `unknown` was rejected. |
| G5 — package-only NetworkSense consumption | VERIFIED — A clean hosted checkout with no `Lumberjacks` tree and a new NuGet cache restored and passed 166/166 tests; 2 consumer projects contain package-only references. | VERIFIED — 1 injected sibling `ProjectReference` fixture was rejected. |
| G6 — P7 mod artifact hash gate | VERIFIED — Platform CI accepted 1 synthetic `comfy-mod-release-manifest/v1` bundle containing exactly 4 files. The pure verifier reported DLL SHA-256 `c81b1f63c7db16b517fe90f90002767ae2a715147d035894c92f0ceaf649ac61` and performed no SSH, Docker, build, or deployment action. | VERIFIED — The same synthetic bundle with exactly 1 byte appended to `ComfyNetworkSense.dll` was rejected (`TamperExecuted=true`, `TamperRejected=true`). I1 below repeats the positive contract with the real local candidate. |
| G7 — generated-file drift | VERIFIED — Comfy Quest's `render_quest_lab.py --check` and `generate_seam_catalog.py --check` both passed. The checked model contains 91 atlas rows, 90 signatures, 77 methods, 34 creator events, 57/57 creator-safe signatures, and 86/86 practical runtime signatures; the patch gate resolved 88 calls (86 atlas integrations + 2 support hooks). | VERIFIED — 2 generator-policy mutations were rejected: removal of `Chat.OnNewChatMessage` and removal of `sign_written` creator metadata. The release verifier also rejected 2 independent drift cases: a hash tamper and standalone/ZIP divergence after recomputing the outer hashes. |
| G8 — corpus snapshot provenance | VERIFIED — Baseline mirrors exactly 2 Platform files from `d5128c03d1df5c2ab45adf042bcc7e8c48ad290b`: `commit-notes.jsonl` is 575,644 bytes with SHA-256 `058bd784005800b59465b76a1ca1b875b17f0bcacd1d4db68840d75334358a2a`; `workbench.json` is 42,176 bytes with SHA-256 `e4f9a9e5a786dd5e7eb20f775358e2b2b5e2ae9e68cfe70e37c2fc09704970`. Eight corpus tests passed and 13 deterministic projections matched. | VERIFIED — The contract suite rejected 3 provenance failure classes: altered bytes/hash or byte count, a missing mirrored source, and a non-40-character revision. It also binds both allowed upstream paths, so a mirror cannot silently change authority. |

## Isolate reconciliation correction

VERIFIED — The Quest Lab provider and its bounded tests were reconciled into Isolate,
and the Compose provider set is the exact 4-provider set recorded above.

VERIFIED — A final audit found that the copied
`Test-WorkbenchMcpIdentity.ps1` helper still advertised Baseline, profile Dev, and
host port 8721 even though the Isolate Compose boundary was `isolate`/Lab/8722.
Commit `600e2d88cd50c1f11b0931fbfb5d110536ba35b3` corrected all 3 defaults and
added an executable three-request contract: 2 valid Isolate invocations pass and
1 stale Baseline/8721 response fails on exactly `project` and `published_port`.
The resulting suite is 25/25 green in run 31584942448.

## Cross-repository integration lanes

### I1 — NetworkSense mod artifact to P7 hash gate

VERIFIED — The real local candidate directory contains exactly 4 files and identifies
NetworkSense source revision `8d9ced6179569d9049af982bb47e41e2f8b56a19`,
candidate label `mod-v0.5.80-split-proof`, plugin version `0.5.80`, and baked release
ID `m7-c10b-20260807-r42`. Its DLL is 940,544 bytes with SHA-256
`6d07d0756c7d928113ec4f0b10e83c73a2f4e6f8119cc4d2f6dfa66c7dbfdc24`.

VERIFIED — Platform's pure consumer verifier accepted that candidate with assembly
name `ComfyNetworkSense`, assembly version `0.5.80.0`, file version `0.5.80`, and
interim dependency profile. NetworkSense's producer-side bundle verifier rejected a
copy of this real candidate after a one-byte DLL mutation; Platform's independent G6
consumer fixture rejected the same mutation against a synthetic producer-compatible
bundle. Neither proof invoked a deploy action.

BLOCKED — This is not a published-lane I1 receipt. NetworkSense has 0 GitHub
releases and no `mod-v0.5.80-split-proof` release tag; its sole Git tag is the
non-release extraction provenance tag `split-base-20260811`. A published asset cannot
be downloaded or installed until publication is authorized and completed.

### I2 — Studio publish to Runtime check/load on OMEN

BLOCKED — The exact manual procedure is preserved in the Comfy Quest
[I2 OMEN runbook](https://github.com/djcdevelopment/comfy-quest/blob/a7043648fe171152f71c5af743a2b81a9f8eef02/docs/runbooks/I2-QUESTPACK-OMEN.md).
It requires an operator-controlled private OMEN world, the matching loopback
Companion/Studio and Runtime DLL set, and in-game input. No unattended substitute
can prove those conditions.

BLOCKED — The operator sequence is: record both revisions and the pre-run receipt
set; author, save, certify, and publish one uniquely versioned pack in the loopback
Studio; verify the inbox filename plus package SHA-256; use F10 to require an
accepted check without changing the active set; use F11 to require an activated load
with the exact pack ID/version/content hash; bind and cast on a locally owned object;
trigger one Greyling completion; prove the second trigger is suppressed; then restore
the prior active set and reset `PrivateWorldConfirmed`. No OMEN game-client action was
performed in this phase.

### I3 — Quest release to Platform vendor/import boundary

VERIFIED — The real local Comfy Quest candidate identifies revision
`a7043648fe171152f71c5af743a2b81a9f8eef02`, candidate label
`quest-v0.2.0-split-proof`, and version `0.2.0`. Platform's consumer module accepted
the 6-file set (4 payloads + manifest + checksums) and manifest SHA-256
`83ada16d86db875c9a0a71ee583f0a2cc1efa2fc2efbe49c047ce6b96e510595`.

VERIFIED — The 4 payload receipts are: `questlab.html`, 41,561 bytes,
SHA-256 `676261d7124ebc07457c5ec93516e589168446ad6ba8cd008bff70e8c33056c0`;
`quest-lab.zip`, 266,352 bytes,
`302e98c88dfe9336b6096a7e01e8910cae86a2820e57a946eddd545526d66ce8`;
`quest-picker.html`, 27,560 bytes,
`1047ca7daaaa73f7704a6c3f7bd0344d3c36c75c9db5a48abb3b3ccc403ffe7c`;
and `quest-picker.zip`, 47,495 bytes,
`f61d0e62e297888eeaedb501af4b9a3fc2d39cc668ab78c65c794ca1afd90a49`.

VERIFIED — Platform's importer fixture passed 8 checks: PowerShell 5/7 timestamp
compatibility, a valid 4-asset release, deterministic pin/vendor/catalog update, an
expected-manifest mismatch rejection, staged-ZIP tamper rejection, source-asset
tamper rejection, extra-asset rejection, and an honest unpinned state. The committed
lock reports `State=unpinned`, `Assets=0`.

BLOCKED — This is not a published-lane I3 receipt. Comfy Quest has 0 tags and 0
GitHub releases. The production importer deliberately requires a published,
non-draft, non-prerelease GitHub release plus an independently obtained manifest
hash, so it correctly made no live pin from the local candidate.

### I4 — Platform corpus mirror to Baseline Pages

VERIFIED — Baseline reconstructed the 2-file mirror from pushed Platform revision
`d5128c03d1df5c2ab45adf042bcc7e8c48ad290b`, verified the exact hashes and byte
counts listed under G8, and regenerated all 13 projections. Hub CI run 31586644439
repeated the mirror and projection checks at Baseline
`39262cee83e2eb4148716be919be448aeed1b94e`; Pages run 31586644505 then deployed
that same revision successfully.

### I5 — headless Valheim boot with released DLL

BLOCKED — No published NetworkSense DLL exists, so the required released input to
`Invoke-HeadlessValheimLab.ps1 -ModDll <released-artifact>` is missing. The local I1
candidate is deliberately not being promoted to release evidence.

BLOCKED — A full headless boot would start or change a live Valheim lab and then
probe runtime identity. That live mutation was not authorized for this verification
pass. Consequently there is no claim that I5 booted, that a released DLL ran, or that
live `/identity` responses were observed in this lane.

## Publication and mutation boundary

VERIFIED — The five sovereign repositories have 0 GitHub releases. Comfy Quest,
Platform, Sovereign Shards, and Isolate have 0 Git tags; NetworkSense has exactly 1
non-release provenance tag, `split-base-20260811`. No product release tag was created.

VERIFIED — This phase created no NuGet publication and performed no game-client,
AM4, i5, P7, GCP, or Valheim-server deployment. The only deployment receipt in this
matrix is the already-authorized static Baseline Pages projection in I4.

BLOCKED — Public package pins, real release assets, I1/I3 published consumption, I2
manual gameplay, and I5 live boot remain downstream work. Their missing prerequisites
are recorded above; none is represented as VERIFIED by a local candidate or fixture.
