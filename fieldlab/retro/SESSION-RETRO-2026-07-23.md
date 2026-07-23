# Session retro — 2026-07-23

## One-line
**Executed the `/plans/` adoption backlog as an offload-orchestration loop — HEARTH gemini-pro
drafted the prose, I supplied the grounding and adversarially verified every draft — shipping M1
(Trust & Rhythm) + two M2 docs + an A1–A6 roadmap track, while discovering the repo's background
automation force-pushes and rewrites `main` mid-session.**

## What this session was
A **document-heavy, orchestration-and-verification** session — the deliberate inverse of last
session's build-and-humility arc. The ask was "leverage HEARTH to do the lifting; you orchestrate and
verify quality," and that's what the shape was: 6 offloaded drafts, 5 subagents (3 recon + 2
adversarial verify), me as the grounding + QA gate, and Derek pacing the scope/gap/publish calls. Two
things made it more than a doc mill: a recon pass that found five false premises in the plans before we
built on them, and a mid-session discovery about how this repo's git automation actually behaves.

## What shipped

My commits (the repo also carries ~15 interleaved background-automation "Companion" commits that are
**not** mine — see the Operator seat):

| Commit | What |
|---|---|
| `237eac8` + `3924ad4` | M1-1 Data & Trust — `docs/data-and-trust.md` (every field grep-cited) + a served `/data-and-trust` page (`DataTrustEndpoints.cs`, `data-and-trust.html`), linked from `/community` + onboarding; `playerId`→`actor_id` fix. Auto-committed by the repo automation as "gateway releases". |
| `8c400b0` | M1-2/3/4 — `docs/alpha-expectations.md`, `weekly-rhythm.md`, `stream-ops-hygiene.md`, `docs/templates/{changelog-entry,session-residue,feedback-triage,status-down}.md`, two honest `docs/residue/` skeletons |
| `74f7572` | Note in root `AGENTS.md` documenting the background auto-commit/force-push automation |
| `47bc78f` | M2-1 `network/tuning-ledger.md` (netcode knob inventory, grep-verified) + M2-3 `gm-interview-guide.md` / `gm-interview.md` / `governance-findings.md` + a `telemetry-v0.md` public-allow-list fix |
| `cd5755b` | A1–A6 adoption milestone track added to the volunteer roadmap JSON (published, rendered, journaled) |

**Durable artifacts:** the ~13 docs above; `network/tuning-ledger.md`; the served `/data-and-trust`
page + its endpoint; the A1–A6 adoption track in the living roadmap; memory
`baseline-repo-auto-commits-and-pushes-main`; this retro + `DECISIONS-PENDING.md`.

## Timeline
- Plan-mode recon: 3 parallel Explore agents read the substrate before touching it and found **five
  reality gaps** the `/plans/` assumed away — no committed session-telemetry JSONL, "config signing"
  is a keyless SHA-256 checksum (not crypto), the M4 turnkey lab is entirely greenfield, the
  plans/README conflated two different "gateways", and several quest-slice doc paths are stale. These
  reshaped M3/M4/M6 and justified stopping at M1.
- Derek scoped to **M1 only**, with three standing calls: document the truth, never fabricate
  substrate to pass an acceptance check, and commit per milestone.
- Executed M1 via the offload loop — HEARTH `gcp-gemini-pro` drafted each doc, I supplied verified
  grounding (real captured-field names, the secret inventory, the log paths) and integrated. Wired
  M1-1 into `Game.Gateway`; verified with a green build in the `sdk:9.0` container.
- **Discovered the automation:** staging M1-1 found "nothing to commit." Investigation showed the repo
  runs background automation that auto-commits Gateway-touching work as "gateway releases",
  **force-pushes `main`, and rewrites history mid-session** — it had absorbed my commits and orphaned a
  feature branch I'd created. Derek: keep it, document the learning, don't rewrite. Pushed the
  `AGENTS.md` note + wrote the memory.
- Ran **2 adversarial-verify Explore agents** on the M1/M2 drafts before commit; they caught four real
  defects — a missing "who do I tell" report destination, an unresolved secret-rotation placeholder, a
  `playerId`/`actor_id` imprecision, and that `quest_completed` needs a *second* gate
  (`questEvaluatorEnabled`). Fixed all.
