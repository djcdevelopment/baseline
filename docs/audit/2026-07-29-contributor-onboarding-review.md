# Contributor-onboarding review — annotated (2026-07-29)

**Provenance:** run per Derek's review instrument
(`docs/audit/contributor-onboarding-review-brief.md`) by a deliberately **context-starved**
fresh-eyes reviewer (Fable agent, read-only, ~20-min time box, no session context — by
construction it knows nothing the repo doesn't say). Annotation layer by the session agent,
who triaged each finding against the live decision queue. Uncommitted like its audit
siblings, pending the `docs/audit/` decision (DEREK-BATCH-1 §1).

**Reviewer's bottom line, verbatim:** *"one of the most self-honest repositories I've
reviewed — it documents its own failures, pins its own pauses, and files decisions against
itself. Its weakness is the mirror image: it is written for its operator and his agents...
The path to contributor-readiness is not better code; it is separating the cockpit from the
front door."*

---

## Triage — what's genuinely new vs already queued

### NEW — material, nobody had these (Derek's radar)

| # | Finding | Why it matters | Suggested owner |
|---|---|---|---|
| N1 | **`ENDtoEND.txt` — 324 KB tracked raw Claude Code terminal transcript at repo root, operator email in the banner** | Privacy + front-door noise; if the repo ever goes public this ships history too (untracking alone doesn't scrub history — say so honestly) | Derek decision (untrack now; history-rewrite only if/when visibility changes) |
| N2 | **CLA gap structurally blocks the ladder's own promise.** `CONTRIBUTING.md`: no CLA published, "opening a pull request does not authorize its merge." But Workbench ladder stage 3 grants code access — a Steward's first landed change has no legal path to land | Resolve before the FIRST stage-2 volunteer, not before the announcement (catalog invites running, not PRs — but the ladder's top rungs are currently writable-in-name-only) | Derek (CLA text or DCO call); agent can draft either |
| N3 | **`infra/gcp/p7/README.md` publishes the live VM IP + "Steam-only, unlisted, password-free" + plain-HTTP gateway endpoint** | Latent while the repo is private; becomes a join-address broadcast the moment visibility changes. Belongs on the visibility-change checklist as a hard gate | Agent-fixable at visibility time; note now |
| N4 | **Four handoff surfaces, one stale** (`HANDOFF.md` 07-21 at root, `HANDOFF-2026-07-29.md`, `handoffs/`, `Lumberjacks/Handoff.md`) | Cold-pickup ambiguity — a fresh agent may grab the stale one | Agent-executable: banner/redirect the stale three at the current one |
| N5 | **Era-1 fiction docs unbannered**: `Lumberjacks/docs/getting-started.md` ("assemble the founding group"), `90-day-roadmap.md`, `12-step-success-plan.md`, `linkedin-article.md` | Newcomers acting on fiction; the stale-banner pattern already exists (quest-slice doc) — apply it | Agent-executable, sed-level |
| N6 | **~15 docs reference pruned paths**, incl. the fieldlab ADR README's own "Canon" line (`GROUND-TRUTH.md`, `TEST-PROGRAM.md` — both gone) | The decision index violates the repo's own ADR-0009 ethos; one footnote convention fixes the class | Agent-executable |
| N7 | **The licensing-phrase guard doesn't cover the register**: `DECISIONS-PENDING.md`'s resolved 07-23 item itself says "solo open-source working sample" | The exact phrase the roadmap guard rejects, living in a root doc the guard can't see | Agent-executable (append-only correction + optionally extend the lint) |
| N8 | **No SECURITY.md** while an (uncommitted) audit memo documents timing-unsafe key comparisons — there is no disclosure channel | Cheap, standard, expected before public | Agent-drafts, Derek approves |
| N9 | **Provenance reciprocity**: CONTRIBUTING requires contributors to disclose AI-generated material; the repo's own July history is agent work under a human identity | Mitigated going forward (today's journal notes are authored "Claude" + commit trailers); the backfill statement is a one-paragraph honesty move | Agent-drafts |

### KNOWN — already on the checklist/register (reviewer independently confirmed)

"Public source" vs private repo (DEREK-BATCH-1 §6) · roadmap `links[]` 404 (§5) ·
`waypoints.json` handles + comfy guild xlsx (§2) · StewardView proprietary license (§6) ·
`docs/audit/` uncommitted (§1 — reviewer's improvement #9 argues for commit-after-read,
same as the checklist) · force-pushed `main` (documented in AGENTS.md; the *outsider
branch-contract* framing is the new angle, relevant only at visibility change) ·
governance-decisions home (extends the open 2026-07-23 register item — reviewer says:
graduate resolved entries into a durable log, skip RFCs until a CLA exists).

### CONTEXT — accurate observations that are design, not defect

- *"A repo to read, not yet a repo to join — deliberately."* Correct and current policy:
  site-downloads-only, code access graduates per-piece at ladder stage 3. The actionable
  seam is N2 (the CLA), not the posture.
- **Improvement #1 (split cockpit from front door)** is right *for the public era*; today
  the audience IS the operator and his agents, and the root register/handoff placement is
  the established convention (retro skill, cold-pickup). File under visibility-change
  prep, not tonight's cleanup.
- Lumberjacks ADRs 0016–0018 as "tech-debt registers wearing ADR numbers" — style note,
  low priority.

## Reviewer's ranked top-10 (verbatim ROI order)

1. Split root: durable front door vs operator cockpit (public-era prep)
2. One-page START-HERE with live/paused/historical status per area
3. Banner the era-1 docs (N5)
4. Fix dangling pruned-path links, ADR canon first (N6)
5. Publish CLA or adopt DCO + SECURITY.md (N2, N8)
6. BUILDING.md consolidating the scattered build truth
7. Unified decision index + Project/Governance Decisions log
8. Written branch/push contract for outsiders (visibility-era)
9. Commit `docs/audit/` post-read as a dated audit trail
10. Glossary + extend the existing roadmap.mjs term-lint to it

## Suggested execution split

- **Agent-executable batch, no Derek time (say "run the cleanup batch"):** N4 stale-handoff
  banners, N5 era-1 banners, N6 pruned-path footnotes, N7 register correction, plus
  reviewer #2 (START-HERE page) and #6 (BUILDING.md consolidation) and #10 (glossary).
- **Derek decisions:** N1 ENDtoEND.txt, N2 CLA-vs-DCO, N8/N9 approve drafts, plus the
  already-queued checklist items the reviewer re-confirmed.
- **Visibility-change gate (file, don't do):** N3 IP/password-free scrub, root split (#1),
  branch contract (#8).

---

## Full review, verbatim

*(reviewer output follows unedited)*

# Fresh-Eyes Review — `C:\work\baseline` (2026-07-28)

Reviewer stance: newcomer, read-only, ~20 minutes, no prior context. Everything below cites files I actually opened.

## Carry-over questions

### What would prevent an experienced engineer from making their first pull request?

Five hard blockers, in the order I hit them:

1. **The project says not to.** `CONTRIBUTING.md` is explicit: no CLA is published yet, "opening a pull request does not authorize its merge," and "contributors should not send large patches expecting immediate acceptance." First PRs are structurally on hold by policy, not by accident.
2. **`main` is force-pushed by background automation.** `AGENTS.md` ("This journal runs as background automation — plan around it") and `HANDOFF-2026-07-29.md` both state that Gateway-/infra-touching work is auto-committed and pushed, and that "SHAs churn within a single session." I watched this live: the dirty working tree from the start of my session was clean by mid-review. A fork would rot in hours; a PR branch has no stable base.
3. **The commit ceremony is non-trivial and enforced.** Every non-merge commit must append a journal note and stage regenerated HTML (`AGENTS.md`, `Lumberjacks/docs/roadmap/README.md`), validated by `npm run roadmap:check -- --staged`, including a lint that fails commits containing the phrase "open source." A newcomer's first commit fails this ceremony unless they've read agent-facing docs.
4. **The build is environment-asymmetric and documented in the wrong place.** net9 services build inside an `sdk:9.0` container; the net48 mod builds on host dotnet 8 with a `-p:PluginOutputPath=` guard. This lives in `AGENTS.md`/`HANDOFF-2026-07-29.md` (agent handoffs), not in `CONTRIBUTING.md` or any BUILDING doc. There is no `.github/` or visible CI at root to tell you what will be checked.
5. **The repo is (currently) private while its own docs claim otherwise** — `DECISIONS-PENDING.md` (2026-07-28 item) records that `LICENSING.md` says "Baseline is public source" while the repo is private, and that public roadmap links 404. You cannot PR into a repo you cannot see.

### Which files would you add or reorganize?

**Add:** a published CLA or a DCO decision (promised by `CONTRIBUTING.md`), `SECURITY.md` (the uncommitted `docs/audit/2026-07-24-independent-36h-audit.md` flags timing-unsafe key comparisons and unauthenticated internal endpoints — there is no disclosure channel), a `BUILDING.md`/quickstart, a glossary, and a durable resolved-decisions log (see §4).

**Reorganize:** the root directory is a license suite interleaved with one operator's live desk. `HANDOFF.md` (stale, 07-21), `HANDOFF-2026-07-29.md`, `DEREK-BATCH-1.md`, `DECISIONS-PENDING.md`, `waypoints.json`, and especially `ENDtoEND.txt` — a **324 KB tracked raw Claude Code terminal transcript**, complete with the operator's email in the banner — all sit beside `LICENSE` and `README.md`. There are four handoff surfaces (`HANDOFF.md`, `HANDOFF-2026-07-29.md`, `handoffs/HANDOFF-LUMBERJACKS-PRIORITY-PATH.md`, `Lumberjacks/Handoff.md`). Consolidate handoffs into one dated directory; untrack the transcript.

**Archive-mark:** `Lumberjacks/docs/getting-started.md` opens with "Assemble the founding group... product/technical lead, backend lead, client lead" — team-formation fiction from a greenfield era, in a 727-commit solo repo. Same era: `90-day-roadmap.md`, `12-step-success-plan.md`, `linkedin-article.md`. `docs/quest-vertical-slice-architecture.md` already carries a stale-content banner via `docs/README.md`; the pattern exists, apply it.

### Which documentation is essential before announcing publicly?

1. Resolve the "public source" vs private-repo contradiction (`LICENSING.md` vs `DECISIONS-PENDING.md` 2026-07-28) and the roadmap-links-404 item.
2. The CLA text and workflow — otherwise the announcement invites contributions the project must refuse.
3. A data-hygiene pass: `waypoints.json` (tracked; `DEREK-BATCH-1.md` §2 says it carries real player handles), the public `comfy` repo's guild spreadsheets (registered decision), `ENDtoEND.txt`, and — nobody has flagged this one yet — `infra/gcp/p7/README.md` publishes the live VM's public IP with "Steam-only, unlisted, **password-free**" and a plain-HTTP Player Gateway endpoint. If the join address is meant to be semi-private, the README of a soon-public repo is the wrong place for it.
4. A build/run quickstart, and `SECURITY.md`.
5. A provenance statement: `CONTRIBUTING.md` requires contributors to disclose AI-generated material, while the audit memo notes 184/184 commits in one window attributed to a single human identity for largely agent-produced work. Reciprocate the disclosure standard before going public.

## 4. Architectural Documentation

There are **two ADR tracks with different scopes, numbering, and eras**, and no cross-index:

- `Lumberjacks/docs/adrs/0001–0020` — classic Nygard-format decisions for the greenfield engine (thin client, WebSocket/UDP transport, PostgreSQL event log). Solid, but 0016–0018 ("json-protocol-debt", "interpolation-debt") are tech-debt registers wearing ADR numbers.
- `fieldlab/docs/adr/0001–0013` — the Valheim netcode-replacement program. This track is genuinely excellent. Its `README.md` states the routing doctrine in one line ("a decision that changes how we'll decide → ADR here; a fact → memory; a how-to → a doc"), tracks status and program rung, and the ADRs practice what they preach: `0009-verify-against-an-independent-source.md` contains a same-day boxed self-correction of its own overclaim. That is rare and worth protecting.

**Are ADRs used appropriately?** Yes — better than most professional teams — *within* their tracks. The failures are at the seams:

- The fieldlab ADR index's "Canon" line points at `../../GROUND-TRUTH.md` and `../../TEST-PROGRAM.md`, **both missing** (pruned). The decision index's own ground-truth links are dead.
- A newcomer cannot tell which track governs which reality (the Lumberjacks track describes an engine that is now partly historical; fieldlab describes the live program).
- **Process/adoption/governance decisions have no home** — the project knows it: `DECISIONS-PENDING.md` (2026-07-23, "Adoption/process ADR home") says such decisions "currently land only in retro + memory + this register." Big calls — accepting force-pushed `main`, "document truth over fake substrate," licensing wording — live as checkbox lines and retro paragraphs.

**What belongs where:** architecture/method decisions → the two ADR tracks (correct today); pending operator calls → `DECISIONS-PENDING.md` (works well as an inbox); but **resolved** register entries should graduate into a durable *Project Decisions* log rather than dissolving into checked checkboxes with links into retros. Governance calls (repo visibility, data retention, licensing wording, the ComfyStewardView proprietary-license question in `HANDOFF-2026-07-29.md`) deserve their own thin track — they are neither architecture nor experiments.

**New document type?** Yes to a *Project/Governance Decisions* log (the register almost is one). **No to RFCs** — `CONTRIBUTING.md` currently forbids substantive external contribution, so an RFC process would be ceremony without an audience. Revisit only after the CLA ships. The retro → ADR pipeline (`fieldlab/retro/SESSION-RETRO-*.md` feeding ADRs) already functions; document the router in one place.

## 5. Operational Readiness

- **Broken links:** the fieldlab ADR canon links above; my grep found ~15 docs referencing pruned paths (`GROUND-TRUTH.md`, `TEST-PROGRAM.md`, `comfy-control-surface`, `program-status.json`), including `fieldlab/VALHEIM-NETCODE-REPLACEMENT-WORKLOG.md` and `docs/quest-vertical-slice-architecture.md`. Public roadmap JSON `links[]` 404 for outsiders (registered in `DECISIONS-PENDING.md`).
- **Private references:** absolute `C:\work\...` and `C:\Users\derek\...` paths throughout (`docs/governance-findings.md` header; `HANDOFF-2026-07-29.md` key-file index points at a plan file in the operator's home directory); tailnet SSH aliases (`i5`, `comfy-p7`) in `AGENTS.md`; the live server IP in `infra/gcp/p7/README.md`. `docs/baseline-vision-and-boundary.md` draws the Baseline-vs-HEARTH product boundary well — but root `AGENTS.md`/`CLAUDE.md` remain one person's cockpit config.
- **Licensing ambiguity:** the BUSL-1.1 + Community Steward grant suite (`LICENSE`, `LICENSING.md`, `COMMERCIAL.md`, `STEWARDSHIP.md`) is unusually coherent and well-drafted. The ambiguity is at the edges: "public source" claim vs private repo; `Lumberjacks/LICENSE.md` as a subtree license whose relationship to root `LICENSE` you must infer from one sentence in `LICENSING.md`; a proprietary/paid `ComfyStewardView` license inside the catalog (`HANDOFF-2026-07-29.md`); and the unpublished CLA.
- **Public data:** `waypoints.json` (real player handles, tracked), guild `.xlsx` in the public `comfy` repo (decision pending), `ENDtoEND.txt`, and the password-free server IP.
- **Documentation gaps:** no root build/run path, no SECURITY.md, no CoC, "getting started" doc that doesn't get you started.
- **Inconsistent terminology:** `network/README.md` still says this directory holds notes "behind the game-facing work elsewhere in `comfy`" — the repo hasn't been comfy for weeks. "Open source" vs the mandated "public source (BSL 1.1)" drifts even inside `DECISIONS-PENDING.md` (the resolved 2026-07-23 item calls baseline "a solo open-source working sample" — the exact phrase the `roadmap.mjs` guard now rejects). I-ladder vs M-milestones vs A-track is decodable only via `Lumberjacks/docs/roadmap/README.md` + the worklog.

## 6. Repository Health

**Alive — emphatically.** 670 commits in July 2026 (vs 51 in March, ~3/month in between), 15 commits on 2026-07-28 alone, and automation that committed files *during my review*. Not abandoned by any measure.

**Research-heavy and experimental at the frontier** — `fieldlab/` evidence trees, pre-registered hypotheses, honest "built, never run" labels (`fieldlab/experiments/patchload-ab/` via the handoff), the five-class result taxonomy noted in the audit memo.

**Operationally serious for exactly one deployment:** digest-pinned images, release bundles, rollback drills, and receipt-level acceptance evidence (75,112/75,112 acks in `infra/gcp/p7/README.md`). "Production-ready" in the sense of one production, one operator.

**Not contributor-friendly — deliberately, for now.** 727 commits across three aliases of one person; `CONTRIBUTING.md` holds patches; `main` is rewritten by robots. Net verdict: *a live solo research/operations cockpit of unusually high documentary integrity* — currently a repo to **read**, not yet a repo to **join**. The bones for contributor-friendliness (honesty invariants, evidence discipline, the Workbench one-pagers with an all-unclaimed `Lumberjacks/docs/workbench/OWNERS.md`) are visibly being built.

## 7. First-Time Contributor Simulation

**What I read first:** `README.md` (good: honest about the merge, the prune, and the four load-bearing areas) → `CONTRIBUTING.md` → `CLAUDE.md`, which routes to `AGENTS.md` → `HANDOFF-2026-07-29.md` → `fieldlab/NETCODE-MAP.md` and `network/README.md`.

**What confused me:** the comfy/baseline/Lumberjacks trinity and which docs describe which era; two ADR tracks; four handoff files; a root directory where `LICENSE` sits next to a 324 KB terminal transcript; a TEMP RULE in `AGENTS.md` expiring *tomorrow morning* (am I bound by it? does it apply to humans?); docs that lucidly describe content that no longer exists (`docs/README.md` spends its first paragraph on what was removed); `Lumberjacks/docs/getting-started.md` telling me to assemble a founding team.

**What impressed me:** `fieldlab/NETCODE-MAP.md` — a source-grounded decompilation map with method signatures, delegate-inlining analysis, and per-funnel hook points — is the best Valheim netcode document I have ever seen in a repo. ADR 0009's same-day self-correction. The roadmap machine (`Lumberjacks/scripts/roadmap.mjs`) with staged-commit enforcement and a *licensing-phrase lint*. `fieldlab/PINNED-networking-lane-2026-07.md` — pausing a lane with written resume conditions instead of letting it rot. Privacy-gated zip publishing (`tools/workbench/Test-WorkbenchZipPrivacy.ps1` chain per the handoff). The candor of `DECISIONS-PENDING.md` — this project files findings against *itself*.

**What would make me hesitate:** the force-pushed `main` (my branch has no stable base); no CLA to sign even if I wanted to; contributing into a BUSL + 8.5%-commercial structure before the CLA text exists; the flagged AI-provenance-under-human-identity pattern sitting in an *uncommitted* audit memo; and the pervasive sense that this repo is someone's running cockpit — pushing a commit here feels like rearranging a stranger's desk while they're at it.

## 8. High-Leverage Improvements (ranked)

1. **Split the root: durable front door vs operator cockpit.** Move `HANDOFF*.md`, `DEREK-BATCH-1.md`, `DECISIONS-PENDING.md`, `waypoints.json` into an `ops/` or dated `handoffs/` area; untrack `ENDtoEND.txt`. *ROI: the first screen a newcomer sees stops being 50% session state — pure cognitive-load relief, zero code.*
2. **One-page START-HERE map with per-area status: live / paused / historical.** The `README.md` four-areas list is 80% of it; add explicit status tags (fieldlab lane = PINNED, Lumberjacks era-1 engine docs = historical, P7 = live). *ROI: live-vs-legacy is the single largest source of newcomer confusion and one page kills it.*
3. **Banner the era-1/aspirational docs** (`Lumberjacks/docs/getting-started.md`, `90-day-roadmap.md`, `12-step-success-plan.md`) using the stale-content pattern `docs/README.md` already applies to the quest-slice doc. *ROI: prevents newcomers acting on fiction while preserving history — sed-level effort.*
4. **Fix the dangling pruned-path links**, starting with `fieldlab/docs/adr/README.md`'s dead canon line, using a standard "pruned 2026-07 — recoverable at `<commit>`" footnote. *ROI: the decision index currently violates the repo's own ADR 0009 ethos; ~15 files, one convention.*
5. **Publish the CLA (or adopt DCO) + add SECURITY.md.** *ROI: this is literally the gate `CONTRIBUTING.md` says blocks all first PRs; nothing else on this list matters for contributions until it exists.*
6. **Write BUILDING.md by consolidating what already exists** in `AGENTS.md`, `HANDOFF-2026-07-29.md`, and `Lumberjacks/docs/build-release-runbook.md` (container build, net48 guard flag, roadmap ceremony, what checks will fail you). *ROI: moves build truth out of agent handoffs and operator memory into the contributor path.*
7. **Unify the decision landscape:** one index covering both ADR tracks' scopes, plus the Project/Governance Decisions log that `DECISIONS-PENDING.md` (2026-07-23) already asks for; graduate resolved register entries into it. *ROI: decision archaeology currently spans two ADR dirs, retros, a register, and private memory; one router page collapses it.*
8. **Document the branch/push contract for outsiders** — either "main is machine-managed; contribute against tag X via workflow Y" or a plan to suspend the force-push automation for the public era (`AGENTS.md` currently documents it only as a warning to agents). *ROI: no navigation doc survives contact with rewritten history; contributors need the ground rules in writing.*
9. **Commit `docs/audit/` (post Derek's read) as a dated audit trail** — the 36h memo is exactly the systems-orientation a newcomer needs (subsystem map, cadence, risks, credits), and today it is invisible to git. *ROI: preserves historical context and doubles as onboarding material for free.*
10. **Ship the glossary and extend the existing `roadmap.mjs` term-lint** to it: comfy/baseline, P7/OMEN/i5, ZDO/AoI, I-ladder/M-/A-track, "public source (BSL 1.1)". *ROI: reuses a guard that already exists; ends the terminology drift that even the decisions register trips over.*

**Bottom line:** this is one of the most self-honest repositories I've reviewed — it documents its own failures, pins its own pauses, and files decisions against itself. Its weakness is the mirror image: it is written *for its operator and his agents*, and nearly every friction above is the residue of that audience. The path to contributor-readiness is not better code; it is separating the cockpit from the front door.
