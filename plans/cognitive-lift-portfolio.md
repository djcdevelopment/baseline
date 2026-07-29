# Cognitive-Lift Portfolio — research → matrix → build order

Status: research in flight (3 web-research agents, 2026-07-29). This file receives their
ideas, scores them, and records the build order. Requested by Derek 2026-07-28: find 5–10
ways to lower his cognitive lift, deliver community value, and activate volunteers; matrix
them; build the top 5 most→least effective.

## Scoring model

Each idea scores 0–5 per criterion; weighted sum, max 65.

| # | Criterion | Weight | 5 means | 0 means |
|---|---|---|---|---|
| C1 | Cognitive-lift reduction | ×3.0 | Removes a whole class of Derek decisions/interrupts | Adds decisions |
| C2 | Recurring-cost inverse | ×2.5 | 0 (or negative) Derek min/week | Daily attention |
| C3 | Volunteer activation | ×2.5 | Converts lurkers → runners → owners | Spectator-only |
| C4 | Community value, soon | ×2.0 | Visible value within days of shipping | Value only after months |
| C5 | Build-cost inverse | ×1.5 | < 2 agent-hours | > 20 agent-hours |
| C6 | Stack leverage | ×1.5 | Pure reuse: Workbench/journal/HEARTH/cron/JSON→HTML | New surface to maintain |

**Hard gates (any FAIL = eliminated regardless of score):**
- G1 Honesty: cannot drift into overpromise or a botted/robotic community voice.
- G2 Async: no real-time Derek presence; batch-compatible with the ~2×/week rhythm.
- G3 Spend: ~$0 marginal (existing HEARTH/GCP/cron only).
- G4 Gate: anything outward-facing ships only via a Derek-approved batch.

## Ideas under evaluation

*(populated from research agents R1: solo-maintainer practices, R2: modding-community
patterns, R3: agent-automation leverage — with sources)*

### From R3 — agent-automation leverage (landed)

- **R3-1 Weekly quiet digest.** Cron agent reads `commit-notes.jsonl` since last digest +
  a DiscordChatExporter JSON pull of the workbench threads → one private markdown Derek
  reads in ~2 min instead of scrollback + git log. Internal-only (no publish gate needed).
  Min-signal threshold so dead weeks write nothing. Evidence: GitHub Agentic Workflows
  daily-status pattern (github.github.com/gh-aw), open-source Discord summarizer bots.
  Build ~3–4h · Derek ~2 min/wk (net negative vs manual). Risk: unread noise.
- **R3-2 Journal → Discord announcement draft.** HEARTH restates journal entries since the
  last announcement as a plain-language draft post; Derek edits/pastes on his existing
  batch rhythm. Prompt constrained to ONLY restate `summary`/`impact`/`verification` —
  no new superlatives, never auto-posted. Evidence: release-drafter / ai-changelog / GH
  "safe outputs" human-gate pattern. Build ~2–3h · Derek ~0 (replaces from-scratch
  writing). Risk: HIGHEST voice-drift risk — marketing register would read botted; the
  restate-only constraint is load-bearing.
- **R3-3 Scripted demo capture.** vhs `.tape` files (checked in per tool) render
  deterministic terminal GIFs for steward-view/telemetry/MCP; one OBS
  Advanced-Scene-Switcher hotkey macro for in-game clips. Evidence: charmbracelet/vhs +
  vhs-action; obs-websocket. Build ~2–3h · Derek ~5 min per new demo (not passive). Risk:
  silent staleness (GIF showing an old UI).
- **R3-4 Static FAQ from thread exports.** DiscordChatExporter (forum-thread mode) →
  HEARTH clusters recurring questions, pulls DEREK'S VERBATIM replies only → `faq.json`
  → third JSON→HTML page in the existing pattern; Derek-gated publish, monthly-ish.
  Evidence: DiscordChatExporter mature; FAQ-clustering half is thin/vendor-marketing.
  Build ~4–6h (incl. one-time bot setup) · Derek ~5–10 min/publish. Risk: misattributed
  answers — verbatim-only rule is load-bearing.
- **R3-5 Feedback → candidate-issues.jsonl.** Same export; HEARTH extracts bug/feature
  candidates into an append-only journal mirroring `commit-notes.jsonl` shape (evidence
  links to source messages); Derek promotes manually — nothing auto-filed. Evidence:
  Dosu/GH triage time-savings real, but all shipping products are live-bots (ruled out);
  batch variant is the fit. Build ~3–5h (shares plumbing with R3-1/4) · Derek ~10 min/wk
  (replaces scrollback). Risk: false negatives — position as second-pass net, dedupe by
  message ID.
