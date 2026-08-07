# Mutual-visibility confirmation — credentialed lane, r42 pair (2026-08-07)

Re-run of the two-client credentialed leg with the operator watching both
screens, because the first run's evidence was telemetry-only.

## Setup

Identical to
[the two-client receipt](../native-20260807-rung3-twoclient/two-client-credentialed-receipt.md):
AM4 re-armed `lumberjacks-primary` with the scoped redirect
(`Player,Pickable_Mushroom,Mushroom`), r42 pair everywhere, wary.fool on OMEN,
durracktu on i5 through the reverse tunnel, run id
`native-20260807-rung3-visual` synced before either join.

## Result

**Operator confirmation (Derek, watching both screens): "both in, moving and
can see each other."** Two enrolled players, co-located in region 35,-1, each
rendering and moving on the other's screen, with Player ZDOs riding the
credentialed redirect lane.

Counters at the moment of confirmation: receipts 1,161 / acknowledged 1,160 /
applied 549 / rejected 0 on window `am4-handshake-async-20260730`.

## What this does and does not prove

- **Proves:** player co-presence through the enrollment-consumer lane — two
  independently credentialed consumers each receiving and applying the other's
  Player ZDO deliveries, human-verified. The credential class AND the delivery
  class of the 08-05 outage are both closed on the rehearsal loop.
- **Bears on (but does not close) the pinned ADR 0013 item:** the 07-21 bug was
  co-located players unable to share BUILDINGS/portals (ownership/visibility
  stamp). This run confirms mutual PLAYER visibility with the fan-out flag off;
  the building-sharing case (two players, one base, structures in the redirect
  scope) still wants its own eyes-on run before the fan-out decision is judged.

## Post-run state

Both clients stopped (i5 self-closed on its bounded hold), tunnel closed, AM4
restored to native at-rest from `.bak-20260807T083649Z` and restarted.
