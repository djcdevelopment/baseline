# Glossary

Short definitions for the post-split fleet. The owning repository and canonical path
for each implementation are in [REPO-MAP.md](../../REPO-MAP.md).

**AM4** — The local host serving the public Community Workbench and roadmap through a
Tailscale Funnel. Its production platform definitions are owned by
`lumberjacks-platform`; unrelated co-tenants can own other routes.

**Baseline** — This repository: the fleet’s durable knowledge, evidence, corpus, and
discovery hub. It preserves pre-split history but is not a writable product-code
authority.

**Comfy** — The community/product display name. The old `comfy` repository is a
historical archive; the name does not imply that current implementation belongs there.

**ComfyNetworkSense / NetworkSense** — The BepInEx telemetry, handshake, owner-score,
and HUD add-on owned by the `networksense` repository.

**Community Workbench** — The public tool catalog generated from
`lumberjacks-platform/Lumberjacks/docs/workbench/workbench.json`. It is distinct from
the loopback Companion workbench panel.

**Companion** — The loopback operator application owned by `lumberjacks-platform`.
It hosts Quest Studio through the published `Comfy.Quest.Studio` package but does not
own Quest Studio’s implementation.

**Contract package** — A small public NuGet seam used across repositories. Consumers
pin exact versions such as `[0.1.0]`; in-repository consumers may use direct project or
source links.

**Corpus mirror** — A minimal snapshot of an external public authority committed to
Baseline so Pages can rebuild offline. It names an immutable upstream commit and is
verified by byte count and SHA-256; it does not outrank the upstream authority.

**FieldLab** — The netcode-replacement research program. Its live harness and working
docs are owned by `lumberjacks-platform`; historical evidence and retrospectives remain
in Baseline.

**G1–G8** — Fleet boundary guards: no reach-in, repository identity, compose identity,
service identity, clean package-only build, artifact tamper detection, generator drift,
and corpus provenance.

**HEARTH / mechnet** — Derek’s personal local-AI/build fleet. It is operator
infrastructure and never ships in a community-facing artifact.

**I1–I5** — Cross-repository integration proofs for mod artifacts, Quest packs,
Quest pages, corpus mirrors, and the headless lab. I2 includes an intentional manual
OMEN game-client step.

**Isolate** — The repository owning the MCP gateway kernel, API/identity contracts,
container manifests, and disposable local lab runtime. Its canonical Compose host
publish is loopback port 8722 to kernel port 8720.

**Lumberjacks platform** — The .NET 9 Gateway/services/Companion stack, roadmap and
Workbench authorities, live FieldLab harness, production compose/env templates, and P7
release/deploy lane.

**Manifest-and-hash handoff** — A non-code boundary where a release records source
revision, identity, byte count, and SHA-256 for each artifact. Consumers verify the
manifest before use and prove tampering fails.

**OMEN** — Derek’s primary workstation and rendered Valheim client.

**P7** — The terminated GCP deployment `comfy-lumberjacks-p7`. Its historical evidence
remains valid; its maintained release/deploy tooling belongs to
`lumberjacks-platform`.

**PD** — Project Decision, the durable canonical home for project-level rationale
under `docs/decisions/`.

**Public source (BSL 1.1)** — The required description of the fleet’s source license.
Business Source License 1.1 is not an OSI-approved open-source license.

**Quest Lab / Runtime / Studio** — The creator sandbox, in-game consumer, and authoring
library owned by `comfy-quest`. They cross into other repositories through exact NuGet
packages, `.questpack` files, or hash-verified release assets.

**Repository identity guard** — A pre-mutation check that the current Git remote and
root markers name the expected sovereign repository. A directory name alone is not
identity.

**Sovereign repository** — A source authority that builds, tests, and releases without
reading a sibling checkout. Integration occurs only through formal packages or
hash-verified artifacts.

**Sovereign Shards** — The greenfield router/shard-manager/sidecar/bot add-on. Port
8730 is reserved; implementation claims remain unverified until code and receipts
exist.

**ZDO** — Zone Data Object, Valheim’s persistent networked world-state record.
