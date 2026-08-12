# 05 — Baseline index and slimming report

Date: 2026-08-12

Slim commit: `39262cee83e2eb4148716be919be448aeed1b94e`

## Result

VERIFIED — Baseline was slimmed in place with ordinary Git deletions and pushed as
the fleet knowledge, evidence, corpus, and discovery hub. The slim commit is present
on `main`; its parent-to-commit comparison with rename detection disabled records
exactly 1,432 deletions, 3 additions, and 27 modifications. The resulting commit has
858 tracked files.

VERIFIED — No product implementation was copied back as a convenience build surface.
The final tree has zero tracked files below `Lumberjacks/`, `network/`, or
`infra/gcp/p7/`; it also has zero tracked files below the transferred live FieldLab
roots `fieldlab/docs/`, `fieldlab/autonomous/`, `fieldlab/scenarios/`, and
`fieldlab/routes/`. The moved deployment, packaging, Workbench, authority-lab,
guest-package, and Quest tool roots likewise resolve to zero tracked files.

## Final tracked-tree counts

VERIFIED — `git ls-tree -r --name-only 39262cee83e2...` produces the following exact
top-level distribution:

| Root | Status | Tracked files |
|---|---|---:|
| repository root | VERIFIED | 15 |
| `.github/` | VERIFIED | 2 |
| `corpus/` | VERIFIED | 8 |
| `data/` | VERIFIED | 25 |
| `docs/` | VERIFIED | 86 |
| `erasave/` | VERIFIED | 2 |
| `fieldlab/` | VERIFIED | 563 |
| `handoffs/` | VERIFIED | 1 |
| `plans/` | VERIFIED | 41 |
| `recipes/` | VERIFIED | 35 |
| `site/` | VERIFIED | 21 |
| `tests/` | VERIFIED | 2 |
| `tools/` | VERIFIED | 57 |
| **Total** | **VERIFIED** | **858** |

VERIFIED — The retained FieldLab material is historical evidence and reconstruction
input, not a second live harness. Exact prefix counts are 72 files under
`fieldlab/evidence/`, 242 under `fieldlab/experiments/`, 12 under
`fieldlab/retro/`, and 212 under `fieldlab/runs/`. The remaining FieldLab files are
the frozen register, status/index material, integration receipts, root findings and
maps, and the evidence dashboard renderer.

## Hub authority and local residue

VERIFIED — The root `README.md`, `AGENTS.md`, `REPO-MAP.md`, and `docs/PORTS.md` now
describe the sovereign fleet and its package/artifact boundaries. PD-9 is the
canonical split decision; the decision index and the PD-5, PD-6, PD-7, and PD-8
dispositions point implementation authority to the owning repositories. Baseline no
longer carries the platform roadmap hook or root NuGet source configuration.

VERIFIED — MCP source authority moved to `isolate`: `network/mcp/` is absent from the
tracked tree, while Baseline's `.mcp.json` is only a client registration for the
canonical isolate endpoint `http://127.0.0.1:8722/mcp`. PD-8 records the completed
reconciliation and its original 24-test isolate receipt; the final verification
matrix records the later 25-test identity-helper regression suite.

VERIFIED — Operator-owned generated/runtime bytes were not deleted as part of the
tracked-tree split. `.gitignore` explicitly keeps `node_modules/`,
`fieldlab/autonomous/state/`, `network/mcp/var/`, Companion `dist/`, and the local
Companion compose override outside authority. At slim validation time,
`tools/selfie-stick/__marimo__/` remained the sole visible untracked path and was
preserved untouched. Removing any of this local residue is a separate operator
cleanup decision.

## Immutable Platform corpus mirror

VERIFIED — The Lumberjacks corpus reconstruction input is pinned to the already
pushed 40-character `lumberjacks-platform` revision
`d5128c03d1df5c2ab45adf042bcc7e8c48ad290b`. The v1 provenance receipt records the
upstream repository, revision, paths, raw revision URLs, byte counts, and SHA-256
digests:

| Mirrored input | Status | Bytes | SHA-256 |
|---|---|---:|---|
| `commit-notes.jsonl` | VERIFIED | 575,644 | `058bd784005800b59465b76a1ca1b875b17f0bcacd1d4db68840d75334358a2a` |
| `workbench.json` | VERIFIED | 42,176 | `e4f9a9e5a786dd5e7eb20f775358e2b2b2b5e2ae9e68cfe70e37c2fc09704970` |

VERIFIED — Mirror sync check and corpus build check both passed against that exact
revision. The builder reported `corpus projections match 13 deterministic outputs`:
the normalized index, Explore page, Updates page, RSS feed, JSON feed, and eight
audience pages. `tools/corpus/test_corpus.py` ran 8 tests successfully, including G8
provenance rejection paths rather than only the positive reconstruction path.

VERIFIED — The supported entrypoint-link audit ran 1 test successfully. A broader
retained-history audit separately classified 13 unresolved references as pre-existing
evidence gaps, not deletions introduced by the split: one worklog target, one MP4,
and eleven evidence targets were already absent. No sovereign current-target or
immutable pre-split-history link was missing.

BLOCKED — The 13 historical evidence gaps cannot be repaired without the absent
source artifacts and were deliberately not replaced with invented receipts. They do
not block the hub checks or Pages build.

BLOCKED — `data/processed/quest-picker.html` remains a clearly labeled historical
snapshot. Refreshing it requires a real tagged Comfy Quest release asset plus its
manifest, byte count, and SHA-256 proof; no such release exists yet, so the local
candidate was not promoted or presented as release-backed.

## Hosted verification

VERIFIED — [Hub CI run 31586644439](https://github.com/djcdevelopment/baseline/actions/runs/31586644439)
completed successfully at head
`39262cee83e2eb4148716be919be448aeed1b94e`.

VERIFIED — [Pages run 31586644505](https://github.com/djcdevelopment/baseline/actions/runs/31586644505)
completed successfully at the same head, proving the pinned mirror and regenerated
public projections land together.

INFERRED — The zero-count implementation roots, immutable corpus receipt, green hub
guards, and green hosted publication lane jointly support PD-9's intended steady
state: Baseline is the fleet's durable map and evidence hub, while product builds,
release ceremony, and live infrastructure remain independently owned.
