# M6-2 — Config Signing: Alpha → Federation Trust

Status: the current documentation task may proceed, but cryptographic signing is
deferred until an external signer, peer node, or other real trust boundary exists.
That trigger requires an ADR covering trust roots, rotation, revocation, and
anti-replay before implementation.

## Objective
Harden config signing from "alpha good enough" to the trust mechanism a
federation can stand on. First deliverable is honest documentation of what the
alpha covers; second is the gap-closing work, sequenced.

## Context
The original plan overstated the substrate: the current mechanism is a keyless
SHA-256 integrity checksum, not cryptographic signing. It can detect accidental
or post-build change when compared with a trusted expected hash; it does not
establish signer identity or federation trust.

Future lab and production signing should share one mechanism, with only key
material and trust roots differing, but that architecture is not selected until
the trigger above exists.

## Steps
1. Threat-model the current integrity implementation. Read the checksum and
   verification
   code paths (config site → signing step → client mod verification). Write
   `docs/signing-threat-model.md`: what it defends against today / what it
   explicitly does not (e.g. key compromise, replay of old signed configs,
   downgrade, no revocation) / trust roots and where keys live. One page,
   honest — this alone discharges the "don't over-trust alpha" risk.
2. At the external-trust trigger, write the ADR and rank the gaps for the
   federation future: likely candidates — key rotation
   procedure, config versioning/anti-replay (embed version + expiry in signed
   payload), revocation story, per-signer identity (operator key vs. future
   GM/author keys for the M5-2 pipeline), audit log of what was signed when.
3. After that ADR is accepted, implement the top 1–2 selected gaps. Tests:
   old-version config rejected,
   tampered payload rejected, expired config rejected.
4. Write the rotation runbook (generate, re-sign, distribute, retire) and
   dry-run it against the lab stack.
5. Update `docs/secrets-and-sauce.md` (M4-3) — the mechanism section links the
   threat model.

## Acceptance
- Threat model reviewed against actual code, not intended design (cite
  file:line for each claim).
- No current checksum is described as signer authentication.
- After the external-trust trigger, implemented gaps have failing-closed tests
  and the rotation dry-run is documented step-by-step as executed.

## Out of scope
Multi-party key ceremony; HSM/production key storage; per-author keys build
(design it, don't build it).
