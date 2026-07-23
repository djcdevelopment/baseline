# M5-1 — Support Runbook (symptom → tool)

## Objective
Map the top failure modes a community member reports to the diagnostic that
resolves them — mostly the comfy-gateway MCP tools that already exist — so
support is workable by a future volunteer, not just Derek.

## Context
The gateway exposes a support console already: `valheim_server_log_tail`,
`valheim_tail_bepinex_log`, `valheim_handshake_trace`/`_preflight`,
`valheim_session_bundle`, `valheim_save_integrity`, `valheim_compare_clients`,
`valheim_networksense_report`, `valheim_ownership_churn_summary`, etc. (full
list in `network/mcp/TOOLS.md`). What's missing is the human-facing map.
Expectations doc (M1-2) defines how reports arrive.

## Steps
1. Read `network/mcp/TOOLS.md` and skim the tool contracts. Build the symptom
   list from reality: recent handoffs, memory of past incidents, and the
   troubleshooting rows from `docs/lab-demo.md` if present.
2. Write `docs/support-runbook.md`, one entry per failure mode (target the top
   8): what the reporter says (their words) / what it usually is / first check
   (exact tool + args or log path) / fix or escalation / what to tell the
   player meanwhile. Cover at minimum: version mismatch, config-signature
   rejection, can't connect / joined during world reload, mod not loading,
   quest event didn't fire (client-side capture — check the PLAYER'S BepInEx
   log, the server can't see it), server down (M1-2 down-state convention),
   lag/rubber-banding (networksense report + ownership churn).
3. Each entry ends with `verified:` — ran the diagnostic against the live or
   lab server, or `unverified` if the failure can't be safely reproduced.
4. Cross-link from alpha-expectations and the demo walkthrough.

## Acceptance
- Every entry's first check is copy-paste executable (tool name + args).
- A volunteer with gateway access but zero codebase knowledge could work
  the first check of every entry.

## Out of scope
New diagnostics; automation/alerting; ticketing.