- Grounding win: verified gameplay capture ships **OFF by default** (`gameplayEventProducerEnabled=false`)
  — the trust note's opt-in story is real, not aspirational.
- Derek adjusted mid-turn: keep a running decision log, and always give a recommendation-with-reasoning
  when asking a question.
- Recommendations pass, then M2-1 + M2-3 + a `telemetry-v0.md` fix. Hand-authored the precision-critical
  knob table (line numbers matter); offloaded the GM-guide prose.
- Fixed the journal taxonomy: added an **A1–A6 adoption track** to the roadmap JSON. Paused before
  rendering to ask about public visibility (the JSON drives the public `/roadmap`); Derek chose to
  publish, so I re-toned it volunteer-facing, rendered, journaled, and pushed.
- Provenance discipline throughout: confirmed every offload's backend/model from the result metadata
  (`gcp-gemini-pro` / `gemini-3.1-pro-preview`), not the model's self-report.

## The team retro — our collaboration across the seats

Two seats, heavily augmented execution. **Claude** held the whole, orchestrated the offload fleet + all
verification, and did every repo write. **Derek** paced, made the scope/gap/publish calls, and steered
mid-course (the decision log and recommendations-with-reasoning).

**Architect (Claude drove recon; Derek decided scope).** Recon did its job: the 3-agent parallel read
caught five discrepancies before we built on them, and Derek's scope-to-M1 call was the correct
response to the findings. The adoption program's shape was dictated by *platform reality* (what
actually exists in the checkout), not by the plans' optimism. *What went well:* refusing to fabricate
substrate to satisfy a flawed brief. *What to change:* nothing here — reading ground truth before
building is exactly the habit we wanted.

**Implementer (Claude drove; HEARTH lifted).** 6 `local_generate` offloads, all `ok:true` on
`gcp-gemini-pro`, edit verdicts faithful/minor-fixes. The routing call held up: Pro for heavy prose,
avoid Flash (truncation), and **hand-author the precision-critical M2-1 table** rather than risk an LLM
mangling line numbers. Large legible output, cheaply. *What to change:* carry the "offload prose,
hand-write anything where a wrong line-number or value is a defect" split as a standing practice.

**Reviewer / QA (Claude drove).** The headline, and this time it's flattering: a clean reversal of last
session. I labeled verified/inferred/gap throughout and ran **independent adversarial verification**
before commit — the two agents caught four specific defects I'd otherwise have shipped, and grounding
`gameplayEventProducerEnabled=false` proved the trust doc wasn't lying. Last session's calibration
lesson was *active*. *What to change:* make an adversarial pre-commit pass the default for any
externally-facing policy/trust doc.

**Operator / SRE (Claude drove; the "infra" was git + the offload fleet).** The substrate this session
was version control and LLM fleets, not live P7. Stumbling into automation that force-pushes and
rewrites `main` mid-session was jarring — and it cost real cycles to diagnose ("why is staging empty?").
*What went well:* we didn't fight it — documented the force-push behavior in `AGENTS.md` + memory,
adapted the commit flow, and stayed out of the shared journal files during the automation's writes.
*What to change:* a **branching/automation reality check at session start** on this repo (is background
git automation running? does it push `main`?) would have turned a mid-session surprise into a known
constraint.

**Product / Planning (Claude drove; Derek decided).** Real organizational value: raw plan text became a
structured, published A1–A6 adoption track, and M1 + two M2 docs are done and legible. Derek's
mid-session process injection — the running decision log and "recommendations with reasoning" — tightened
the loop immediately and stopped me from handing over raw facts without a synthesized path. *What to
change:* hold that format as a standing default so it doesn't need re-asking.

## Two seats, two views

**From Claude's seat.** The offload loop worked exactly as intended — I stayed the grounding-and-QA
gate while the fleet did the drafting, and nothing shipped un-verified. The calibration standard from
last time held under a very different workload. Where I under-reached: I let the git-automation mystery
consume investigation cycles mid-flow; a cheap up-front probe ("does this repo auto-push `main`?")
would have pre-empted it. What I'd want next time: a session-start automation/CI check on unfamiliar or
automation-heavy repos, so background force-pushes are a known constraint, not a surprise.

