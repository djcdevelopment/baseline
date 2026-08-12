# 03 — Comfy Quest extraction report

Date: 2026-08-12

Target: `https://github.com/djcdevelopment/comfy-quest` (private)

Extraction base: `baseline@split-base-20260811`
(`aceb2eb48d770885a2c4171b926867f4ee82b4a4`)

## Result

VERIFIED — The sovereign Comfy Quest repository is extracted, scrubbed, repaired,
scaffolded, tested, and pushed. Final checkout is `C:\work\comfy-quest`; local and
`origin/main` both resolve to `2d181ea7d35014d5e97ecf2b3d5b2a5261a04460`.
The tree is clean, the remote is private, and no extraction copy remains.

VERIFIED — The filtered repository has 112 commits and 233 tracked files. Its newest
history is:

```text
2d181ea Extract Comfy Quest as a sovereign repository
6c0275e Carve Quest Studio out of Game.Companion behind IQuestStudioHost
3c3aa83 Split the fused test project along the quest seam
97e1b73 Cut the shared-contract seams: two source packages, consumers retargeted
0d36d0e Retarget cross-seam scripts behind parameters ahead of the repo split
```

## History and secret scrub

VERIFIED — Filtering started at the sealed split tag and included the Quest Lab,
Runtime, Contracts, Studio, tools, catalogs, all actual Quest tests, and only their
required fixtures. A repeated filter included the previously omitted Quest Picker
sample history.

VERIFIED — A full-history gitleaks scan found one historical fake Stripe-shaped value
in a privacy negative test. It was not a credential; history was rewritten to the
plain value `fixture-value`. The final full-history scan covered 110 commits and
returned no leaks. The commit map is retained at
`docs/provenance/commit-map.txt`.

## Corrected ownership and seams

VERIFIED — The repository carries 18 Python test modules, not the handoff’s stated 17.
Those modules contain 199 tests. Grimoire generated artifacts were also included
because the carried test contract requires them.

VERIFIED — Quest Studio moved to `src/Quest.Studio` and is self-contained for .NET 9,
with an exact interim `Comfy.Quest.Contracts` constraint `[0.1.0-local]`. It no longer
depends on Lumberjacks-wide `Directory.Build.props` or package props.

VERIFIED — The QuestLab i5 lane now lives under `tools/questlab-batch` and uses a
Quest-owned SHA-verified BatchMode deploy helper. Runtime peer acceptance writes local
captures and stages below `C:/deploy/comfy-quest`. It does not reach into Platform or
NetworkSense.

VERIFIED — The fused Workbench builder was split into Quest Lab and Quest Picker
packagers under `tools/questlab-package`; the telemetry branch is absent. The legacy
bridge sample is now a minimal fixture under `tests/fixtures/quest-bridge`.

VERIFIED — The canonical generated tome is committed at
`docs/generated/questlab.html`; the renderer and capability test both target it.
Generation followed by `--check` is the supported drift proof. `.gitattributes` was
corrected so CRLF conversion cannot falsify artifact hashes.

VERIFIED — `rg` and project inspection found zero references to
`Comfy.Transport.Contracts`; Quest does not consume the platform transport package.

## Gates

VERIFIED — Product builds:

```text
ComfyQuestLab Release build: 0 warnings, 0 errors
ComfyQuestContracts build: green
ComfyQuestRuntime build: green
Quest.Studio net9 build and pack: green
```

VERIFIED — C# suite:

```text
dotnet test network/mod/ComfyQuestLab.Tests -c Release
Passed: 185, Failed: 0, Total: 185
```

VERIFIED — Root spot-check repeated the complete carried Python suite:

```text
python -m unittest discover -s tests -v
Ran 199 tests in 7.439s
OK
```

VERIFIED — Root spot-check repeated the committed tome drift gate:

```text
python tools/component-packets/render_quest_lab.py --check
Verified C:\work\comfy-quest\docs\generated\questlab.html
```

VERIFIED — The seam/tome generators report 91 atlas rows, 90 signatures, and 34
creator events. The patch gate covers all 86 practical signatures. Quest Lab and Quest
Picker packaging both pass privacy gates and emit hash/byte receipts.

VERIFIED — Repository identity passes at the final checkout; the wrong-origin
negative fixture returns nonzero. The no-reach-in positive scan passes and an injected
forbidden sibling reference fails.

## Remaining phase dependency

BLOCKED — Public `Comfy.Quest.Contracts` and `Comfy.Quest.Studio` publication requires
a NuGet.org API key and the `NUGET_API_KEY` repository secret, neither of which is
present. Contracts must publish and become downloadable before Studio is packed with
the public exact dependency. No tag or release should be created before that proof.

INFERRED — The repository has enough local evidence to prepare the ordered publication
workflow and the `quest-v0.2.0-split-proof` artifact lane safely while retaining the
explicit interim feed. A follow-up is doing that preparation without claiming public
availability.
