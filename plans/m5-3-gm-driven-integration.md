# M5-3 — GM-Driven Integration Playbook

## Objective
The training half of white-glove graduates: a playbook for a trained GM to
drive segments of the NEXT GM's integration on stream, with Derek as safety
net. Converts "Derek's tool" into "our thing" and makes session N measurably
shorter than session 1.

## Context
Two GMs are absorbed and were trained live during their own integrations.
Session-residue notes (M1-3) record what's common vs. bespoke — the common
parts are the GM-drivable parts. The white-glove metric: each session should
shed at least one manual step into tooling/config.

## Steps
1. From the residue notes (or by reconstructing the integration steps from
   the onboarding flow if residue notes don't exist yet), split the
   integration into segments and classify each: GM-drivable / operator-only
   (secrets, server access) / bespoke-per-guild.
2. Write `docs/gm-driven-integration.md`: the segment map; a driver guide per
   GM-drivable segment (what to do, what success looks like, when to hand
   back); the safety-net protocol (operator watches, intervenes on
   operator-only steps, never mid-segment unless asked); and the on-stream
   framing (the GM is the expert of their guild's content — the vocabulary
   from the interviews (M2-3) is theirs, use it).
3. Add the measurement: a per-integration log line in the residue template —
   total time, segments GM-driven, manual steps performed, the one step
   promoted to tooling. Trend visible across sessions.
4. Prep the ask: a short invitation blurb for the trained GMs (voice rules
   from positioning.md — invitation and recognition, never obligation).

## Acceptance
- Segment map covers the full current onboarding flow; every segment
  classified with a reason.
- A trained GM reading only the driver guide could run their segments.
- The measurement fields exist in the residue template.

## Out of scope
Actually scheduling/running the session; incentives/rewards for GM drivers.
