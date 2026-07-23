# M6-2 — Config Signing: Alpha → Federation Trust

## Objective
Harden config signing from "alpha good enough" to the trust mechanism a
federation can stand on. First deliverable is honest documentation of what the
alpha covers; second is the gap-closing work, sequenced.

## Context
Signing exists and works for the current single-operator world. It quietly
becomes the federation trust story in Projection: a node accepts a config
because it verifies against a trusted key, and nodes trust each other's
signed artifacts. Keep lab and prod mechanisms identical (M4-3 rule) — only
key material and roots differ.

## Steps
1. Threat-model the current implementation. Read the signing/verification
   code paths (config site → signing step → client mod verification). Write
   `docs/signing-threat-model.md`: what it defends against today / what it
   explicitly does not (e.g. key compromise, replay of old signed configs,
   downgrade, no revocation) / trust roots and where keys live. One page,
   honest — this alone discharges the "don't over-trust alpha" risk.
2. Rank the gaps for the federation future: likely candidates — key rotation
   procedure, config versioning/anti-replay (embed version + expiry in signed
   payload), revocation story, per-signer identity (operator key vs. future
   GM/author keys for the M5-2 pipeline), audit log of what was signed when.
3. Implement the top 1–2 gaps that are cheap and high-value now (anti-replay
   versioning is the usual first pick). Tests: old-version config rejected,
   tampered payload rejected, expired config rejected.
4. Write the rotation runbook (generate, re-sign, distribute, retire) and
   dry-run it against the lab stack.
5. Update `docs/secrets-and-sauce.md` (M4-3) — the mechanism section links the
   threat model.

## Acceptance
- Threat model reviewed against actual code, not intended design (cite
  file:line for each claim).
- Implemented gaps have failing-closed tests.
- Rotation dry-run completed in lab and documented step-by-step as executed.

## Out of scope
Multi-party key ceremony; HSM/production key storage; per-author keys build
(design it, don't build it).
