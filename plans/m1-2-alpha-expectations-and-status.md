# M1-2 — Alpha Expectations & Down-State Convention

## Objective
Set support expectations explicitly ("alpha, best-effort, here's how to report,
here's the rhythm") and establish a down-state convention so a dead server at
3am costs goodwill instead of trust.

## Context
One operator (Derek). Live community connecting via TLS self-service onboarding
(comfy-p7.duckdns.org). Streams frame live failures as expected alpha wobble —
put the same frame in writing.

## Steps
1. Write `docs/alpha-expectations.md`: what alpha means here, response rhythm
   (weekly sweep, see m1-3), how to report an issue (what a useful report
   contains: server time, quest name, BepInEx log location on the client), and
   what NOT to expect (SLAs, instant fixes).
2. Define the down-state convention: a pinned-message template for the
   community channel ("server down / known / ETA-or-no-ETA") and where it gets
   posted. Store the template in `docs/templates/status-down.md`.
3. Add the "how to report" two-liner to the onboarding page and link the full
   doc.
4. Optional if time allows: a static `/status` note on the community site that
   the operator can flip by hand (no automation yet — automation is a later
   milestone).

## Acceptance
- A new volunteer can answer, from the docs alone: is this normal, who do I
  tell, what do I include, when will I hear back.
- Templates are copy-paste ready (no placeholders left ungrounded except VOD
  links and dates).

## Out of scope
Automated status pages, uptime monitoring, alerting.
