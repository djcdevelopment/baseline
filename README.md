# Baseline

Baseline is the hub of knowledge, evidence, and discovery for the Comfy Valheim
toolkit. The active products are independent add-ons with their own builds, releases,
and boundaries; this repository answers where they live, why the boundaries exist,
and what evidence supports the project’s claims.

## Start here

- [Repository map](REPO-MAP.md) — implementation owner, canonical path, artifact
  contract, and guard for every surface.
- [Era and status map](docs/internal/START-HERE.md) — what is live, historical,
  stopped, or awaiting an operator proof.
- [Evidence standard](docs/decisions/pd-4-evidence-standard.md) — the difference
  between verified, inferred, blocked, and aspirational claims.
- [Repository split decision](docs/decisions/pd-9-repository-split.md) — why Baseline
  became the hub and how code crosses repository boundaries.
- [Port registry](docs/PORTS.md) — one runtime claim per local port.

## The add-on fleet

| Repository | Owns |
|---|---|
| [`networksense`](https://github.com/djcdevelopment/networksense) | ComfyNetworkSense mod, HUD, telemetry tests, and mod release artifacts |
| [`lumberjacks-platform`](https://github.com/djcdevelopment/lumberjacks-platform) | Gateway/services/Companion, live FieldLab harness, roadmap, Workbench, production compose, and P7 lanes |
| [`comfy-quest`](https://github.com/djcdevelopment/comfy-quest) | Quest Lab, Runtime, Contracts, Studio, generators, and creator release artifacts |
| [`sovereign-shards`](https://github.com/djcdevelopment/sovereign-shards) | Greenfield router, shard manager, sidecar, and bot architecture |
| [`isolate`](https://github.com/djcdevelopment/isolate) | MCP kernel, API contracts, container manifests, and disposable lab runtime |

Cross-repository code uses exact public packages. DLLs, generated pages, zips, and
corpus inputs cross only with an immutable revision or release tag plus verified byte
counts and SHA-256 hashes. No repository reads a sibling checkout.

## What remains here

- durable project decisions and architecture/history documentation under `docs/`;
- historical FieldLab evidence, retrospectives, and receipts under `fieldlab/`;
- public discovery inputs, mirrors, deterministic projections, and Pages under
  `corpus/`, `data/`, and `site/`;
- operator handoffs and archived plans; and
- small hub-owned tools for corpus, site, dispatch, provenance, and evidence work.

Baseline’s Git history remains the browsable pre-split archive. Product trees were
removed with ordinary commits; their component histories continue from the sealed
`split-base-20260811` tag.

## Public surfaces

The public Community Workbench and roadmap are served at
[am4.tail8e749c.ts.net](https://am4.tail8e749c.ts.net/workbench). Baseline’s
reconstructable discovery projections are published through GitHub Pages. Runtime and
deployment authority belongs to the owning product repository; a page mirrored here
does not become a second source of truth.

## Contributing and security

Read [AGENTS.md](AGENTS.md) before changing this hub and
[CONTRIBUTING.md](CONTRIBUTING.md) before proposing work. Report suspected
vulnerabilities through [the private security process](SECURITY.md), not a public
issue.

## License

Public source is provided under the [Business Source License 1.1](LICENSE), with the
Community Steward grant and automatic conversion described there. Plain-language
scope is in [the licensing guide](docs/legal/LICENSING.md).

*Not affiliated with or endorsed by Iron Gate AB or Coffee Stain Publishing.*
