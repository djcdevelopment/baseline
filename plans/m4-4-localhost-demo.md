# M4-4 — The Localhost Demo Walkthrough

## Objective
The white-glove demo, scripted: `compose up` → join the local server with your
own Valheim client → watch YOUR kill land on YOUR localhost dashboard. Nothing
demystifies "what does this capture and where does it go" faster than seeing
your own data land on a machine you control. The client-side limitation IS the
feature — say so in the walkthrough.

## Context
Prereqs: M4-2 stack, M4-3 lab keys. Capture is client-side, so the demo
requires the mod installed in the tester's Valheim (the self-service
personalized zip flow exists — reuse or adapt it to point at localhost).
Remember the world-reload delay: the server isn't joinable until the
"Game server connected" log line.

## Steps
1. Write `docs/lab-demo.md` as a follow-along (audience: an alpha tester or
   server mod, NOT a developer): prerequisites, compose up, how to know it's
   ready, how to install the lab-configured mod zip, connect to
   `127.0.0.1:2456`, kill something, open the dashboard, find your event.
   Include a troubleshooting table (top 5: Docker not running, port taken,
   joined too early, mod not loaded — where the BepInEx log is, signature
   rejected).
2. Adapt the mod-zip generation for lab mode: server address localhost, config
   signed with the lab key (from M4-3 state volume). Smallest change that
   works; document it in the walkthrough.
3. Dry-run the whole doc yourself on the local machine, fixing every step that
   doesn't match reality. The dry-run IS the review.
4. Add a final section "what you just saw": map each demo moment to the piece
   that did it (mod captured → gateway received → telemetry stored →
   dashboard aggregated) with links to deeper docs/workbooks.

## Acceptance
- A dry-run from clean state succeeds following ONLY the written steps.
- Time-to-first-event from `compose up` is measured and stated in the doc.
- Every troubleshooting row names the exact log/file to check.

## Out of scope
Multi-tester scenarios; streaming/recording the demo; Mac/Linux client paths
(note them as untested).
