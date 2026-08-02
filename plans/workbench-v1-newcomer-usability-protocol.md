# Workbench v1 newcomer usability protocol

Purpose: close story WB-S2.13 with evidence from a genuinely unfamiliar person,
without substituting Derek's explanation or an agent's familiarity for product
usability. This is a product gate, not a training session.

## Test boundary

- Give the participant only the Workbench URL and this sentence: “Please use the
  page to understand what is running, perform one safe inspection, find its
  evidence, and tell me how you would recover if something went wrong.”
- Do not explain profiles, machine names, Dev MCP, receipts, or navigation before
  the attempt.
- Use Standard mode. Repeat the orientation pass once at a phone-width viewport
  or on a phone connected only through the operator's intentionally provided
  local access path.
- Do not run install, rollback, rendered movement, or factory reset during this
  usability test.
- Record no Steam ID, access key, player coordinates, or other private game data.

## Participant tasks

1. Explain, in their own words, which boxes are active and which are intentionally
   absent or waiting.
2. Find and run **Inspect system** without assistance.
3. Find the resulting job and open its events or receipt.
4. Explain the difference between safe recreate and factory reset.
5. Locate the public-safe support path they would use when asking for help.
6. Explain why **Rollback latest mod update** is unavailable when no reversible
   Workbench transaction is active, without trying to bypass it through the
   compatibility page.
7. On the narrow/mobile view, return to Home, Explore, Jobs, and Recover without
   horizontal scrolling or hidden controls.

## Pass criteria

All seven tasks complete without shell access, repository knowledge, or facilitator
instruction. One neutral clarification such as “say what you think this label
means” is allowed; navigation or domain coaching is not. Any accidental attempt
to start a player-impacting capability, inability to find the receipt, confusion
between amber and failure, or confusion between recreate and reset is a finding,
not user error.

## Observation record

Record one row per task:

| Task | Outcome (`pass`, `hesitated`, `failed`) | Time | Participant's words | Product finding |
|---|---|---:|---|---|
| System map |  |  |  |  |
| Inspect system |  |  |  |  |
| Evidence/receipt |  |  |  |  |
| Recreate vs reset |  |  |  |  |
| Public-safe support |  |  |  |  |
| Rollback availability |  |  |  |  |
| Mobile navigation |  |  |  |  |

Finish with one verdict: `passed`, `needs_copy_change`, `needs_navigation_change`,
or `unsafe_confusion`. Link the resulting private observation from the Workbench
implementation receipt; publish only a redacted conclusion.
