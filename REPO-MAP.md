# Comfy repository map

Baseline is the place to ask “where does this live?” It keeps durable decisions,
evidence, public corpus projections, and the map below. Product implementation is
owned by a sovereign repository and crosses a boundary only as a pinned package or a
hash-verified release artifact.

| Surface | Owning repository | Canonical path | Boundary artifact | Owning guard |
|---|---|---|---|---|
| Fleet index, decisions, evidence archive | [`baseline`](https://github.com/djcdevelopment/baseline) | `docs/`, `fieldlab/evidence/`, `corpus/` | immutable links and provenance receipts | entrypoint links + corpus G8 |
| NetworkSense mod and HUD | [`networksense`](https://github.com/djcdevelopment/networksense) | `network/mod/ComfyNetworkSense/` | `mod-v*` DLL, release manifest, SHA-256 sums | repo identity + G1/G5 release gates |
| NetworkSense unit tests | `networksense` | `network/mod/ComfyNetworkSense.Tests/` | CI receipt | exact test-count gate |
| Quest contracts | [`comfy-quest`](https://github.com/djcdevelopment/comfy-quest) | `network/mod/ComfyQuestContracts/` | `Comfy.Quest.Contracts` exact NuGet version | package payload + clean-restore gate |
| Quest Lab and Runtime | `comfy-quest` | `network/mod/ComfyQuestLab/`, `network/mod/ComfyQuestRuntime/` | `quest-v*` DLL/zips and manifest | G1/G7 + exact test-count gates |
| Quest Studio | `comfy-quest` | `src/Quest.Studio/` | `Comfy.Quest.Studio` exact NuGet version and `.questpack` files | package dependency + round-trip gates |
| World snapshot analytics and spatial map authoring | [`ComfyStewardView`](https://github.com/djcdevelopment/ComfyStewardView) | `viewer/` | content-addressed spatial anchor/evidence JSON | shared hash fixtures + Steward contract tests |
| Quest Lab tome and picker | `comfy-quest` | `docs/generated/questlab.html`, `tools/questlab-package/` | release assets with manifest/SHA-256 sums | render drift + release verifier |
| Gateway, services, Companion | [`lumberjacks-platform`](https://github.com/djcdevelopment/lumberjacks-platform) | `Lumberjacks/src/` | versioned container images and HTTP identity contracts | solution tests + G3/G4 |
| Transport contracts | `lumberjacks-platform` | `Lumberjacks/src/Comfy.Transport.Contracts/` | `Comfy.Transport.Contracts` exact NuGet version | package payload + clean-restore gate |
| Roadmap journal and Workbench catalog | `lumberjacks-platform` | `Lumberjacks/docs/roadmap/`, `Lumberjacks/docs/workbench/` | generated HTML and hash-addressed downloads | platform pre-commit/render gates |
| Live FieldLab harness | `lumberjacks-platform` | `fieldlab/`, `tools/authority-lab/` | release manifests and run receipts | artifact-first harness gates |
| Historical FieldLab evidence | `baseline` | `fieldlab/evidence/`, `fieldlab/retro/`, `fieldlab/runs/` | immutable evidence receipts | PD-4 evidence labeling |
| P7 release/deploy/rollback lane | `lumberjacks-platform` | `infra/gcp/p7/` | signed/hash-recorded release manifests | pure artifact verifier before deploy |
| MCP gateway kernel and lab containers | [`isolate`](https://github.com/djcdevelopment/isolate) | `network/mcp/`, `docker/` | container image + `/identity` and API contracts | 24-test MCP suite + compose boundary |
| Shard/router greenfield architecture | [`sovereign-shards`](https://github.com/djcdevelopment/sovereign-shards) | `router/`, `shard-manager/`, `sidecar/`, `bot/` | future versioned contracts; port 8730 reserved | identity + port-claim lint |
| Public discovery corpus | `baseline` | `corpus/`, `site/` | pinned mirrors from immutable upstream SHAs | provenance, byte, and SHA-256 validation |

## Integration rules

- Cross-repository .NET code uses exact NuGet constraints such as `[0.1.0]`.
- A mod DLL, generated page, zip, or corpus source crosses by immutable revision or
  release tag plus a manifest, byte count, and SHA-256 digest.
- A script never reads a sibling checkout. Paths derive from the repository root or
  from an explicit operator-supplied artifact.
- Deployment tools verify repository identity before mutation. A loopback port or
  successful health response is not identity; use the owning service’s `/identity`
  contract.
- Baseline does not regain implementation as a convenience copy. It records where the
  authority moved and mirrors only the minimum public data needed for reconstruction.

See [PD-9](docs/decisions/pd-9-repository-split.md) for the durable rationale and
[the port registry](docs/PORTS.md) for runtime claims.