- **Shared prerequisite R3-1/4/5:** one-time Discord Developer Portal bot app, read-only +
  read-message-history, scoped to the workbench forum category.

### From R1 — solo-maintainer practices (landed)

- **R1-1 Forum status tags for pre-batch triage.** Require member category tags on the
  #workbench forum (question/bug/claiming/feature); Derek or a Stage-3 Contributor applies
  status tags (needs-derek/answered/resolved); batch pass filters by `needs-derek` instead
  of reading everything. Evidence: practitioner guides (no rigorous study), triage
  principle corroborated by Homebrew + External Secrets burnout docs. Build ~0.5–1h ·
  Derek slightly NEGATIVE recurring. Risk: spotty member tagging degrades to status quo;
  never let tags become an auto-closer (stale-bot backlash documented).
- **R1-2 Per-tool FAQ block + saved replies.** Add an FAQ section to the one-pager
  template (recurring tool-specific questions, seeded from threads); native GitHub/Discord
  saved replies for Derek's 5–10 most-repeated answers. Evidence: Nuxt's documented
  Discord-support cost; GitHub saved-replies testimonials. Build ~1–2h + 10 min Derek
  setup · ~2 min/wk. Risk: FAQ rot — keep it inside the generator-synced one-pager, never
  a separate doc.
- **R1-3 Bias first tasks bug-fix-shaped.** One instruction line in the template: prefer
  small bug-fix-shaped bounded tasks. Evidence: 2026 longitudinal GFI study — only 27% of
  labeled issues ever get a newcomer PR; bug-fix tasks merge 68.7% vs ~54% features;
  review support (Derek) is the bottleneck, so don't over-expand task lists. Build ~15min
  · 0 recurring. Risk: correlational, from big projects; too-safe tasks may not hook.
- **R1-4 OWNERS.md → workbench.json sync script.** Parse new ledger entries, patch the
  matching tool's ownership block, wired into the existing check step; fail LOUDLY on
  parse mismatch. Removes a two-place hand-sync + a whole "ledger says X, page says Y"
  bug class. Evidence: all-contributors bot pattern; CNCF ladder-as-ledger convention.
  Build ~2–3h · NEGATIVE recurring. Risk: silent parser bug — must fail closed.
