# PD-1 — Governance & contributions

Status: adopted 2026-07-29 (Derek). Canonical *why* for the contribution posture.
The *what* lives in [`CONTRIBUTING.md`](../../CONTRIBUTING.md), [`CLA.md`](../legal/CLA.md),
and [`LICENSING.md`](../legal/LICENSING.md); this document explains it.

## The operating principle

> **Baseline sells licenses, so the maintainer must hold rights to the whole tree.**

Baseline is public source (BSL 1.1) with a paid commercial path
([`COMMERCIAL.md`](../legal/COMMERCIAL.md)), and ComfyStewardView is proprietary. A licensor
who grants Additional Use Grants and sells commercial licenses must hold sufficient
rights over every line shipped. Rights are cheap to collect at the door and famously
expensive to collect retroactively. Every contribution rule below follows from this
one sentence.

## Decisions recorded

- **The repo is public** (flipped 2026-07-29). Reading was never meant to be the gate.
- **ComfyStewardView remains proprietary** (affirmed by the operator 2026-07-30);
  its Workbench contribution path is documentation and feedback, not code contribution.
- **PRs are open to anyone; the maintainer is the sole approval gate**, on a batch
  rhythm — responses in days, not minutes (2026-07-29).
- **Ladder stage 3 is "Contributor"** (renamed from Steward, which is overloaded on the
  server) and grants commit access to that piece. The license-suite "Community Steward"
  grant and the ComfyStewardView product name are unaffected.
- **Contributor representations** ([`CONTRIBUTING.md`](../../CONTRIBUTING.md)) —
  original work, permission sufficient to use *and relicense*, AI-generated material
  disclosed — predate the CLA and remain in force alongside it. Substantive
  third-party code is not merged until the contributor agreement is completed
  (`LICENSING.md` §Contributions).

## The instrument: lightweight CLA (decided 2026-07-29, delegated)

**Decision:** a plain-language contributor license agreement — [`CLA.md`](../legal/CLA.md)
v1.0 — signed with one sentence in the first substantive PR (or by email), recorded in
[`docs/legal/cla-signatures.md`](../legal/cla-signatures.md) at merge. Trivial changes
waivable at the maintainer's discretion.

Why, against the delegation criteria:

- **The license demands it.** BSL 1.1 plus the commercial path require rights
  aggregation; a DCO certifies provenance and transfers nothing.
- **Capacity.** An army of one human needs no CLA bot and no external service — one
  sentence and a ledger file is the entire machinery.
- **Near-term goals.** Friction is near zero for the cohort that exists (name-known
  friends), and the ladder's fixed-one-thing rung stays frictionless via the
  trivial-change waiver.

## AI-assisted contributions (decided 2026-07-29, delegated)

This project is built by **one human directing many AI agents** — the public audit
says so and the commit history shows it, so the bar is symmetric and
disclosure-based, not prohibitive:

- AI-assisted work is welcome; appreciable AI generation must be disclosed (already a
  CONTRIBUTING representation).
- **You sign it, you own it:** the human contributor must understand and stand behind
  every line; the CLA certifications bind the human regardless of tooling.
- Contributions are judged on **verification, not provenance** — tests, repro steps,
  receipts. A PR its author cannot answer questions about gets declined.
- The maintainer may request provenance detail (which parts were generated) when it
  matters for licensing confidence.

## Decision mode and circle-back

The two sections above were decided and documented by the project's agent under the
operator's explicit 2026-07-29 delegation ("future facing; we're still building");
the operator's rubber stamp is recorded here rather than implied. **Circle back at
the First Stranger gate's first firing** — in the operator's words, "after first
alpha tester is live or when someone asks about contributing to the repo" — including
a real legal review of the CLA text if contribution volume warrants it.

## Revisit triggers

- **First Stranger gate, first firing:** review every delegated decision above
  (instrument, AI bar), counsel pass on the CLA text if warranted.
- **Downgrade CLA→DCO** becomes reasonable only if the commercial posture is ever
  dropped (change date passes with no successor licensing, or paid licensing ends) —
  at that point rights aggregation stops earning its friction.
