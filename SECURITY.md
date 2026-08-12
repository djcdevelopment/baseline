# Security Policy

Baseline is a pre-alpha fleet hub maintained by one human (with many AI agents).
Product runtimes and deployments live in independently versioned repositories. This
policy is written for that reality — honest about what a solo maintainer can promise,
and deliberately public about known risk (see the transparency section).

## Supported versions

`main` (latest) only. There are no maintained release branches yet.

## Reporting a vulnerability

**Please do not open a public issue for a suspected vulnerability.**

- **Primary:** GitHub → the repository's **Security** tab → **Report a vulnerability**
  (private vulnerability reporting is enabled on this repository).
- **Fallback:** email `licensing@djcdevelopment.com` with a subject starting
  `[SECURITY]`.

## What to expect

- **Acknowledgment within 7 days.** The project runs on a batch rhythm — days, not
  minutes.
- **Within 90 days:** a fix, a mitigation, or a published accepted-risk disposition
  with its trigger for revisiting (see below — this project publishes those on
  purpose).
- **The ask:** please hold public disclosure for 90 days or until a fix ships,
  whichever comes first. Credit in the fix note is offered gladly if you want it.
- There is no bounty program.

## Transparency posture

This project audits itself and publishes the results, including findings it has
decided to accept for now: see [`docs/audit/`](docs/audit/) and the standing
[findings disposition](docs/audit/2026-07-29-findings-disposition.md). If you are
about to report something listed there, a report is still welcome — especially if you
believe the recorded disposition underestimates the risk.

## Scope

This repository's hub content, Pages projections, and release/mirror import tooling.
Runtime reports belong to the repository that owns the affected surface: use
[`REPO-MAP.md`](REPO-MAP.md) to route Workbench/Gateway, mod, Quest, MCP, or shard
issues. The retired pre-cutover archive repositories are out of scope (unmaintained
by design).

---

*Provenance: agent-drafted under the maintainer's recorded 2026-07-29 delegation,
operator-ratified; response promises get re-validated at the
[First Stranger gate](docs/decisions/pd-2-security-posture-first-stranger-gate.md).*
