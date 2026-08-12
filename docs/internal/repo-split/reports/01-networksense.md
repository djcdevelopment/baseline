# 01 — NetworkSense extraction report

Date: 2026-08-12

Target: `https://github.com/djcdevelopment/networksense` (private)

Extraction base: `baseline@split-base-20260811`
(`aceb2eb48d770885a2c4171b926867f4ee82b4a4`)

## Result

VERIFIED — The sovereign NetworkSense repository is extracted, scrubbed, scaffolded,
tested, and pushed. Final checkout is `C:\work\networksense`; local and `origin/main`
both resolve to `b8a13ce28baa0de4ab24a4dc13cb68d220e52f13`. No extraction copy remains under
`C:\work\_extract`.

VERIFIED — The filtered repository has 254 commits and 173 tracked files. Its newest
history is:

```text
b8a13ce Establish the sovereign NetworkSense repository
6c9945b Split the fused test project along the quest seam
ea6621c Cut the shared-contract seams: two source packages, consumers retargeted
b0666c5 Retarget cross-seam scripts behind parameters ahead of the repo split
82eae30 Build Quest Studio to Runtime vertical
```

## History and secret scrub

VERIFIED — Filtering began from the sealed tag and used the detailed NetworkSense
include set, followed by inverted exclusions for MCP, Quest projects, and
`tools/i5/Invoke-I5QuestLabBatch.ps1`. The last included pre-scrub source commit
`70982ebc` maps to filtered commit `6c9945b`.

VERIFIED — The first full-history gitleaks scan found one credential-shaped negative
fixture named `c7-invalid-enrollment-key`. It was not a credential; history was
rewritten to the non-secret value `invalid-enrollment-fixture`. The repeated full
history scan covered 249 commits / about 2.37 MB and returned no leaks. A repeated
working-tree scan covered about 2.84 MB and returned no leaks. Filter analysis reports
the largest retained blob as 115,412 bytes.

## Ownership seam repairs

VERIFIED — The QuestLab i5 batch lane is absent. NetworkSense retains its mod/HUD,
tests, network contracts/design records, NetworkSense release tools, generic i5/am4
deployment, modpack, and synthetic extractor lanes.

VERIFIED — Post-split executable reach-ins were removed: the phase analyzer is now an
explicit SHA-pinned platform artifact input, the readiness lane is NetworkSense-local,
the dashboard URL names `lumberjacks-platform`, i5 staging is namespaced below
`C:/deploy/networksense`, and state-changing entrypoints verify repository identity.

VERIFIED — The interim feed contains the three sealed `0.1.0-local` packages required
before public NuGet publication. CI intentionally does not cloud-build the mod because
licensed Valheim/BepInEx compile inputs are not available on GitHub-hosted runners; it
does run the package-only empty-cache test and repository boundary gates.

## Gates

VERIFIED — Local release build, with plugin copying disabled:

```text
dotnet build network/mod/ComfyNetworkSense/ComfyNetworkSense.csproj -c Release -p:ComfyCopyToPlugins=false
Build succeeded. 0 Warning(s), 0 Error(s)
```

VERIFIED — Root spot-check using a newly created empty `NUGET_PACKAGES` directory:

```text
dotnet test network/mod/ComfyNetworkSense.Tests/ComfyNetworkSense.Tests.csproj -c Release
Passed! Failed: 0, Passed: 166, Skipped: 0, Total: 166
```

VERIFIED — Identity and boundary self-tests:

```text
tools/Assert-RepoIdentity.ps1
repo identity verified: djcdevelopment/networksense

tools/Test-BoundaryGuards.ps1
G1 no-reach-in verified across 137 files.
G2 identity coverage verified for 11 host entrypoints and the extractor.
G5 package-only references verified across 2 projects.
G2 negative fixture: wrong expected origin was rejected.
G1 negative fixture: forbidden source reach-in was rejected.
G5 negative fixture: sibling project reference was rejected.
boundary guard self-tests passed.
```

VERIFIED — The synthetic extractor builds without warnings/errors. Its guarded live
run reported 19 routed types, 21 direct types, 120 instance members, 122 components,
and zero unresolved types. The i5 deployment dry run resolves to
`C:/deploy/networksense` and performs no network mutation.

## Remaining phase dependency

BLOCKED — Public exact package repinning, the mod release tag, and release asset
publication require the NuGet IDs to be published and a `NUGET_API_KEY` repository
secret. No key is present yet. The repository remains on its explicit interim local
feed; a follow-up is adding publication-ready release tooling without creating a tag
or pretending that the public package/release exists.

INFERRED — Once the three public `0.1.0` packages resolve and the local/public DLL byte
gate passes, rollback changes from “return to the sealed Baseline tree” to “repin the
exact package/release version,” as required by PD-9.
