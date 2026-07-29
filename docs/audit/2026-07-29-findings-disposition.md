# Audit findings — standing dispositions (2026-07-29)

Companion to [`2026-07-24-independent-36h-audit.md`](2026-07-24-independent-36h-audit.md):
the audit reports findings; this document records what the project **decided** about
each one, so that no finding sits decision-less. Published deliberately — accepted
risk stated in the open is part of the project's posture.

**Decision mode: delegated.** Dispositions decided and documented by the project's
agent under the operator's explicit 2026-07-29 delegation ("future facing; we're
still building"); operator rubber stamp recorded here. **Circle back at the
[First Stranger gate](../decisions/pd-2-security-posture-first-stranger-gate.md)'s
first firing** — in the operator's words, "after first alpha tester is live or when
someone asks about contributing to the repo."

| Finding | Disposition | Why | Due / trigger |
|---|---|---|---|
| **HIGH** — `terraform apply` from this repo would destroy the live VM + 4 resources | **Mitigated by standing rule** | RECONCILE-GAP is open and documented; the hard rule lives in the cost runbook, the handoff, and agent memory | Permanent fix is the deliberate Terraform reconcile effort, separately scheduled |
| **MED** — timing-unsafe key comparisons | **Fix at the next Gateway image cut** | The fix is cheap (constant-time comparison) and the next image cut is already planned (P7 cutover); today's exposure is limited — keyed surfaces answer only on loopback/tailnet vantage or are blocked at the public funnel | Next image cut; hard-due at First Stranger |
| **MED** — unauthenticated internal endpoints | **Accepted-risk while the network posture holds** | The public funnel allowlists only the public surfaces and 404s everything else; `/ops/*` is blocked at the funnel and vantage-gated at the gateway; internal endpoints are reachable only from loopback/tailnet | First Stranger, or any change that exposes new surface — whichever comes first |
| **MED** — floating base-image tags | **Accepted for dev season** | Operator-in-the-seat mode distinction (ADR 0005 amendment precedent: heavy provenance tape is for unattended agents); the deploy lane itself is digest-pinned at the compose level | Pin base images at the first release cut intended for operators other than the maintainer |
| **MED** — zero Companion test coverage | **Accepted for now; flagged as a first-task candidate** | Pure capacity call for an army of one; the seam is exercised by the operator in the seat. It is also exactly the bug-fix-shaped first task the Workbench ladder wants to hand a future Contributor | Revisit when Companion next changes, or when a Contributor wants a first task |

Related standing decisions: the security *posture* (open direct-join, password
deferral, and the full at-gate due-list) is
[PD-2](../decisions/pd-2-security-posture-first-stranger-gate.md); the private
reporting channel is [`SECURITY.md`](../../SECURITY.md).
