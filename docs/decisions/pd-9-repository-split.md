# PD-9 — Sovereign add-on repositories with Baseline as the hub

- Status: Accepted
- Owner: Derek
- Date: 2026-08-12
- Extraction base: `baseline@split-base-20260811` (`aceb2eb48d770885a2c4171b926867f4ee82b4a4`)

## Decision

Baseline becomes the durable knowledge, evidence, and discovery hub. Active product
implementation is divided into sovereign repositories:

- `networksense` owns the telemetry mod, HUD, tests, and mod release lanes;
- `lumberjacks-platform` owns the .NET 9 services, Companion, live FieldLab harness,
  roadmap ceremony, Workbench catalog, production compose/env templates, and P7 lane;
- `comfy-quest` owns Quest Lab, Runtime, Contracts, Studio, generators, and creator
  artifacts;
- `sovereign-shards` is the greenfield router/shard/sidecar/bot add-on; and
- `isolate` owns the MCP kernel, container manifests, and disposable lab runtime.

Baseline keeps the browsable pre-split history, decisions, historical evidence,
corpus mirrors/projections, and [the fleet map](../../REPO-MAP.md). Its current tree is
not a shadow implementation repository.

## Why

The merged tree made knowledge discoverable, but it also let unrelated products share
filesystem paths, build props, generators, local package fallbacks, release scripts,
compose identities, and commit ceremony. Those implicit seams made a successful local
build a poor proof that a component was independently usable. A sovereign add-on must
be buildable, testable, publishable, and removable without a sibling checkout.

The split retains Baseline’s valuable role: one durable place to understand the whole
system and inspect evidence. Ordinary deletions preserve its history, while filtered
repositories retain component history from the sealed extraction tag.

## Rejected alternatives

1. **Keep the monorepo.** Rejected because file reach-ins and shared build state hide
   the true package/release contracts.
2. **Copy code into several repositories.** Rejected because multiple writable
   authorities drift. A mirror is permitted only for public corpus inputs and must be
   pinned and hash-verified.
3. **One repository per shared type.** Rejected as excessive ceremony. Three small
   cross-repository .NET seams are published packages; larger integrations remain
   release artifacts.
4. **Make Baseline a meta-build checkout.** Rejected because it would recreate sibling
   reach-ins. Fleet verification orchestrates released artifacts and independent CI,
   not source trees.

## Contract boundaries

- `Comfy.Quest.Contracts`, `Comfy.Transport.Contracts`, and `Comfy.Quest.Studio` are
  public NuGet packages. Consumers use exact constraints; producers publish in
  dependency order.
- NetworkSense publishes its DLL with source revision, release identity, build-input
  hashes, byte count, and SHA-256 digest. Platform deployment consumes that manifest;
  it does not rebuild or inspect NetworkSense source.
- Comfy Quest publishes Quest Lab/Picker pages and zips with the same manifest-and-hash
  discipline. Platform vendors those assets by release tag plus pinned manifest hash.
- Baseline mirrors Workbench and roadmap corpus records from an immutable
  `lumberjacks-platform` commit. G8 rejects a missing, mutable, or tampered mirror.
- Production compose and environment templates belong to `lumberjacks-platform`.
  The generic MCP/lab compose runtime belongs to `isolate`; compose project names must
  be distinct.

## Governance placement

The append-only roadmap journal and its pre-commit hook move with
`lumberjacks-platform`, the implementation program they describe. Baseline records
program-level decisions and evidence but has no per-implementation-commit journal
ceremony. Each product repository owns its identity, no-reach-in, build, test, and
release guards.

## Rollback

Before public package pins, rollback could return to the sealed Baseline extraction
tag. Once consumers resolve public exact packages, rollback means repinning a package
or release artifact. Product code is not copied back into Baseline.
