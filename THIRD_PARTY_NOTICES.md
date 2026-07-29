# Third-party material and license boundaries

The root project license applies only to material DJC Development is
authorized to license. Dependencies and externally sourced material retain
their own copyright and license terms.

This file is an inventory aid, not a substitute for the license notices
shipped by each dependency.

## Referenced but not redistributed

`network/mod/ComfyNetworkSense/ComfyNetworkSense.csproj` references locally
installed assemblies from Valheim, Unity, BepInEx, and Harmony. Those
assemblies are not part of this repository and are not licensed by this
project. Users must obtain and use them under their applicable terms.

NuGet, npm, container, operating-system, and other declared dependencies are
governed by their own licenses. Lockfiles and version declarations do not
relicense those dependencies.

## Files requiring their own terms or provenance review

- `infra/gcp/p7/scripts/lib/System.Collections.Immutable.dll`
- `infra/gcp/p7/scripts/lib/System.Reflection.Metadata.dll`

  These binaries identify Microsoft Corporation as their publisher. They are
  not covered by the project license. Confirm and ship the matching Microsoft
  package license and notices with every redistributed bundle.

- `Lumberjacks/tools/ideas/9923-2823P-MTDC_ An Ax to Grind_ A Practical Ax Manual.html`
- `Lumberjacks/tools/ideas/9923-2823P-MTDC_ An Ax to Grind_ A Practical Ax Manual_files/`

  These are a saved United States Forest Service publication and associated
  web assets. They are excluded from the project license. Preserve source and
  government attribution and confirm the status of every included asset
  before redistribution.

- `recipes/quest-submission-bridge/`

  Byte-exact copies recovered 2026-07-29 from the project's public comfy
  archive (`github.com/djcdevelopment/comfy`, commit `ae81c83`), which is
  MIT-licensed. The copies retain their MIT terms — full license text and the
  file-by-file mapping are in `recipes/quest-submission-bridge/PROVENANCE.md`.
  The authored additions in that directory (`PROVENANCE.md`, `.gitattributes`)
  are project material under the root license.

- `recipes/camera-gallery/`

  Byte-exact copies recovered 2026-07-29 from the project's public comfy
  archive (`github.com/djcdevelopment/comfy`, commit `ae81c83`), which is
  MIT-licensed. The copies retain their MIT terms — full license text and the
  file-by-file mapping are in `recipes/camera-gallery/PROVENANCE.md`. The
  authored additions in that directory (`PROVENANCE.md`, `.gitattributes`)
  are project material under the root license.

- `Lumberjacks/oldimages/`

  These image files have OpenArt-style source names but no repository license
  or complete provenance record. They are excluded from the project license
  and should not be included in a release until their ownership, generation
  history, and permitted uses are documented.

## Decompiled and compatibility-derived material

`fieldlab/` and related implementation notes contain compatibility research
derived in part from observation and decompilation of locally installed game
assemblies. The repository does not include those decompiled assemblies or
claim ownership of third-party code. Before commercial distribution or
licensing, obtain legal review of the relevant platform terms, applicable
exceptions, and each excerpt or mirrored element.

## Adding third-party material

Before committing a third-party file:

1. record its source URL, author or publisher, exact version, and retrieval
   date;
2. retain its license and required notices;
3. confirm that redistribution and the intended production use are allowed;
4. keep it outside the project license scope; and
5. add it to this inventory when it is shipped or copied into the repository.
