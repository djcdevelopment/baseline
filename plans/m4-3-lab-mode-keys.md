# M4-3 — Lab Mode Keys & the Secrets/Sauce Boundary

## Objective
Lab mode: all keys the stack needs are generated on first run; and a one-page
boundary doc that makes the open-source posture explicit — architecture,
equations, configs, and the signing MECHANISM all ship (sauce); only live keys
and tokens stay behind (secrets), and they rotate.

## Context
Config signing is alpha-grade and is the long-run federation trust story (M6-2)
— keep the mechanism identical between lab and prod; only the key material
differs. Secret inventory comes from M4-1. No credentials ever land in the
repo or on the P7 box pattern — same rule here.

## Steps
1. From the M4-1 secret list, classify each: generate-on-first-run (signing
   keypair, gateway API key), harmless-default (ports, names), or
   genuinely-absent-in-lab (external tokens — the stack must degrade
   gracefully without them; verify it does).
2. Implement first-run generation: an init container or entrypoint script in
   `infra/lab/` that creates missing keys into a git-ignored
   `infra/lab/state/` volume and prints what it generated. Idempotent.
3. Verify signing works lab-to-lab: sign a config with the generated key,
   client-side verification path accepts it, and a tampered config is
   rejected. Script it — this is a runnable proof.
4. Write `docs/secrets-and-sauce.md`: the boundary table (item / ships or
   stays / why / rotation procedure for the stays-behind items), plus the
   explicit statement that lab mode is cryptographically real but trusts a
   different root.

## Acceptance
- `compose up` on a clean machine needs zero secrets provided by hand.
- Tamper test fails closed.
- Boundary doc lists every secret from the inventory — none unclassified.

## Out of scope
Hardening signing to production grade (M6-2); key ceremony for prod.
