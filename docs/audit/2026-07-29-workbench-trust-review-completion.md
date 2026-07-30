# Community Workbench trust review — completion report

**Date:** 2026-07-29 · **Source mandate:** `community-workbench-trust-review-prompt.docx` (repo root)
· **Live surface:** https://am4.tail8e749c.ts.net/workbench

Nine sections of the review, what landed for each, and what remains for the operator. Commits:
`29e2698` + `68fb03b` (provenance pair), `9828ff0` + `5acdad4` (actionability pair), `35e66ed`
(verify-live), `3c7cc11` (token resolution), `a3e14a2` + `3424335` (policy-copy pair), plus the
docs commit carrying this report. History may be rewritten by the background automation; the
roadmap journal notes (milestone A7, 2026-07-29 15:34–16:00 UTC) are the durable record.

## 1. The contradiction found, and how it was resolved (§1)

**Found exactly as described:** `mcp-mod-channel.discussion.href` was `null` while MC-1's
`done_when` required the result "in the thread" — an uncompletable task, still counted and
presented as open. No thread existed on the Discord side either (`provision-state.json` had no
mcp-mod-channel entry), and the defect was duplicated in the one-pager
(`docs/workbench/tools/mcp-mod-channel.md`).

**Resolution (descending-preference options a+b combined):**
- **(b) shipped now:** MC-1 carries `completion: {destination_kind:"main-forum", href:null,
  state:"actionable"}`; its `done_when` says honestly that the list is posted in the #workbench
  forum because the tool's own thread has not opened yet; the card's Discuss row renders a real
  link — "no thread yet — post in the #workbench forum" → the live forum. Verified live: the
  `task MC-1 destination is live` check passes against the Discord API.
- **(a) prepped for the operator:** seed `10-thread-seed-mcp-mod-channel.md` + a
  `provision.json` posts entry (bot self-test 87/87; the bot now resolves `<ACCESS-URL>` from
  `source.href` for not-published tools). Derek's next `plan`/`apply` creates the thread; then
  Recipe A in `HANDOFF-2026-07-29.md` fills `discussion.href`, deletes the override, and rewords
  `done_when` back to the thread.
- **(c) available in schema:** `state:"blocked"` + `blocked_reason` exists, renders visibly, and
  is excluded from the count — MC-1 did not need it.

The generator's hardcoded inert-row text "thread opens with the announcement" (stale — the
announcement had already shipped) became "no thread yet".

## 2. Schema changes (§1–§2)

Optional per-task `completion` object: `destination_kind` (`tool-thread` | `main-forum`),
`state` (`actionable` | `blocked`), `href` (**must be null** — destinations derive from
`discussion.href` / `feedback.forum_href`, never typed twice), `blocked_reason` (required iff
blocked). When absent, the derivation default is tool-thread/actionable from `discussion.href`
— and **a null `discussion.href` is a build failure naming the three options**, never a silent
downgrade. A blocked task cannot be `suggested`.

## 3. How the counts compute, and the final count (§2)

`computeTaskCounts()` (exported, `scripts/workbench.mjs`) resolves every task through
`resolveTaskCompletion()`: **present** = listed in `first_tasks`; **actionable** = resolves to
state `actionable` with a live-derivable destination; **blocked** = explicit blocked state.
Hero, per-card header, and index rows all consume the same computation; the hero appends
"· N blocked" only when nonzero. **Final count: 11 first tasks, 11 actionable, 0 blocked** —
the same 11 the page showed before, but now true: every one of the 11 has a verified-live
destination (see §9).

## 4. Provenance (§3)

**Defect confirmed live:** the committed page said "Rendered 2026-07-29 11:50 UTC from an
uncommitted working tree" while the tree was clean (inputs committed at `7b1dfc4`, 11:50:33
UTC — the stamp recorded the renderer's pre-commit state and went false the moment the commit
landed). `check()` was structurally blind to it: `normaliseFreshness()` blanked the span before
comparison.

**Now:** one authoritative provenance path (`provenance()`), two modes scoped to the inputs
(`docs/workbench/workbench.json` + `scripts/workbench.mjs`):
- **Production** (inputs clean): `Published from a3e14a2 · 2026-07-29 15:57 UTC` — the last
  commit touching the inputs (SHA sliced in JS, not `%h`, so `core.abbrev` cannot vary it) and
  that commit's committer timestamp. Fully deterministic: `check()` compares the artifact
  **byte-for-byte including the stamp**.
