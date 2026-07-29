# PD-1 — Governance & contributions

Status: adopted 2026-07-29 (Derek). Canonical *why* for the contribution posture.
The *what* lives in [`CONTRIBUTING.md`](../../CONTRIBUTING.md) and
[`LICENSING.md`](../../LICENSING.md); this document explains it and records the open slot.

## The operating principle

> **Baseline sells licenses, so the maintainer must hold rights to the whole tree.**

Baseline is public source (BSL 1.1) with a paid commercial path
([`COMMERCIAL.md`](../../COMMERCIAL.md)), and ComfyStewardView is proprietary. A licensor
who grants Additional Use Grants and sells commercial licenses must hold sufficient
rights over every line shipped. Rights are cheap to collect at the door and famously
expensive to collect retroactively. Every contribution rule below follows from this
one sentence.

## Decisions recorded

- **The repo is public** (flipped 2026-07-29). Reading was never meant to be the gate.
- **PRs are open to anyone; the maintainer is the sole approval gate**, on a batch
  rhythm — responses in days, not minutes (2026-07-29).
- **Ladder stage 3 is "Contributor"** (renamed from Steward, which is overloaded on the
  server) and grants commit access to that piece. The license-suite "Community Steward"
  grant and the ComfyStewardView product name are unaffected.
- **Interim rights bridge, until the formal instrument ships:** the
  [`CONTRIBUTING.md`](../../CONTRIBUTING.md) contributor representations (original work,
  permission sufficient to use *and relicense*, AI-generated material disclosed), plus
  "contact `licensing@djcdevelopment.com` before substantial work." Substantive
  third-party code is not merged until the contributor agreement is completed
  (`LICENSING.md` §Contributions).

## The open slot: CLA vs DCO

The formal instrument is **not yet picked** — tracked in the root
[`DECISIONS-PENDING.md`](../../DECISIONS-PENDING.md). Due **before the first substantial
external PR** (equivalently: PD-2's First Stranger gate, for code).

Standing recommendation on file: a lightweight click-through CLA (trivial/docs-only PRs
exempt), because a DCO certifies provenance but transfers nothing — it cannot satisfy
the operating principle above. The call is the maintainer's; when made, the resolution
is recorded here and the register entry collapses to a one-liner.

## Revisit triggers

- **Instrument decision due:** first substantial external PR / First Stranger (code).
- **Downgrade CLA→DCO** becomes reasonable only if the commercial posture is ever
  dropped (change date passes with no successor licensing, or paid licensing ends) —
  at that point rights aggregation stops earning its friction.