**From Derek's seat (my reconstruction — correct me).** "This is the mode I wanted: use the fleet for
the lifting, but *you* own the grounding and the quality gate — and you did, the adversarial passes
earned their keep. You kept me in the loop with the decision log and gave me recommendations, not just
facts, which is how I actually want to drive. You refused to fake substrate and you flagged the
public-render before it bit us — good instincts on both. The automation tangle ate some time, but you
documented it instead of fighting it, which is the right call. Confidence matched the evidence this
session. Keep it there."

## Last time's lessons — follow-through
| Lesson | Status |
|---|---|
| `L-2026-07-22-1` — calibration standard: label verified/inferred/guessing; don't let a prior hypothesis pre-decide the read | **acted-on** (labeled verified/inferred/gap throughout; ran 2 adversarial-verify passes; paused to ask before the public-render action) |
| `L-2026-07-22-2` — diff config before theorizing on a two-client divergence | n/a (no live divergence this session) |
| `L-2026-07-22-3` — co-presence bug's live status is UNKNOWN; re-examine before arming the fan-out | **pending** (netcode work; surfaced only as `pre-ledger` context in the tuning ledger) |
| `L-2026-07-22-4` — P7 terraform state lives in the retired `comfy` checkout | n/a this session |
| `L-2026-07-22-5` — self-service onboarding + TLS live on P7 | **acted-on as reference** (used the onboarding/enrollment flow as M1-1 grounding) |

*Prior `--fleet` second opinion:* none pending (last retro dispatched none).

## Lessons learned
1. **`L-2026-07-23-1` — Recon before committing to a backlog pays for itself.** Three Explore agents
   found five false premises in the plans (missing session logs, keyless "signing", greenfield lab,
   gateway conflation, stale paths) that reshaped half the milestones and justified stopping at M1.
   Reading the ground truth is cheaper than executing on a wrong plan. → **practice.**
2. **`L-2026-07-23-2` — Document the truth; never fabricate substrate to pass an acceptance check.**
   Where a brief's premise is false, the deliverable becomes an honest "what exists + ranked gap list"
   (the residue skeletons stayed empty rather than inventing GM detail; the signing/replay gaps were
   documented, not stubbed). → **memory (feedback):** `document-truth-over-fake-substrate`.
3. **`L-2026-07-23-3` — This repo's automation auto-commits Gateway-touching work and force-pushes /
   rewrites `main` mid-session.** Plan around it (it lands on `main` and hits origin on its own; pure
   `docs/` changes don't trigger it); don't fight it with resets. → **memory (done):**
   `baseline-repo-auto-commits-and-pushes-main`.
4. **`L-2026-07-23-4` — Adversarial LLM verification catches real defects in offloaded prose.** A
   dedicated agent told to *attack* the drafts found four bugs (missing gate, bad placeholder, naming,
   destination) I'd have shipped. Make it the default QA pass for externally-facing docs. → **practice.**
5. **`L-2026-07-23-5` — Verify offload provenance from the result metadata, not the model's
   self-report.** The HEARTH envelope (`backend`/`model`/`ok`) is the proof the work ran where it
   claims — reinforces the CLAUDE.md offload doctrine. → **practice.**
6. **`L-2026-07-23-6` — A data file that drives a public page needs a visibility check before it's
   written.** The A-track roadmap JSON renders to the public `/roadmap`; catching that and pausing to
   ask (rather than rendering internal go-to-market framing publicly) was the right gate. → **practice.**

## Provenance
Session work is 5 of my commits (M1-1 `237eac8`/`3924ad4`, M1-2/3/4 `8c400b0`, AGENTS.md `74f7572`,
M2 `47bc78f`, A-track `cd5755b`), interleaved with ~15 background-automation commits that are not mine;
git range is non-contiguous because the automation rewrote history. Offload: `gcp-gemini-pro`
(`gemini-3.1-pro-preview`) drafted this retro's Timeline + role first-passes (`tokens_out≈1799`),
**edit_verdict: minor-fixes** — faithful, tightened two over-reaches (it proposed editing my own
baseline prompt) and added lessons 2 and 6. Six document offloads earlier in the session all ran on
`gcp-gemini-pro`, verdicts faithful/minor-fixes. Judgment sections (Two seats, Lessons, QA
self-assessment) written frontier. No `--fleet`. Adoption/process work — no netcode ADR earned (ADRs
here are scoped to the netcode-replacement program); durable decisions captured in memory + this retro
+ `DECISIONS-PENDING.md`.