- **R1-5 Canned decline templates.** 2–3 pre-written "no/out-of-scope" replies (add
  feature X / repo access / when's it opening) + one personalization line each use.
  Evidence: Homebrew "no complaint outranks maintainer burnout", External Secrets
  request-vs-demand line, opensource.guide. Build ~30–45min · net time-POSITIVE. Risk:
  verbatim reuse reads cold in a small community — personalize every time.
- **R1-6 Pre-batch HEARTH digest of threads.** ≈ R3-1 (merge at matrix time). R1 flags:
  thinnest evidence of its set; only nets positive if the Discord export step is FULLY
  automated — half-automation is a new chore.
- **R1 cross-cutting:** first 30 days determine second contributions; first 12 weeks
  predict retention → fast triage (R1-1) + searchable answers (R1-2) outrank ladder
  redesign; the ladder itself matches CNCF's template structurally. Rejected up front:
  synchronous office hours (violates async), stale-bots (documented backlash).

### From R2 — modding-community patterns (landed)

- **R2-1 Forum channel + ladder tags** (merges with R1-1): one forum post per tool tagged
  with the EXISTING ladder states (Unclaimed/Trying/Claimed/Owned) + member tags; Stage-3
  Contributors re-tag their own tool. Timing finding: Discord cannot convert threads→forum
  later — cheap NOW (zero history), expensive after threads fill.
- **R2-2 Time-boxed test waves** via r2modman profile-code export/import (the real
  modding-world mechanism — no config hand-editing); ✅ reaction = opt-in roster; rides the
  existing changelog ritual. Aspirational until readiness gates open — template-in-waiting.
- **R2-3 "Already answered" one-pager section** (merges with R1-2): write the
  recurring-question line into the tool's one-pager as a byproduct of the existing
  feedback sweep.
- **R2-4/6 Showcase channel + themed contests**: native reaction-sort forum = zero-bot
  starboard; Jotunheim/Valheimians run exactly this (genre-proven). Empty channel reads
  sad — stage with the announcement, not before.
- **R2-5 Changelog credit line**: "thanks to <name> for X" when a shipped change traces to
  a stage-2+ ledger entry. Nexus-style visibility-as-reward; deliberately NOT a ranked
  contest (Nexus abandoned that for metric-gaming).
- **R2 sequencing:** structure edits (tags, FAQ section, credit line) are safe at
  zero-volunteer scale; people-dependent ideas (waves, showcase, contests) look inert or
  sad if stood up before the first volunteer clears the gates — stage as templates.

## Matrix

Dedup: 17 raw → 13 scored (R1-1+R2-1 merged; R1-6+R3-1 merged; R1-2+R2-3 merged;
R2-4+R2-6 merged). Weighted sum, max 65. All 13 pass gates G1–G4 as scoped (voice-risk
ideas carry a mandatory restate-only constraint + Derek gate; people-dependent ideas are
built as templates-in-waiting, announced only when a cohort exists).

| # | Idea | C1×3 | C2×2.5 | C3×2.5 | C4×2 | C5×1.5 | C6×1.5 | **Total** |
|---|---|---|---|---|---|---|---|---|
| 1 | Journal → announcement draft (R3-2) | 5 | 5 | 3 | 4 | 5 | 5 | **58.0** |
| 2 | Forum tags & ladder rendering (R1-1+R2-1) | 4 | 5 | 4 | 3 | 5 | 4 | **54.0** |
| 3 | Bug-fix-shaped first tasks (R1-3) | 2 | 5 | 5 | 2 | 5 | 5 | **50.0** |
| 4 | Per-tool FAQ + saved replies (R1-2+R2-3) | 4 | 4 | 2 | 2 | 5 | 5 | **46.0** |
| 5 | Feedback → candidate-issues.jsonl (R3-5) | 4 | 4 | 3 | 2 | 3 | 5 | **45.5** |
| 6= | Test-wave template (R2-2) | 3 | 4 | 4 | 1 | 5 | 4 | 44.5 |
| 6= | Changelog credit line (R2-5) | 1 | 5 | 4 | 2 | 5 | 5 | 44.5 |
| 8 | OWNERS→workbench.json sync (R1-4) | 3 | 5 | 2 | 2 | 4 | 5 | 44.0 |
| 9 | Quiet digest (R3-1+R1-6) | 4 | 5 | 1 | 2 | 3 | 5 | 43.0 |
| 10 | Showcase channel + contests (R2-4/6) | 1 | 5 | 4 | 3 | 5 | 2 | 42.0 |
| 11 | Canned decline templates (R1-5) | 4 | 5 | 1 | 1 | 5 | 3 | 41.0 |
| 12 | Scripted demo capture, vhs (R3-3) | 2 | 3 | 3 | 4 | 4 | 3 | 39.5 |
| 13 | Generated FAQ page from exports (R3-4) | 3 | 4 | 2 | 1 | 2 | 4 | 35.0 |

Reading the cut: the top 5 form a coherent portfolio — **writing-lift** (1), **triage-lift**
(2), **conversion odds** (3), **repeat-question deflection** (4), **signal capture** (5).
Ranks 6–13 are staged in this file as backlog; several (credit line, waves, showcase) are
deliberately parked until the first real volunteer exists, per R2's zero-cohort finding.
Rank 13's timing kills it now (nothing to cluster); revisit when threads have months of
history. Rank 12 (vhs demos) is the first thing to pull forward if "hard to show" pain
returns after the Workbench ships.

## Build order (top 5)

Most → least effective. No Derek time during builds; his touches land on DEREK-BATCH-1.

1. **Journal → announcement drafter** — `tools/workbench/New-AnnouncementDraft` reads
   journal entries since the last draft, emits a factual skeleton (works with HEARTH
   down), optionally smooths via HEARTH ollama under a restate-only prompt (no new
   claims/superlatives), writes `discord/drafts/<date>-announcement.md` marked NEVER
   AUTO-POSTED. State file tracks last-drafted entry.
2. **Forum tags & ladder rendering** — `discord/07-forum-tags-setup.md`: exact taxonomy
   (4 ladder states + question/bug/claiming/first-task-done + needs-derek/answered),
   click-path, and the do-it-at-creation timing note; pinned-post draft updated; Derek's
   single Discord session covers this + thread creation.
3. **Bug-fix-shaped first-task lens** — one instruction in `TEMPLATE-one-pager.md`
   citing the merge-rate evidence; applies to all future task authoring.
4. **Per-tool "Already answered" section + saved replies** — template section (inside the
   generator-synced one-pager, no separate doc) + `discord/08-saved-replies.md` starter
   set drafted from known friction (Python/openpyxl, download path, config path fix,
   invite process, soft-decline).
5. **Candidate-issues distiller** — `tools/workbench/distill_feedback.py`: DiscordChatExporter
   JSON → heuristic+HEARTH classify → append `candidate-issues.jsonl` (journal-shaped,
   message-ID dedupe, source links); fixture-tested with synthetic export; goes live after
   the one-time Discord bot setup (`discord/09-discord-bot-setup.md`). Nothing auto-files.
