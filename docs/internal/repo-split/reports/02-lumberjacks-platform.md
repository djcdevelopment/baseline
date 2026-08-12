# 02 — Lumberjacks Platform extraction report

Date: 2026-08-12

Target: `https://github.com/djcdevelopment/lumberjacks-platform` (private)

Extraction base: `baseline@split-base-20260811`
(`aceb2eb48d770885a2c4171b926867f4ee82b4a4`)

## Result

VERIFIED — The sovereign platform repository is extracted, scrubbed, repaired,
scaffolded, tested, and pushed. Its final checkout is
`C:\work\lumberjacks-platform`; local `main` and `origin/main` both resolve to
`a122776f7ceb9a04acbc31ef3bb7e94ae192efbe`. The tree and `git fsck` are clean,
and no extraction copy remains under `C:\work\_extract`.

VERIFIED — The sealed source tag maps to filtered commit
`93a2513ca424be24eb3e500cf1f12df5abd26d97`. The final history includes 676
commits. Its newest relevant commits are:

```text
a122776 Fix guest config splitting across PowerShell editions
c03b3fe Scrub managed guest keys from repeated sections
5b808a0 Restore live FieldLab authority inputs
3fa815a Make hosted platform checks checkout- and shell-correct
d82ec55 Repair hosted extraction gates
7bc1ad8 Establish the sovereign Lumberjacks platform repository
```

## History and secret scrub

VERIFIED — Filtering kept Lumberjacks (excluding old images, nested MCP, and Quest
Studio), P7, the live FieldLab harness and ADR working set, platform tools/tests, and
the roadmap ceremony. The filter reported no retained blob above 5 MiB; the final
pack is about 7.77 MiB. The committed 1,161-line provenance map has SHA-256
`280CA6CC2A7D89A4E30B4DBFF400F50B10D320D49E785E8EE8D86DEA713D0710`.

VERIFIED — Five initial gitleaks findings were fixture or detector false positives
and were scrubbed through the filtered history. Gitleaks 8.30.1 then scanned all 676
commits / about 11.70 MiB with no leaks.

## Corrected ownership and seams

VERIFIED — Platform owns the .NET 9 services, Gateway and Companion, Transport
contracts, production Compose/P7, Workbench and append-only roadmap, live FieldLab
scripts/docs/scenarios/routes/autonomous harness, and Companion i5 lane. It contains
no NetworkSense source, Quest Studio source, MCP kernel, old images, or Baseline
historical run/evidence archive.

VERIFIED — The corrected manifest adds 24 non-run experiment inputs: 23
creative-runtime inputs and one patchload configuration. No run output was copied.
Twenty-three files plus the patchload config are byte-identical to the sealed tag;
the CRE-E06 runner differs only by its platform identity guard and passes 13/13
adapter checks. The active retro skill was made platform-local. Fifteen unchecked
legacy decision rows were evaluated against the queue policy; four viable platform
choices remain, and the stale “isolate has no remote” claim was removed.

VERIFIED — Companion consumes the exact interim Quest Contracts, Quest Studio, and
Transport packages at `0.1.0-local`; it does not reach into a sibling checkout. The
i5 scripts use a self-contained, SHA-verified BatchMode deploy helper. Runtime
identity is baked into the release images and asserted by the native FieldLab
preflight.

## Gates

VERIFIED — .NET 9 solution build and tests are green, 649/649:

```text
Comfy.Transport.Contracts: 126
Game.Gateway:              247
Game.Companion:             26
Game.Simulation:           250
Total:                     649
```

VERIFIED — The Docker verify build repeats all 649 tests in a clean container; the
standalone Companion image also builds. Gateway and Companion runtime `/identity`
checks return the expected repository and revision.

VERIFIED — Roadmap has 46/46 tests plus a clean render check. Workbench validates all
eight tools. Authority Lab is 7/7. Python is eight passed plus two expected sealed-
artifact skips. A dedicated PowerShell 5/7 regression proves repeated BepInEx
sections remove five managed keys while preserving four user values.

VERIFIED — G1 no-reach-in, G2 coverage of 28 state-changing entrypoints and its
negative, G3 eight unique Compose project names, G4 service identity, and G6 wrong-
SHA rejection all pass. All PowerShell files parse and FieldLab/Compose
configurations validate.

VERIFIED — The final hosted matrix is green in all five jobs (roadmap-workbench,
guards, Python, .NET, and containers):
`https://github.com/djcdevelopment/lumberjacks-platform/actions/runs/31582448902`.

VERIFIED — The final ownership-transfer roadmap receipts are
`20260812084138-transferred-lumberjacks-platform-ownership-to-it` and
`20260812090802-restored-live-fieldlab-authority-inputs`; the platform hook accepted
both ceremonies.

## Remaining phase dependency

BLOCKED — No package, tag, release, or deployment was created. Public
`Comfy.Transport.Contracts` 0.1.0 publication and coordinated public repinning require
the NuGet ID and repository `NUGET_API_KEY`, neither of which is currently available.
The explicit interim feed remains the honest pre-publication boundary.

INFERRED — After all three public packages resolve, the safe rollback commitment
changes from the local interim feed to repinning an exact public version. Until then,
the repository must not claim that commitment point has been crossed.
