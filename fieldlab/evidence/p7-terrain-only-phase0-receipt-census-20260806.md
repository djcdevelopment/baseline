# Phase 0 receipt census — P7 terrain-only regression (2026-08-06)

Plan: debug/resolve the terrain-only regression Derek reported from the last P7
playtest. Phase 0 confirms the report is the documented 2026-08-05 outage
([SESSION-RETRO-2026-08-05](../retro/SESSION-RETRO-2026-08-05.md)) using repo
receipts and local machines only — the VM was not started.

## Findings

**Confirmed (verified this session):**

- **No playtest after 08-05.** Newest artifacts in `fieldlab/retro/` and
  `fieldlab/evidence/` are the 08-05 retro (03:37) and fix plan (03:30). Every
  commit since 08-05 is site/photography/quest work.
- **No release cut after the r41 pair.** Newest entries in
  `fieldlab/runs/releases/` are `m7-c10a-20260802-r*` (08-02). No r42 manifest
  exists; `b206c31` (the r42 source) remains uncut and undeployed.
- **No runtime netcode changes since r42 landed.**
  `git log b206c31..HEAD -- Lumberjacks/src network/mod` matches only
  `Community/*.html` renders and one 3-line quest-telemetry payload addition in
  `GameplayEventProducer.cs` (`468e9d1`, quest_name forwarding — not the
  delivery path).
- **`autoPortOnJoinEnabled = false` on both clients** — the documented
  false-diagnosis precedent (2026-07-22) is excluded for the 08-05 session.

**Deviation from expectation (plan predicted empty enrollment keys):**

Both lab clients now hold at-rest enrollment credentials, and their configs are
mutually divergent:

| Key | OMEN | i5 |
|---|---|---|
| `lumberjacksGatewayUrl` | `http://127.0.0.1:4000` | `http://100.124.12.37:4000` |
| `lumberjacksEnrollmentId` | `9a3fc0e7...` (present) | `fd31442f...` (present, different) |
| `lumberjacksClientAccessKey` | present (not recorded here) | present (not recorded here) |
| `zdoAuthoritativeConsumerEnabled` | **false** | **true** |
| `lumberjacksGameSessionEnabled` / `MotionEnabled` | true / true (left armed at rest) | true / true (left armed at rest) |

Provenance of the credentials is **unverified**. They are NOT from the AM4 lab
gateway — the `lj-workbench` container on AM4 has no enrollment store mounted
(checked: `/var/lib/lumberjacks/` holds only `roadmap/`). Most likely they were
minted against P7's enrollment store during the 08-05 recovery attempts, after
the retro was written. If so they may already be valid on P7 — verify by
checking both enrollment ids against `/mnt/comfy-p7/lumberjacks/enrollment/`
during the Phase 4 VM forensics (added to that checklist).

## Verdict

Diagnosis **confirmed**: the reported regression is the 08-05 outage; the
four-failure ladder in the retro stands. The credential deviation does not
contradict it (the failure-4 mechanism is "no *admitted* consumer", which the
session's own telemetry receipts showed as `active_consumers: 0`); it changes
the remediation starting point — the clients' at-rest state is itself live
evidence of lesson L-2026-08-05-4 (mode stored in three places, currently
divergent three ways), which the Phase 3 `verify-mode` preflight exists to
catch.

## Phase 4 forensics additions (run at next VM start, before mutating)

1. Check whether enrollment ids `9a3fc0e7...` / `fd31442f...` exist and are
   Active in P7's enrollment store; if yes, the credential half of the fix
   already exists and Phase 2 rung 3's mint step collapses to validation.
2. (unchanged) boundary events for the 08-05 window, WAL sizes,
   `.bak-20260805T1020Z` presence.