- **Preview** (inputs dirty): `Preview rendered 2026-07-29 15:30 UTC with uncommitted changes`
  — inspectable locally, never publishable.

Asymmetric guards close both false states: preview stamp in a clean tree fails check (the
shipped defect, reproduced byte-for-byte as negative test 5); production stamp over dirty
inputs fails check (negative test 4). Publish Gate 0 independently refuses dirty inputs or a
stamp-less page. The commit flow is now a pair (inputs → render → HTML); `HANDOFF-2026-07-29.md`
and `BUILDING.md` carry the recipe.

## 5. Copy derived from structured policy (§4–§5)

The 108-character access-policy sentence, byte-identical in three `source.note`s with a
near-duplicate in a fourth, is deleted from the data. `accessPolicyLine()` derives the sentence
per card from `source.kind` + `contribution.code_contributions` (6 tools grant commit access at
stage 3; steward-view honestly does not). Notes keep tool-specific facts only, enforced two
ways (ordered so the sharper message wins): a **contradiction check** (`commit access` in a
note while `code_contributions:false`) and a **policy-vocabulary ban**.

Operator identity: ladder stage 4 says **"the project operator agrees you are the person
holding it"** (the review's preferred wording); `OWNERS.md` — linked at every ladder mention —
now defines the operator once (Derek, `djcdevelopment`, why the role has authority) and its
stage-4 row matches. A `\bDerek\b` anywhere in `workbench.json` is a build failure. The
rendered page contains zero person names. First-person authored content (`00-announcement.md`
signatures, drafts) deliberately keeps its byline — that is a signature, not governance prose.

Adjacent fixes in the same class: `LICENSING.md` (named 6×, linked 0×) now auto-links via
`linkLicensing()` with a named==linked check mirroring the OWNERS.md rule; four inert doc rows
naming now-public files carry real hrefs (verified live); a headline tool count disagreeing
with `tools.length` and any hardcoded task-count prose are build failures.

## 6. New offline guards (workbench:check / validate) — complete list

1. Thread-completing task with null `discussion.href` and no `completion` → fail (3 options named)
2. `completion` shape: enum destination/state, authored `href` must be null, `blocked_reason`
   iff blocked, blocked ⇒ never `suggested`, actionable ⇒ destination must resolve
3. Headline tool count must match `tools.length` (words one–twelve or digits)
4. Hardcoded task-count prose anywhere in the JSON → fail
5. `source.note` contradiction (commit access vs `code_contributions:false`) → fail
6. `source.note` policy vocabulary → fail
7. `\bDerek\b` (any person name guard) in the catalog → fail
8. `LICENSING.md` named == linked in the rendered page
9. Clean tree: byte-exact artifact compare **including** the stamp; preview stamp → fail
10. Dirty inputs: production stamp in the artifact → fail
11. `check` refuses without a git checkout (provenance unverifiable)
12. Publish Gate 0 (`Publish-WorkbenchAssets.ps1`): porcelain-clean inputs + `Published from`
    stamp required before any upload

## 7. New publish-time remote checks (workbench:verify-live) — complete list

