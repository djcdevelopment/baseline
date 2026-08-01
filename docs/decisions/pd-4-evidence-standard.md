# PD-4 — What counts as proof: evidence paths and falsifiable guards

Status: adopted 2026-08-01 (Derek). Canonical *why* for how work in this repo is
proven, and for which of the two standards applies when.

This document exists so that any agent, on any machine, in any environment, can be
pointed at one place — instead of reconstructing the standard from whichever comment
it happened to read first.

## The two modes

**Discovery.** The contract is not known yet; the work *is* finding the edges. The
valuable artifact is a path to evidence.

**Contract.** The shape is decided and now has to stop eroding. The valuable artifact
is a guard that fails when it erodes.

Applying the contract standard to discovery work is the common mistake, and it is
expensive: a test written against a shape you invented an hour ago mostly freezes your
current guess, and you pay for it on every correction. Applying the discovery standard
to a settled contract is the rarer mistake and costs you a silent regression.

## The rule that does not generalize

`Lumberjacks/scripts/roadmap.test.mjs` opens with:

> a guard that cannot be shown to fail is decoration

That is correct **where it lives**. The roadmap generator emits a published page with a
stable contract and an external audience — the most production-like surface in the
repo. It is not the house standard for everything, and reading it as one will slow
fieldlab work down for no gain.

The rule is also not sufficient, which is the part worth remembering. On 2026-08-01
`roadmap:check` held ~28 guards, every one demonstrably able to fail, and stayed green
while the public page asserted that the networking lane was on hard hold (it reopened
07-30) and that P7 was serving (it was terminated 07-29). The guards checked *shape*.
Nothing checked *truth*. A suite can be fully falsifiable and still be decoration in
the sense that matters.

## What an evidence path must contain

For work in flight, state four things. Prose is fine; the discipline is that none of
the four is missing.

1. **The claim** — what is asserted to work, in one sentence.
2. **What would prove it** — the named integration test, feature, or run whose passing
   closes the question, and *why that thing proves this claim*.
3. **The gate** — the explicit condition under which the claim may be upgraded, and
   the label it carries until then (`UNVERIFIED`, `built but unproven`, `candidate`).
4. **How to inspect further** — the logs, the tool sets, the ways to look. This is the
   part with the longest shelf life: it stays useful even when the claim it was
   attached to turns out to be wrong.

Item 4 is the one most often dropped, and dropping it is what turns a result into
something only its author can re-check.

## This is not new here — it is the better half of existing practice

- [`fieldlab/docs/adr/0014-boot-must-converge-or-say-so.md`](../../fieldlab/docs/adr/0014-boot-must-converge-or-say-so.md)
  marks itself reasoned-from-repo-files and **UNVERIFIED against the VM**, and names
  the exact cold stop/start that would close it. That is a complete evidence path.
- The journal record schema requires `verification` and `evidence` on every note — the
  same instinct at commit granularity.

PD-4 promotes this to the standard rather than leaving it as something two documents
happen to do well.

## Consequences

- **Reporting.** Work in flight is reported with its evidence path, not as green/red.
  A binary verdict discards how much territory a run actually covered.
- **Labels are load-bearing.** `built but unproven` is a complete, respectable status.
  Upgrading it without passing the stated gate is the failure — not the label.
- **Guards stay cheap and few in discovery.** Encode invariants you *chose* (they erode
  silently and cost little). Do not encode behavior you are still discovering.
- **A gate should hand over the inspection route.** A check that blocks without saying
  where to look is the binary failure mode in a new costume. Where a check can name the
  source of truth for the claim it is guarding, it should.

## Related

- [PD-1 — Governance & contributions](pd-1-governance-and-contributions.md) for who
  decides.
- `fieldlab/docs/adr/` for technical netcode decisions; PDs are the
  governance/product/posture track (see [README](README.md)).
