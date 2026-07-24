# baseline

This repo merges the `comfy` repo and mods with the Lumberjacks network
implementation, per [`fieldlab/plan-baseline-cutover.md`](fieldlab/plan-baseline-cutover.md).
`comfy`'s content lives at repo root (history preserved unmodified — original
commit SHAs resolve, e.g. `git show 433f1cc3`); the Lumberjacks service tree
lives under [`Lumberjacks/`](Lumberjacks/README.md) (landed via `git subtree`,
full original history preserved as the second parent of the merge commit — see
`git log <merge-commit>^2 -- <path>` if `git log --follow` on a
`Lumberjacks/`-prefixed path stops at the merge boundary, which is expected
subtree behavior, not lost history).

## What this repo is

Four load-bearing areas:

- **Release and deployment pipeline** — [`infra/gcp/p7/`](infra/gcp/p7/README.md).
  Builds, hashes, bundles, validates, deploys and drills rollback for the GCP VM
  `comfy-lumberjacks-p7`, which runs a Valheim server plus five Lumberjacks
  services. All five are pinned by image digest out of a validated release
  bundle; none build from source on the VM.
- **The Valheim mod** — [`network/mod/ComfyNetworkSense/`](network/mod/ComfyNetworkSense/README.md).
  The live BepInEx plugin: ZDO redirect, handshake, telemetry.
- **The service stack and roadmap** — [`Lumberjacks/`](Lumberjacks/README.md).
  Gateway, eventlog, progression and operatorapi, plus the append-only
  roadmap/journal at [`Lumberjacks/docs/roadmap/`](Lumberjacks/docs/roadmap/README.md)
  driven by [`Lumberjacks/scripts/roadmap.mjs`](Lumberjacks/scripts/roadmap.mjs).
- **The experiment workspace** — [`fieldlab/`](fieldlab/NETCODE-MAP.md). Current
  netcode and ground-truth material; see
  [`fieldlab/NETCODE-MAP.md`](fieldlab/NETCODE-MAP.md) and
  [`fieldlab/VALHEIM-NETCODE-REPLACEMENT-WORKLOG.md`](fieldlab/VALHEIM-NETCODE-REPLACEMENT-WORKLOG.md).

## Roadmap tooling

The roadmap is the one status surface. Every non-merge commit appends one
journal record and stages the regenerated HTML:

```powershell
cd Lumberjacks
node scripts/roadmap.mjs note --milestone M0 --kind implementation `
  --summary "..." --impact "..."
node scripts/roadmap.mjs check            # validate + confirm generated HTML is current
node scripts/roadmap.mjs check --staged   # additionally enforce the commit contract
```

## Network research fork

`network/` also holds shareable notes on multiplayer architecture: bandwidth
budgets, priority-ranked replication, interest management, transport fallback,
and the design discipline that came from building for weaker machines and
weaker links. Start at [`network/README.md`](network/README.md) and
[`network/research-framing.md`](network/research-framing.md).

## The July 2026 prune

Roughly 280 of 1045 tracked files were deliberately removed in July 2026: the
handoff tree, community and strategy essays, a generated repo-map snapshot, a
Discord/Sheets data-harvest side project, a second Valheim mod
(`comfy-control-surface`), a camera-flythrough exploration, rank-ladder
recipes, a community-systems kit, and a large set of finished fieldlab
experiment plans, scenarios and evidence. None of it was load-bearing for the
four areas above.

That included `comfy`'s original README, which this file used to carry verbatim
below the merge preamble — a statement of the project's community mission
("enable caring to look like art instead of labor") and a session-by-session
history of how the repo grew. It was removed because nearly every path it
pointed at is gone and the repo's live purpose is now the four areas above, not
community tooling. It is worth reading; it is just no longer an accurate index
of this repo.

All pruned content remains recoverable from this repo's git history and from the
two still-existing source repos, `C:\work\comfy` and `C:\work\lumberjacks`. If
you are looking for something a doc used to reference and cannot find it here,
that is where it went.

## License

Current versions are distributed under the [Business Source License
1.1](LICENSE), with a community-use grant for noncommercial deployments of up
to 100 active members that publish their complete deployed source. Commercial
production use requires a separate written license. Each version converts to
AGPL-3.0-only no later than the Change Date in `LICENSE`.

Earlier versions remain available under the license terms that accompanied
them. See [LICENSING.md](LICENSING.md) for the scope and plain-language
summary, [NOTICE.md](NOTICE.md) for affiliation and trademark notices, and
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for exclusions.