Classes: `discord` | `github` | `routes` | `downloads` | `served-artifact`; JSON receipt at
`captures/workbench-verify-live.json`; `--pre-publish` runs as publish Gate 4, `--post-publish`
after upload. **Discord:** invite resolves (unauthenticated API), targets guild
`1531911987074957442`, not expired (fails expired, warns ≤14 days), expiry matches
provision-state; every member-only URL names the expected guild and resolves via the bot token
(fail-closed when the token is missing; `--allow-unverified-threads` downgrades; token
resolution mirrors the provisioning bot's); threads must parent to the #workbench forum;
archived threads warn; every task's resolved destination must be among the verified-live URLs.
**GitHub:** every `djcdevelopment` URL in catalog + footer answers 200; every declared-public
repo is API-verified `private:false`. **Routes:** the six nav routes + `/join` + `/health`
answer 200 on-origin (off-origin redirect = auth-gate failure). **Downloads (post):** each
site-download streams with exact `size_bytes`, exact SHA-256, and a matching
`X-Download-Sha256`. **Served artifact (post):** `X-Workbench-Sha256` equals the local
committed render's hash.

## 8. Negative tests — the guards are load-bearing (28 total, all green)

`npm run workbench:test` = 19 generator cases + 9 verifier cases. The ten mandated negatives,
each asserting its specific failure then restoring and proving byte-identical deterministic
re-render: (1) thread task + null href → three-options message; (2) blocked task excluded from
the hero, rendered visibly, and a hand-tampered hero count fails the byte compare; (3) wrong
headline count and hardcoded count prose → their lint messages; (4) production stamp over dirty
inputs → its message; (5) preview stamp in a clean tree → its message (the live defect,
reproduced); (6) note promising commit access vs `code_contributions:false` → contradiction
message, distinct from the vocabulary ban; (7) 404 deep link → `github` class names the URL;
(8) valid-shaped expired invite → `discord` class "invite expired"; (9) wrong-guild thread →
`discord` class names both guilds; (10) wrong-digest and truncated downloads → `downloads`
class digest/size messages. Plus: missing-token fail-closed vs downgrade, off-origin redirect,
pre-publish scope, green-path world, completion derivation matrix, LICENSING parity negative,
person-name ban, and pins on the two strongest pre-existing guards.

## 9. Destination status (live run, 2026-07-29 15:59 UTC, pre-publish)

**PASS — 60 checks, 0 failed, 0 warnings** (receipt: `captures/workbench-verify-live.json`).
Invite `discord.gg/TSHTD38yV` resolves to the expected guild, expires 2026-08-28 (matches
provision-state; the build starts warning 2026-08-14 — regenerating as never-expiring remains
recommended). All 8 member-only destinations live and correctly parented; all 11 task
destinations verified (MC-1 → forum). All 28 GitHub URLs 200 including the four newly linked
docs; `baseline`, `Lumberjacks`, `comfy`, `ComfyStewardView` all API-confirmed public. All 8
AM4 routes 200 on-origin.

## 10. Not verified, and why

- **Downloads and served-page hash** (post-publish classes): the live AM4 page still serves the
  pre-review render — nothing new was published this session. They verify the moment Derek
  republishes (`Publish-WorkbenchAssets.ps1` with his AM4 overrides now runs the full pass
  itself).
- **The `tools.json` pointer** is not publicly served; its shape is proven offline (Gate 3 +
  the xunit contract tests) and behaviorally (wrong pointer ⇒ 503, tested).
- **`.NET gateway suite** not re-run: no C# was touched; the container run remains a
  pre-release step.

## 11. Preserved decisions (§7) and provenance of this work

Tools-before-ladder, the dense index, card action rows, always-visible status_detail /
requirements / digests, `not_a_verdict`, "RECOVERABLE · NOT RUNNING", inert rows for genuinely
absent destinations, licence descriptions, per-tool stage-3 rights, reply language, the print
note, JSON → generator → HTML ownership, and download primacy are all untouched — the diff
to the rendered page is: the stamp line, the Discuss row for one tool, blocked-rendering
capability (unused at 0 blocked), seven derived access-policy sentences, linked LICENSING.md
mentions, four doc links, and one word in the ladder. No response-time promise reappeared.
1280×800 fold: unchanged except the stamp text (verified in the browser pane).

Work provenance: one HEARTH flash offload (gcp-gemini, 273 tokens out, truncated — the known
clipping) drafted the Discord seed; it was finished and corrected inline (one invented
capability removed). All generator, verifier, and test logic was written frontier-side. A
pre-existing stray NUL byte in `workbench.mjs` (made ripgrep treat the generator as binary) was
fixed in passing.

## Operator actions pending

1. **Republish to AM4** (your overrides + `Publish-WorkbenchAssets.ps1`) — the script now
   refuses preview artifacts, verifies live destinations first, and runs the full post-publish
   pass. Until then the public page shows the pre-review render, false stamp included.
2. **Create the MCP Mod Channel thread**: `workbench_discord.py plan` → approve receipt →
   `apply` (needs `--site-base-url https://am4.tail8e749c.ts.net` for the link-carrying seed) →
   then Recipe A in the HANDOFF (fill `discussion.href`, drop MC-1's override, two-phase land).
3. **Invite expiry 2026-08-28**: regenerate as never-expiring when convenient; builds warn from
   2026-08-14.
