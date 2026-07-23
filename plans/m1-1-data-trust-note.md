# M1-1 — Data & Trust Note

## Objective
Publish a plain-language page stating exactly what the quest mod and telemetry
capture, where it goes, who can see it, and how to opt out. This ships **before**
the next volunteer is absorbed — discovered capture poisons trust retroactively;
announced capture is the pitch.

## Context
- Capture is client-side (in-game events, weapon type) from the quest vertical
  slice; the community API serves **aggregates only** (versioned v0 API in the
  omen-dashboard stack).
- Integrations are performed live on stream — cite the VODs as standing proof
  that everything is wired in the open.
- Voice rules: `C:\work\comfy\docs\positioning.md`. Never surveillance framing;
  owner-controlled and opt-in per `adoption-strategy.md`.

## Steps
1. Inventory actual captured fields: read the quest-slice capture code under
   `network/mod/` and the aggregates API surface in the dashboard stack. List
   every field name. Do not paraphrase — enumerate.
2. Draft the note (target ≤ 1 page) with sections: What is captured / What is
   never captured / Where it lives / Who can see what (player vs GM vs operator)
   / How to opt out / Watch it being built (VOD links placeholder).
3. Write to `docs/data-and-trust.md` AND surface it on the community site
   (`/community`) — check the live-page source in the dashboard stack for where
   static pages mount.
4. Add a one-line link to the self-service onboarding page so every new
   installer sees it.

## Acceptance
- Every field in the note matches a field actually present in capture code
  (grep-verifiable; note the source file per field in an HTML comment).
- No framing that reads as a verdict or as monitoring of players.
- Linked from onboarding; renders on /community.

## Out of scope
Consent tooling / opt-out mechanics beyond documenting the existing switch.
