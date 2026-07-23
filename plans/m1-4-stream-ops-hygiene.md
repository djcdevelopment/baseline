# M1-4 — Stream Ops Hygiene

## Objective
A pre-stream checklist plus small hardening so that white-glove-on-stream can
never leak what can't be unleaked: keys, tokens, gateway URLs with secrets,
player identifiers in logs.

## Context
Integrations, training, and demos happen live on screen. Anything shown is
published. The gateway uses an `X-Hearth-Key` style header pattern; BepInEx and
server logs can contain player names / Steam IDs.

## Steps
1. Sweep the repo for what a screen-share could expose: grep for env files,
   `*.key`, tokens in compose/config examples, and note which log files include
   player identifiers (check `network/mod/ComfyNetworkSense` log output and
   gateway logs under `network/mcp/var`).
2. Write `docs/stream-ops-hygiene.md`:
   - pre-stream checklist (dedicated terminal profile with clean env, no
     secrets in shell history, editor workspace without `.env`/`infra` open,
     OBS scene that crops or excludes sensitive panes);
   - a "player-data on screen" rule: which log tails are safe to show raw vs.
     need the redacted view;
   - incident step if a leak happens anyway (rotate first, apologize second —
     list which keys rotate where).
3. If quick wins exist, take them: e.g. add a `--redact` flag or env toggle to
   the noisiest log-tail path that masks player names/IDs. Only if it's < 1 hr;
   otherwise file it as a TODO in the doc.

## Acceptance
- Checklist is short enough to actually run (≤ 10 items).
- Every named rotation target includes where the key lives and the rotate
  command/procedure.

## Out of scope
Full secrets-management overhaul; vault tooling.
