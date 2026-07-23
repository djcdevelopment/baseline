# M1-3 — Weekly Rhythm & Templates

## Objective
Make the weekly community cycle (feedback sweep → roadmap update → changelog
post → GM touch-base) a checklist with copy-paste templates, so it survives busy
weeks and is delegable later.

## Context
The Volunteer Roadmap is live (the artifact titled "Volunteer Roadmap", id
3b391578 — NOT the retired "Netcode Program Dashboard"). Feedback currently
arrives ad hoc. Mod updates ship via Steam-bound downloads and deserve 2–3
player-facing sentences each.

## Steps
1. Write `docs/weekly-rhythm.md`: the four-step cycle, ~30 min target, with an
   explicit "you said → we did / won't / later" convention for how feedback
   items land on the roadmap.
2. Create `docs/templates/`:
   - `changelog-entry.md` — player-voice template (what changed, why you care,
     what to do if it breaks).
   - `session-residue.md` — post-consult note per GM: what was common vs.
     bespoke, vocabulary mapping (their term ↔ our term), manual steps I
     performed, toil surfaced, the ONE manual thing that should never need
     doing manually again.
   - `feedback-triage.md` — item, source, disposition (do/won't/later), roadmap
     link.
3. Seed the residue habit: backfill one residue note per already-absorbed GM
   (2 files) from memory/handoffs — mark inferred items as inferred.
4. Add a `recipes/` or `tools/` one-liner if a script can pre-collect the week's
   inputs (recent commits for changelog, open feedback items). Keep it trivial.

## Acceptance
- All three templates exist and the two backfilled residue notes use one.
- The rhythm doc names where feedback arrives and where dispositions are
  visible.

## Out of scope
Automating the sweep; feedback intake tooling.
