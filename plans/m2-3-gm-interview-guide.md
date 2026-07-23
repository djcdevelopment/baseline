# M2-3 — GM Interview Guide (governance ground truth)

## Objective
A light, reusable interview instrument for the absorbed Guild Masters that
closes the open questions in the governance doc and feeds the pattern library —
so each white-glove session doubles as research.

## Context
`C:\work\comfy\docs\governance.md` §Open questions still needs: (2) what
"farming" concretely trips on beyond the countable limits; (3) does an event
run-log exist today, how is a "run" recorded, is solo flagged, is loot
attributed; (4) does "run an event" mean complete or host. The recommended
first hub feature (Creator-Event run-log + anti-farming detector) depends on
these answers. Also collect toil inventory per `adoption-strategy.md`
(labor-first sequencing) and vocabulary mapping for the residue notes (M1-3).

## Steps
1. Write `docs/gm-interview-guide.md`: ~10 questions max, 20-minute target,
   grouped: (a) run-log reality — the four governance questions verbatim,
   translated into their vocabulary; (b) toil inventory — what do you do
   weekly that's repetitive, what would you do with the hours back; (c)
   vocabulary — their names for ranks/events/turn-ins vs. ours; (d) feel —
   one thing that would make you trust this more.
2. Create an answer-capture template `docs/templates/gm-interview.md` mirroring
   the guide, with a `confidence` field per answer (their certainty, not ours).
3. Add a closing step: route answers — governance answers get appended to a
   `## Findings` section the builder adds to a NEW file
   `docs/governance-findings.md` (do not edit the retired comfy checkout);
   toil items become candidate recipe/backlog entries; vocabulary lands in the
   residue note.

## Acceptance
- Guide fits one page; no question requires them to understand our internals.
- Both files exist; routing instructions are explicit enough for a different
  agent to file the answers correctly.

## Out of scope
Conducting the interviews (Derek does, on stream or 1:1); building the
run-log detector.
