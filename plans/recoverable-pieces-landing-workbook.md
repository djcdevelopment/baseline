# Recoverable pieces — find → land → document workbook

A strategy and step-by-step implementation workbook for recovering pruned
pieces back into `baseline` without taking away the community's claiming
tasks. First executed 2026-07-29 for the two `recoverable-not-running`
workbench tools (`quest-submission-bridge`, `camera-gallery`); written so
the next recovery — or a re-verification of this one — can follow the same
steps.

Every step row carries a **tier** (see the legend at the end): the point is
that deterministic tools and cheap models do the mechanical work, and
expensive judgment is spent only where judgment is the work.

## 1. Purpose and scope

**Posture: pave the path.** Land the revivable raw material in-repo,
byte-exact and unwired, with provenance recorded — so that a would-be
reviver starts from a `baseline` checkout instead of cross-repo
archaeology. The claiming tasks themselves stay open.

Out of scope, deliberately:

- **QB-1** (port `bridge_consumer.py` to the live mod's telemetry) and
  **CG-1** (revive segment 1) — those are the community's claiming tasks.
- Any wiring into `network/` (also keeps this work outside the background
  roadmap automation's force-push scope).
- Thunderstore packaging, new workbench downloads, or any status change —
  `recoverable-not-running` stays true until something runs.
- The root `waypoints.json` fossil (real coordinates + builder names):
  document, never spread.
- Posting to Discord — the seed file is updated in-repo; syncing it to the
  live forum is operator-gated.

## 2. Where the pieces are — three find-lanes

| Lane | What | How |
|---|---|---|
| L1 | baseline's own history | Pre-prune ref `57654fd` (= `d75ffb2^`; prune commit `d75ffb2`, 2026-07-21, "Prune 279 of 1045 tracked files after a Gemini-backed audit"). `git show 57654fd:handoffs/<p>` |
| L2 | the `comfy` remote, already configured in baseline | `comfy/main` = `ae81c83` — objects already fetched; `git cat-file blob ae81c83:handoffs/<p>` works offline |
| L3 | the public archive on GitHub | https://github.com/djcdevelopment/comfy/tree/main/handoffs — human-browsable |

L1 ≡ L2: `git rev-parse 57654fd:handoffs ae81c83:handoffs` → the same tree
`5d7b29bcd5d31b89a8b06785af11a8eb1de9743b`. The retired `C:\work\comfy`
checkout is **not** a lane (retired roots rule, `AGENTS.md`) — and working
trees smudge line endings, which is exactly what byte-exact recovery must
avoid. Recover from git *blobs*, never from a checkout's files.

## 3. The contract seams (why the bridge is "recoverable", not "broken")

Recorded from reading both halves; these seams **are** QB-1's content, not
defects to smooth over here:

- The live mod's proof of a quest completion is a durable **server-side
  EventLog entry** (`quest_completed`, relayed via HTTP POST
  `/valheim/events` from `GameplayEventProducer`) — there is **no local
  outbox file**. `bridge_consumer.py` expects the retired mod's outbox
  shape. The two halves speak different languages by design.
- `bridge_consumer.py` hard requirements (`validate_payload`, ~:56–110):
  `schema_version == 1`, `status == "ready_for_review"`, non-empty
  `evidence.screenshot`. A null screenshot **fails the whole batch**, not
  one payload — and the retired mod could emit null when an action needed
  no screenshot (a quest-view entry with `screenshots: 0`).
- `workflow.era` / `workflow.tier` type drift: the retired C# emitted JSON
  strings; the hand-authored demo fixtures carry numbers. The consumer is
  tolerant (untyped `.get`), so the inconsistency propagates silently into
  `state/*.json`.
- Rank validation fires only on `submission_type` ending `_rank_proof` —
  plain `rank_proof` fixtures bypass it.
- `notes` is always empty from the game; trace files and screenshots are
  path-echoed but never opened (no existence checks).

## 4. Migrate vs document — the decision record

| Material | Decision | Why |
|---|---|---|
| Python consumers, fixtures, briefs (both tools) | **Migrate** byte-exact | The raw material a claimant actually starts from; small, runnable, license-clean to carry with provenance |
| Retired C# `ComfyControlSurface` mod (incl. `SubmissionService.cs`) | **Document** (archive pointer) | Optional alternative path only; landing it would imply the old mod is coming back |
| `valheim-camera-proof/` plugin | **Document** (archive pointer) | Fetched by whoever takes segment 3; not needed for CG-1 |
| `mikers-demo/bridge-review/` outputs | **Regenerate, never migrate** | Never tracked in the archive, and nondeterministic (`utc_now()`, absolute paths) — committed goldens would be false precision |
| Root `waypoints.json` fossil | **Leave untouched** | Privacy-sensitive; already flagged on the camera card |

## 5. Piece → destination map

Pinned source: `SRC = ae81c83bee1a8077f15c211055dd0667ca50b469`.

**Rule 1:** `recipes/quest-submission-bridge/<p>` := blob
`SRC:handoffs/comfy-control-surface/<p>` — 15 files (QUEST.md, PROOF.md,
`bridge-consumer/` README + both consumers + fixture + mikers-demo trio,
`fixtures/` five contract fixtures, `generate-actions-from-rank-ladder.py`).
Full list in that folder's `PROVENANCE.md`.

**Rule 2:** `recipes/camera-gallery/<basename>` := blob
`SRC:handoffs/<basename>` — 9 files (segment-1 script + brief, segment 2/3/4
briefs + runner, `video_to_gallery.py`, both sample fixtures). Full list in
that folder's `PROVENANCE.md`.

Each landing dir additionally gets two authored files: `.gitattributes`
(`* -text`) and `PROVENANCE.md`.

## 6. Phase F1 — find and verify (all T0)

| Step | Command | Evidence of done (2026-07-29 run) |
|---|---|---|
| Resolve the refs | `git rev-parse d75ffb2^ 57654fd ae81c83 comfy/main` | `d75ffb2^` == `57654fd`; `comfy/main` == `ae81c83` |
| Tree identity | `git rev-parse 57654fd:handoffs ae81c83:handoffs` | both `5d7b29b…` |
| Clean start | `git status --porcelain` | empty |

## 7. Phase F2 — land byte-exact

| Step | Command | Tier | Evidence (2026-07-29) |
|---|---|---|---|
| Write `.gitattributes` **before** `git add` | `printf '* -text\n' > recipes/<dir>/.gitattributes` | T0 | present in both dirs |
| Copy from blobs, never a checkout | `git cat-file blob "$SRC:<src-path>" > recipes/<dir>/<p>` per file | T0 | 15 + 9 copies, zero failures |
| Stage | `git add recipes/<dir>` | T0 | — |
| **Prove byte-identity** | per file: `git rev-parse ":recipes/<dir>/<p>"` == `git rev-parse "$SRC:<src-path>"` | T0 | zero mismatches, both dirs |
| Draft `PROVENANCE.md` prose | brief with all shas/facts → cheap model draft → review | T1/T2 draft, T3 review | both files landed |
| Notices + recipes/README rows | edit `THIRD_PARTY_NOTICES.md`, `recipes/README.md` | T3 | landed in C1/C2 |
| Ceremony + commit | `npm run roadmap:note -- --milestone A7 --kind implementation …`; stage journal trio; `npm run roadmap:check -- --staged`; commit; `git pull --rebase`; push | T0/T3 | C1 `53897d5`, C2 `ef8409a` |

Line-ending facts, precisely: the archive **blobs are LF**. The danger runs
through checkouts — baseline has `core.autocrlf=true` and no root
`.gitattributes`, so files copied from a smudged working tree, or edited and
re-added without `-text`, would change blobs. `* -text` in the landing dir
plus blob-to-blob copying makes the sha proof above hold on any platform.

Windows: invoke Python by full path (the PATH `python` may be a Store
stub), and never round-trip landed bytes through PowerShell 5.1
`Get-Content`/`Set-Content`.

## 8. Phase F3 — documentation sync

| Step | Surface | Tier | Evidence (2026-07-29) |
|---|---|---|---|
| Fix wrong provenance ref | camera one-pager: `cc322ee` → `d75ffb2`/`57654fd` | T3 | C3 |
| Say where the pieces now are | both one-pagers + `workbench.json` `status_detail`/`recovery.notes`/`docs[]` — statuses and claiming tasks untouched | T3 (honesty invariants) | C3 |
| Complete the piece list | camera `recovery.paths` += the 4 real files it was missing | T0 (list diff) + T3 | C3 |
| In-repo run variants | both one-pagers' "run it" sections | T3 | C3 |
| Seed + handoff | dated update paragraph in Discord seed 06; dated addendum in the cold-pickup handoff | T2 draft, T3 review | C3 |
| Render + check | `npm run workbench:render` && `npm run workbench:check` | T0 | "Workbench OK: 7 tools … 2 recoverable, generated HTML current" |
| Ceremony + commit | as F2, kind `documentation` | T0/T3 | C3 `7b1dfc4` |

## 9. Phase F4 — verify and publish

| Step | Command | Tier |
|---|---|---|
| Re-run the sha proof against HEAD | loop `git rev-parse "HEAD:recipes/<dir>/<p>"` vs `"$SRC:<src>"` | T0 |
| Compile every landed script | `<python> -m py_compile` ×5 | T0 |
| Bridge smoke, temp out-dir | `bridge_consumer.py …\mikers-demo %TEMP%\qsb-smoke` → 1 payload; review md carries `rank:Thrall`; `review_inbox.py list/accept/export` → `/slayer submit …` draft; delete temp | T0 |
| Bridge smoke, contract fixture | same against `bridge-consumer\fixtures` | T0 |
| Camera dry run | `video_to_gallery.py flythrough.mp4 …\timeline.sample.json --dry-run --duration 60` (flags verified against its argparse) | T0 |
| Entry-point links | `python -m unittest` the repo's entrypoint-links test | T0 |
| Publish the page | the workbench publish script with the current host overrides; verify served hash against `X-Workbench-Sha256` | T0 |
| Forum sync | bot `plan` → receipt → **operator approves** → `apply`. Never auto. | gated |

## 10. Risks and traps (all hit or dodged on the first run)

- **Concurrent sessions commit to `main`** and background automation can
  force-push it for Gateway/`network/`/`infra/` changes: keep
  stage→check→commit windows tight, `git pull --rebase` before each push,
  never fight an automation push.
- **Checkout smudge** (see §7): copy from blobs, prove with shas — a
  narrative claim about line endings is worth nothing next to
  `git rev-parse` equality.
- **Honesty invariants**: the generator requires `recoverable-not-running`
  tools to stay `not-published`; landed-but-unwired must never be phrased
  as "runs".
- **Licensing lint**: the roadmap check fails notes containing
  "open source" — this repo's phrase is *public source (BSL 1.1)*. The
  landed copies stay MIT with the full text in each `PROVENANCE.md`.
- **Cheap-model truncation**: a mid-cloud drafting call that returns ~90
  tokens and stops mid-sentence is a parameter problem, not a model
  verdict — retry once with the output cap omitted before falling back to
  drafting inline. (Both PROVENANCE drafts succeeded on the retry.)
- **Nondeterministic goldens**: outputs carrying timestamps or absolute
  paths are smoke-tested with content assertions, never committed as
  byte-goldens.

## 11. Model-tier legend

| Tier | Meaning | Used for |
|---|---|---|
| T0 | Deterministic tooling (git, python, npm scripts) | copies, sha proofs, renders, smokes — anything with a checkable answer |
| T1 | Cheap local model | labeling, extraction, first-pass triage |
| T2 | Mid cloud model | bulk drafting from a fact sheet (PROVENANCE prose, update paragraphs), large-context extraction |
| T3 | Frontier model | wording that carries invariants (status honesty, license boundary), multi-file edits, judgment calls |

The operator's concrete backend mapping for T1/T2 lives outside this repo
on purpose. Rule of thumb: if a step's output can be *verified* by a T0
check, draft it at the cheapest tier that produces usable text; if a wrong
word changes what the repo promises, it's T3.

## Executed 2026-07-29 — result ledger

- C1 `53897d5` — quest-submission-bridge raw material landed (15 files,
  sha-proven).
- C2 `ef8409a` — camera-gallery raw material landed (9 files, sha-proven).
- C3 `7b1dfc4` — cards, catalog, seed, handoff synced; render + check
  green.
- C4 — this workbook.
- F4 evidence recorded in the roadmap journal note accompanying the
  verification run.
